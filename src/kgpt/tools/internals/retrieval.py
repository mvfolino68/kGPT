"""Retrieval agent with hybrid search and reranking.

This module implements a modern RAG retrieval pipeline with:
- Query enhancement for domain-specific disambiguation
- Hybrid search (dense + keyword scoring)
- Reranking (delegated to rerank.py)
- Result deduplication
"""

import asyncio

from langchain_core.documents import Document
from loguru import logger

from kgpt.cache import get_query_cache
from kgpt.tools.internals.rerank import create_rerank_query, rerank_documents
from kgpt.tools.query_enhancer import enhance_query_for_web_search
from kgpt.vectorstore import get_vectorstore


async def _enhance_retrieval_queries(queries: list[str]) -> list[str]:
    """
    Enhance retrieval queries with domain-specific disambiguation using LLM.

    Args:
        queries: List of raw queries from user/router

    Returns:
        List of enhanced queries optimized for Kafka document retrieval
    """
    tasks = []
    for query in queries:
        # Use the same enhancement logic as web search
        # This ensures "kraft" -> "KRaft" disambiguation
        tasks.append(
            enhance_query_for_web_search(
                query,
                add_domain_suffix=False,  # Don't add suffix for vector search
            )
        )

    if not tasks:
        return []

    return await asyncio.gather(*tasks)


async def search_documents(query: str, sub_queries: list[str] | None = None) -> list[Document]:
    """
    Search the knowledge base using hybrid search and reranking.

    Args:
        query: Main search query
        sub_queries: Optional list of related queries to broaden search

    Returns:
        List of relevant documents
    """
    logger.info(f"Searching knowledge base for: {query[:50]}...")

    # Check cache first
    cache = get_query_cache()
    # Cache key includes sub-queries to be correct
    cache_key = f"retrieval:{query}:{str(sub_queries)}"
    cached = cache.get(cache_key)
    if cached:
        logger.info("Using cached retrieval results")
        return cached

    store = get_vectorstore()
    all_docs: list[Document] = []
    seen_content_hashes: set[int] = set()

    raw_queries = [query] + (sub_queries or [])

    # Enhance queries for domain-specific disambiguation
    queries = await _enhance_retrieval_queries(raw_queries)

    if queries != raw_queries:
        logger.debug(f"Enhanced queries: {raw_queries} -> {queries}")

    try:
        # Search across all collections
        collections = store.list_collections()

        for q in queries:
            logger.debug(f"Searching: {q[:50]}...")

            for collection in collections:
                try:
                    # Hybrid search (combines dense + keyword scoring)
                    results = store.hybrid_search(
                        q,
                        k=5,
                        collection_name=collection,
                        alpha=0.7,  # Favor dense vectors slightly
                    )

                    for doc, score in results:
                        # Deduplicate by content hash
                        content_hash = hash(doc.page_content[:500])
                        if content_hash not in seen_content_hashes:
                            seen_content_hashes.add(content_hash)
                            doc.metadata["relevance_score"] = float(score)
                            doc.metadata["collection"] = collection
                            doc.metadata["search_query"] = q[:100]
                            all_docs.append(doc)

                except Exception as e:
                    logger.warning(f"Error searching collection {collection}: {e}")
                    continue

        # Preliminary sort by relevance score
        all_docs.sort(key=lambda d: d.metadata.get("relevance_score", 0), reverse=True)

        # Log initial retrieval scores for debugging
        if all_docs:
            initial_scores = [f"{d.metadata.get('relevance_score', 0):.3f}" for d in all_docs[:5]]
            logger.debug(f"Initial retrieval scores (top 5): [{', '.join(initial_scores)}]")

        # Take top candidates for reranking
        candidates = all_docs[:20]

        # Reranking
        if candidates:
            # Create optimized rerank query with Kafka context
            enhanced_query = queries[0] if queries else query
            rerank_query = create_rerank_query(query, enhanced_query)
            logger.debug(f"Rerank query: {rerank_query}")

            reranked_docs = await rerank_documents(
                query=rerank_query,
                documents=candidates,
                top_k=10,
            )
        else:
            reranked_docs = []

        logger.info(
            f"Retrieved {len(all_docs)} candidates, kept {len(reranked_docs)} after reranking"
        )

        # Cache results
        cache.set(cache_key, reranked_docs)

        return reranked_docs

    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        # Return empty list on error for resilience
        return []
