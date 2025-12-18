"""Retrieval agent with hybrid search and reranking.

This module implements a modern RAG retrieval pipeline with:
- Query enhancement for domain-specific disambiguation
- Hybrid search (dense + keyword scoring)
- Reranking with Cohere or cross-encoder models
- Minimum relevance filtering to remove irrelevant results
- Multi-collection search
- Result deduplication and filtering
"""

from langchain_core.documents import Document
from loguru import logger

from kgpt.agents.query_enhancer import enhance_query_for_web_search
from kgpt.agents.state import AgentState
from kgpt.cache import get_query_cache
from kgpt.vectorstore import get_vectorstore

# Minimum rerank score threshold - documents below this are filtered out
# Cohere rerank scores: 0.0 = irrelevant, 1.0 = highly relevant
# Using 0.01 as a very low threshold - primary filtering is via top_k ranking
# The reranker's main job is ordering, not filtering
MIN_RERANK_SCORE_COHERE = 0.01

# Minimum number of documents to keep even if below threshold
# This ensures we always have some context for synthesis
MIN_DOCS_TO_KEEP = 3

# Cross-encoder scores are different (can be negative)
# Keep docs with score > 0 (positive relevance signal)
MIN_RERANK_SCORE_CROSS_ENCODER = 0.0


async def rerank_documents(
    query: str,
    documents: list[Document],
    top_k: int = 10,
    min_score_threshold: float | None = None,
) -> list[Document]:
    """
    Rerank documents using Cohere's reranker or a cross-encoder fallback.

    Reranking significantly improves retrieval quality by using a more
    sophisticated model to score query-document relevance. Documents below
    the minimum relevance threshold are filtered out.

    Args:
        query: The original user query
        documents: List of candidate documents
        top_k: Number of documents to return after reranking
        min_score_threshold: Optional override for minimum score filtering

    Returns:
        Reranked list of documents (best first), filtered by relevance
    """
    if not documents:
        return []

    # Try Cohere reranking first (best quality)
    try:
        from kgpt.db import get_db

        db = get_db()
        cohere_key = db.get_setting("cohere_api_key")

        if cohere_key:
            import cohere

            co = cohere.Client(cohere_key)

            # Prepare documents for reranking
            doc_texts = [doc.page_content for doc in documents]

            # Rerank using Cohere
            rerank_response = co.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=doc_texts,
                top_n=min(top_k * 2, len(documents)),  # Get more for filtering
                return_documents=False,
            )

            # Apply minimum score threshold
            threshold = (
                min_score_threshold if min_score_threshold is not None else MIN_RERANK_SCORE_COHERE
            )

            # Reorder and filter documents based on reranking
            reranked_docs = []
            all_scored_docs = []
            filtered_count = 0
            scores_preview = []

            for result in rerank_response.results:
                doc = documents[result.index]
                score = float(result.relevance_score)
                doc.metadata["rerank_score"] = score
                doc.metadata["reranking_model"] = "cohere-rerank-v3"
                scores_preview.append(f"{score:.3f}")
                all_scored_docs.append((doc, score))

                # Filter by threshold
                if score >= threshold:
                    reranked_docs.append(doc)
                else:
                    filtered_count += 1

            # Ensure we keep at least MIN_DOCS_TO_KEEP even if below threshold
            # This prevents returning empty results when scores are low
            if len(reranked_docs) < MIN_DOCS_TO_KEEP and len(all_scored_docs) > len(reranked_docs):
                # Add more docs from the scored list (they're already sorted by score)
                for doc, score in all_scored_docs:
                    if doc not in reranked_docs:
                        reranked_docs.append(doc)
                        if len(reranked_docs) >= MIN_DOCS_TO_KEEP:
                            break

            # Limit to top_k after filtering
            reranked_docs = reranked_docs[:top_k]

            logger.info(
                f"Reranked docs using Cohere. "
                f"Scores: [{', '.join(scores_preview[:5])}], "
                f"kept {len(reranked_docs)}, filtered {filtered_count} below {threshold:.2f}"
            )
            return reranked_docs

    except ImportError:
        logger.debug("Cohere not installed, using fallback reranking")
    except Exception as e:
        logger.warning(f"Cohere reranking failed: {e}, using fallback")

    # Fallback: Use cross-encoder reranking with sentence-transformers
    try:
        from sentence_transformers import CrossEncoder

        # Use a lightweight cross-encoder model
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)

        # Score each document
        pairs = [[query, doc.page_content[:1000]] for doc in documents]
        scores = model.predict(pairs)

        # Apply minimum score threshold
        threshold = (
            min_score_threshold
            if min_score_threshold is not None
            else MIN_RERANK_SCORE_CROSS_ENCODER
        )

        # Sort by cross-encoder score and filter
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        reranked_docs = []
        filtered_count = 0
        for doc, score in scored_docs:
            doc.metadata["rerank_score"] = float(score)
            doc.metadata["reranking_model"] = "ms-marco-MiniLM"
            if score >= threshold:
                reranked_docs.append(doc)
                if len(reranked_docs) >= top_k:
                    break
            else:
                filtered_count += 1

        logger.info(
            f"Reranked {len(reranked_docs)} docs using cross-encoder, "
            f"filtered {filtered_count} below {threshold:.1f}"
        )
        return reranked_docs

    except ImportError:
        logger.debug("sentence-transformers not installed, skipping reranking")
    except Exception as e:
        logger.warning(f"Cross-encoder reranking failed: {e}")

    # Final fallback: Return documents sorted by original similarity score
    logger.info("Using similarity scores for ranking (no reranking model available)")
    sorted_docs = sorted(
        documents,
        key=lambda d: d.metadata.get("relevance_score", 0),
        reverse=True,
    )
    return sorted_docs[:top_k]


def _enhance_retrieval_queries(queries: list[str]) -> list[str]:
    """
    Enhance retrieval queries with domain-specific disambiguation.

    This ensures that ambiguous terms like "kraft" are properly understood
    as "KRaft" (Kafka Raft consensus) rather than unrelated concepts.

    Args:
        queries: List of raw queries from user/router

    Returns:
        List of enhanced queries optimized for Kafka document retrieval
    """
    enhanced = []
    for query in queries:
        # Use the same enhancement logic as web search
        # This ensures "kraft" -> "KRaft" disambiguation
        enhanced_query = enhance_query_for_web_search(
            query,
            add_domain_suffix=False,  # Don't add suffix for vector search
        )
        enhanced.append(enhanced_query)

    return enhanced


def _create_rerank_query(original_query: str, enhanced_query: str) -> str:
    """
    Create an optimized query for Cohere reranking.

    Cohere reranker needs domain context to score Kafka documents correctly.
    For example, "what is kraft" scores 0.001 but "What is KRaft in Apache Kafka?"
    scores 1.0 for the same Kafka documentation.

    Args:
        original_query: The user's original question
        enhanced_query: The domain-enhanced query (kraft -> KRaft)

    Returns:
        Query optimized for Cohere reranking with Kafka context
    """
    # If query already has Kafka context, use the enhanced version as-is
    query_lower = enhanced_query.lower()
    if "kafka" in query_lower or "confluent" in query_lower:
        return enhanced_query

    # Add Kafka context for reranking (critical for Cohere to score correctly)
    # This is different from vector search - rerankers need explicit context
    return f"{enhanced_query} in Apache Kafka"


async def retrieval_node(state: AgentState) -> dict:
    """
    Retrieval node with hybrid search and reranking.

    Pipeline:
    1. Enhance queries with domain-specific disambiguation
    2. Hybrid search - combine dense vector and keyword matching
    3. Deduplication - remove duplicate chunks from different queries
    4. Reranking - use Cohere or cross-encoder to improve precision
    5. Relevance filtering - remove documents below threshold
    6. Caching - cache results for repeated queries
    """
    logger.info("Retrieval agent fetching documents...")

    # Check cache first
    cache = get_query_cache()
    cache_key = f"retrieval:{state['question']}"
    cached = cache.get(cache_key)
    if cached:
        logger.info("Using cached retrieval results")
        return {"retrieved_docs": cached}

    store = get_vectorstore()
    all_docs: list[Document] = []
    seen_content_hashes: set[int] = set()

    # Use sub_goals from router + main question
    sub_goals = state.get("sub_goals", [])
    raw_queries = [state["question"]] + [g for g in sub_goals if g != state["question"]]

    # Enhance queries for domain-specific disambiguation
    # This transforms "kraft" -> "KRaft" to find correct Kafka documentation
    queries = _enhance_retrieval_queries(raw_queries)

    if queries != raw_queries:
        logger.debug(f"Enhanced queries: {raw_queries} -> {queries}")

    try:
        # Search across all collections
        collections = store.list_collections()

        for query in queries:
            logger.debug(f"Searching: {query[:50]}...")

            for collection in collections:
                try:
                    # Hybrid search (combines dense + keyword scoring)
                    results = store.hybrid_search(
                        query,
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
                            doc.metadata["search_query"] = query[:100]
                            all_docs.append(doc)

                except Exception as e:
                    logger.warning(f"Error searching collection {collection}: {e}")
                    continue

        # Preliminary sort by relevance score (higher = better)
        all_docs.sort(key=lambda d: d.metadata.get("relevance_score", 0), reverse=True)

        # Log initial retrieval scores for debugging
        if all_docs:
            initial_scores = [f"{d.metadata.get('relevance_score', 0):.3f}" for d in all_docs[:5]]
            logger.debug(f"Initial retrieval scores (top 5): [{', '.join(initial_scores)}]")

        # Take top candidates for reranking (more than we need)
        candidates = all_docs[:20]

        # Reranking for better precision (includes relevance filtering)
        if candidates:
            # Create optimized rerank query with Kafka context
            # Cohere needs domain context to score Kafka docs correctly
            enhanced_query = queries[0] if queries else state["question"]
            rerank_query = _create_rerank_query(state["question"], enhanced_query)
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

        return {"retrieved_docs": reranked_docs}

    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return {
            "retrieved_docs": [],
            "error": f"Retrieval failed: {str(e)}",
        }


def extract_doc_citations(docs: list[Document]) -> list[dict]:
    """Extract citation information from retrieved documents with content previews and metadata."""
    citations = []
    seen_urls = set()

    for doc in docs:
        source = doc.metadata.get("source", "")
        source_name = doc.metadata.get("source_name", "")

        # Derive source_name from URL if not set
        if not source_name and source:
            from urllib.parse import urlparse

            parsed = urlparse(source)
            # Use domain + path for a more descriptive name
            if parsed.netloc:
                source_name = parsed.netloc
                # Add path hint for context
                if parsed.path and parsed.path != "/":
                    path_hint = parsed.path.strip("/").split("/")[-1][:30]
                    if path_hint:
                        source_name = f"{source_name} - {path_hint}"
            else:
                source_name = "Documentation"
        elif not source_name:
            source_name = "Documentation"

        if source and source not in seen_urls:
            seen_urls.add(source)
            # Include content preview for display
            content_preview = doc.page_content[:500] if doc.page_content else ""

            # Extract relevance/rerank scores - prefer rerank_score if available and non-zero
            # If rerank_score is 0, fall back to similarity score for display purposes
            rerank = doc.metadata.get("rerank_score")
            similarity = doc.metadata.get("relevance_score")
            if rerank is not None and rerank > 0:
                relevance_score = rerank
            else:
                relevance_score = similarity

            citation = {
                "title": source_name,
                "url": source if source.startswith("http") else "",
                "type": "doc",
                "content_preview": content_preview,
            }

            # Add relevance score if available
            if relevance_score is not None:
                citation["relevance_score"] = float(relevance_score)

            # Add metadata for educational display
            metadata = {}
            if doc.metadata.get("collection"):
                metadata["collection"] = doc.metadata["collection"]
            # Use "relevance_score" which is what hybrid_search sets (not "similarity_score")
            if doc.metadata.get("relevance_score") is not None:
                metadata["similarity_score"] = float(doc.metadata["relevance_score"])
            # Use is not None to handle 0 as a valid score
            if doc.metadata.get("rerank_score") is not None:
                metadata["rerank_score"] = float(doc.metadata["rerank_score"])

            if metadata:
                citation["metadata"] = metadata

            citations.append(citation)

    return citations
