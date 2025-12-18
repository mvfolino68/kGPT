"""Advanced retrieval agent with query expansion, hybrid search, and reranking.

This module implements a modern RAG retrieval pipeline with:
- Query expansion for better recall
- Hybrid search (dense + keyword scoring)
- Reranking with Cohere or cross-encoder models
- Multi-collection search
- Result deduplication and filtering
"""

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from kgpt.agents.state import AgentState
from kgpt.cache import get_query_cache
from kgpt.llm import get_llm
from kgpt.vectorstore import get_vectorstore

QUERY_EXPANSION_PROMPT = """You are a search query expansion assistant.
Given a user question, generate 2-3 alternative search queries that might help find relevant documentation.

User question: {question}

Generate alternative queries, one per line. Be specific and use different phrasings.
Output only the queries, nothing else."""


async def expand_queries(question: str) -> list[str]:
    """
    Expand a question into multiple search queries for better recall.
    
    Uses an LLM to generate semantically related queries that might
    match different phrasings in the document corpus.
    """
    try:
        llm = get_llm(streaming=False)
        prompt = ChatPromptTemplate.from_template(QUERY_EXPANSION_PROMPT)
        chain = prompt | llm

        result = await chain.ainvoke({"question": question})
        queries = [q.strip() for q in result.content.strip().split("\n") if q.strip()]

        # Always include the original question first
        return [question] + queries[:2]

    except Exception as e:
        logger.warning(f"Query expansion failed: {e}")
        return [question]


async def rerank_documents(
    query: str,
    documents: list[Document],
    top_k: int = 10,
) -> list[Document]:
    """
    Rerank documents using Cohere's reranker or a cross-encoder fallback.
    
    Reranking significantly improves retrieval quality by using a more
    sophisticated model to score query-document relevance.
    
    Args:
        query: The original user query
        documents: List of candidate documents
        top_k: Number of documents to return after reranking
        
    Returns:
        Reranked list of documents (best first)
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
                top_n=min(top_k, len(documents)),
                return_documents=False,
            )
            
            # Reorder documents based on reranking
            reranked_docs = []
            for result in rerank_response.results:
                doc = documents[result.index]
                doc.metadata["rerank_score"] = float(result.relevance_score)
                doc.metadata["reranking_model"] = "cohere-rerank-v3"
                reranked_docs.append(doc)
            
            logger.info(f"Reranked {len(reranked_docs)} documents using Cohere")
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
        
        # Sort by cross-encoder score
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        reranked_docs = []
        for doc, score in scored_docs[:top_k]:
            doc.metadata["rerank_score"] = float(score)
            doc.metadata["reranking_model"] = "ms-marco-MiniLM"
            reranked_docs.append(doc)
        
        logger.info(f"Reranked {len(reranked_docs)} documents using cross-encoder")
        return reranked_docs
        
    except ImportError:
        logger.debug("sentence-transformers not installed, skipping reranking")
    except Exception as e:
        logger.warning(f"Cross-encoder reranking failed: {e}")
    
    # Final fallback: Return documents sorted by original similarity score
    logger.info("Using similarity scores for ranking (no reranking model available)")
    sorted_docs = sorted(
        documents,
        key=lambda d: d.metadata.get("relevance_score", 999),
    )
    return sorted_docs[:top_k]


async def retrieval_node(state: AgentState) -> dict:
    """
    Advanced retrieval node with hybrid search and reranking.

    Pipeline:
    1. Query expansion - generate alternative queries for better recall
    2. Hybrid search - combine dense vector and keyword matching
    3. Deduplication - remove duplicate chunks from different queries
    4. Reranking - use a cross-encoder to improve precision
    5. Caching - cache results for repeated queries
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
    seen_content_hashes: set[str] = set()

    # Get sub-goals or use the main question
    queries = state.get("sub_goals", [state["question"]])

    try:
        for query in queries:
            # Step 1: Query expansion for better recall
            expanded = await expand_queries(query)
            logger.debug(f"Expanded query into {len(expanded)} variations")

            for search_query in expanded:
                logger.debug(f"Searching: {search_query[:50]}...")

                # Search across all collections
                collections = store.list_collections()

                for collection in collections:
                    try:
                        # Step 2: Hybrid search (combines dense + keyword scoring)
                        results = store.hybrid_search(
                            search_query,
                            k=5,
                            collection_name=collection,
                            alpha=0.7,  # Favor dense vectors slightly
                        )

                        for doc, score in results:
                            # Step 3: Deduplicate by content hash
                            content_hash = hash(doc.page_content[:500])
                            if content_hash not in seen_content_hashes:
                                seen_content_hashes.add(content_hash)
                                doc.metadata["relevance_score"] = float(score)
                                doc.metadata["collection"] = collection
                                doc.metadata["search_query"] = search_query[:100]
                                all_docs.append(doc)

                    except Exception as e:
                        logger.warning(f"Error searching collection {collection}: {e}")
                        continue

        # Preliminary sort by relevance score
        all_docs.sort(key=lambda d: d.metadata.get("relevance_score", 0), reverse=True)
        
        # Take top candidates for reranking (more than we need)
        candidates = all_docs[:20]

        # Step 4: Reranking for better precision
        if candidates:
            reranked_docs = await rerank_documents(
                query=state["question"],
                documents=candidates,
                top_k=10,
            )
        else:
            reranked_docs = []

        logger.info(f"Retrieved and reranked {len(reranked_docs)} documents")

        # Cache results
        cache.set(cache_key, reranked_docs)

        return {"retrieved_docs": reranked_docs}

    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return {
            "retrieved_docs": [],
            "error": f"Retrieval failed: {str(e)}",
        }
