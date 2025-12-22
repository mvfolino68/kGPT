"""RAG pipeline information and demo endpoints for educational purposes."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class RAGPipelineInfo(BaseModel):
    """Information about the RAG pipeline for educational purposes."""

    pipeline_stages: list[dict]
    retrieval_config: dict
    embedding_config: dict
    reranking_available: bool
    hybrid_search_enabled: bool


# ============================================================================
# RAG Pipeline Endpoints
# ============================================================================


@router.get("/info", response_model=RAGPipelineInfo)
async def get_rag_pipeline_info() -> RAGPipelineInfo:
    """
    Get information about the RAG pipeline configuration.

    This endpoint explains how the retrieval-augmented generation system works,
    including all the stages from query to answer.
    """
    from kgpt.db import get_db
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    # Check if reranking is available
    reranking_available = False
    reranking_method = None
    try:
        import cohere

        cohere_key = db.get_setting("cohere_api_key")
        if cohere_key:
            reranking_available = True
            reranking_method = "Cohere rerank-v3"
    except ImportError:
        pass

    if not reranking_available:
        try:
            from sentence_transformers import CrossEncoder

            reranking_available = True
            reranking_method = "ms-marco MiniLM cross-encoder"
        except ImportError:
            pass

    # Check if hybrid search is enabled
    hybrid_enabled = True  # Qdrant supports hybrid search by default

    # Get embedding config
    embedding_model = db.get_setting("embedding_model") or "text-embedding-3-small"
    embedding_provider = db.get_setting("embedding_provider") or "openai"

    # Determine embedding dimensions
    embedding_dims = 1536  # default

    if embedding_provider == "openai":
        if "text-embedding-3-large" in embedding_model:
            embedding_dims = 3072
        elif "text-embedding-3-small" in embedding_model or "ada-002" in embedding_model:
            embedding_dims = 1536
    elif embedding_provider == "fastembed":
        if "bge-small-en-v1.5" in embedding_model or "BAAI/bge-small-en-v1.5" in embedding_model:
            embedding_dims = 384
        elif "bge-base-en-v1.5" in embedding_model or "BAAI/bge-base-en-v1.5" in embedding_model:
            embedding_dims = 768
        elif (
            "bge-large-en-v1.5" in embedding_model
            or "BAAI/bge-large-en-v1.5" in embedding_model
            or "multilingual-e5-large" in embedding_model
        ):
            embedding_dims = 1024

    # Build pipeline stages dynamically
    stages = []

    # Stage 1: Query Expansion
    stages.append(
        {
            "name": "Query Expansion",
            "description": "Generate alternative phrasings of the user's question to improve recall",
            "example": "Original: 'How do I configure Kafka?' → Generates 2-3 alternative phrasings",
        }
    )

    # Stage 2: Embedding Generation
    stages.append(
        {
            "name": "Embedding Generation",
            "description": f"Convert the query into a dense vector using {embedding_provider} {embedding_model}",
            "example": f"Text → [{embedding_dims}-dimensional vector]",
        }
    )

    # Stage 3: Vector Search
    collections = store.list_collections()
    stages.append(
        {
            "name": "Vector Search",
            "description": f"Search {len(collections)} collection(s) using cosine similarity",
            "example": f"Query vector compared against document vectors in: {', '.join(collections[:3])}{'...' if len(collections) > 3 else ''}",
        }
    )

    # Stage 4: Hybrid Scoring
    if hybrid_enabled:
        stages.append(
            {
                "name": "Hybrid Scoring",
                "description": "Combine dense vector similarity with keyword matching (BM25-style)",
                "example": "RRF fusion: 0.7 × dense_score + 0.3 × keyword_score",
            }
        )

    # Stage 5: Reranking
    if reranking_available:
        stages.append(
            {
                "name": "Reranking",
                "description": f"Re-score and reorder results using {reranking_method}",
                "example": "Cross-encoder model scores query-document pairs for better precision",
            }
        )

    # Stage 6: Deduplication
    stages.append(
        {
            "name": "Deduplication",
            "description": "Remove duplicate content from multiple query expansions",
            "example": "Hash-based deduplication ensures unique results",
        }
    )

    # Stage 7: Context Assembly
    stages.append(
        {
            "name": "Context Assembly",
            "description": "Combine top-ranked chunks into a context window for the LLM",
            "example": "Top 10 chunks assembled as context",
        }
    )

    # Stage 8: Answer Generation
    llm_provider = db.get_setting("llm_provider") or "openai"
    llm_model = db.get_setting("llm_model") or "gpt-4o-mini"
    stages.append(
        {
            "name": "Answer Generation",
            "description": f"LLM ({llm_provider} {llm_model}) generates an answer from the retrieved context",
            "example": "Synthesizes answer with citations from validated sources",
        }
    )

    return RAGPipelineInfo(
        pipeline_stages=stages,
        retrieval_config={
            "top_k_initial": 20,
            "top_k_final": 10,
            "hybrid_alpha": 0.7,
            "query_expansion_count": 3,
        },
        embedding_config={
            "model": embedding_model,
            "provider": embedding_provider,
            "dimensions": embedding_dims,
        },
        reranking_available=reranking_available,
        hybrid_search_enabled=hybrid_enabled,
    )


@router.get("/demo")
async def rag_demo(query: str = Query(..., description="Demo query")) -> dict:
    """
    Demonstrate the full RAG pipeline step by step.

    This endpoint shows what happens at each stage of retrieval,
    making it educational for understanding how RAG works.
    """
    from kgpt.tools.query_enhancer import enhance_query_for_web_search
    from kgpt.vectorstore import get_vectorstore

    store = get_vectorstore()

    steps = []

    # Step 1: Query expansion
    try:
        # Renamed to "Query Enhancement" to match the new tool behavior
        enhanced = await enhance_query_for_web_search(query)
        # Wrap in list to maintain compatibility with existing frontend expectations
        expanded = [enhanced]
        steps.append(
            {
                "step": 1,
                "name": "Query Enhancement",
                "input": query,
                "output": expanded,
                "description": "Enhanced query with domain context to improve search relevance",
            }
        )
    except Exception as e:
        expanded = [query]
        steps.append(
            {
                "step": 1,
                "name": "Query Enhancement",
                "input": query,
                "output": [query],
                "error": str(e),
            }
        )

    # Step 2: Generate embedding
    try:
        embedding = store.get_embedding_for_text(query)
        steps.append(
            {
                "step": 2,
                "name": "Embedding Generation",
                "input": query[:100],
                "output": {
                    "dimensions": len(embedding),
                    "preview": embedding[:5],
                    "model": "text-embedding-3-small",
                },
                "description": "Converted query text to a dense vector representation",
            }
        )
    except Exception as e:
        steps.append(
            {
                "step": 2,
                "name": "Embedding Generation",
                "error": str(e),
            }
        )
        embedding = []

    # Step 3: Vector search
    try:
        results = store.search_chunks(query, k=5)
        steps.append(
            {
                "step": 3,
                "name": "Vector Search",
                "input": f"Query vector ({len(embedding)} dims)",
                "output": {
                    "chunks_found": len(results),
                    "top_results": [
                        {
                            "preview": r["content_preview"][:150],
                            "similarity": r["similarity_percent"],
                            "source": r["source_name"],
                        }
                        for r in results[:3]
                    ],
                },
                "description": "Found most similar document chunks using cosine similarity",
            }
        )
    except Exception as e:
        steps.append(
            {
                "step": 3,
                "name": "Vector Search",
                "error": str(e),
            }
        )
        results = []

    # Step 4: Summary
    steps.append(
        {
            "step": 4,
            "name": "Context Assembly",
            "description": f"Would assemble top {len(results)} chunks as context for LLM",
            "total_context_length": sum(len(r.get("content", "")) for r in results),
        }
    )

    return {
        "query": query,
        "pipeline_steps": steps,
        "total_steps": len(steps),
    }
