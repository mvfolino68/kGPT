"""Documents API routes for managing document sources, ingestion, and vector operations.

This module provides a comprehensive API for:
- Document source management (CRUD)
- Document ingestion with progress tracking
- Vector search and browsing
- Collection management and analytics
- RAG pipeline inspection (educational)
"""

import asyncio
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from kgpt.api.schemas import (
    DocumentsListResponse,
    DocumentSource,
    IngestRequest,
    IngestResponse,
    SourceType,
)
from kgpt.db import get_db

router = APIRouter(prefix="/documents", tags=["documents"])

# Track ongoing ingestion jobs with detailed progress
_ingestion_jobs: dict[int, dict] = {}
# Track cancelled jobs
_cancelled_jobs: set[int] = set()


# ============================================================================
# Additional Schemas for Vector Operations
# ============================================================================


class VectorSearchRequest(BaseModel):
    """Request for semantic vector search."""
    query: str = Field(..., description="Search query text")
    k: int = Field(default=10, ge=1, le=100, description="Number of results")
    collection_name: str | None = Field(default=None, description="Collection to search")
    source_filter: str | None = Field(default=None, description="Filter by source name")
    with_vectors: bool = Field(default=False, description="Include vector previews")


class ChunkResult(BaseModel):
    """A document chunk with metadata."""
    content: str
    content_preview: str
    metadata: dict[str, Any]
    similarity_score: float
    similarity_percent: float
    source: str
    source_name: str
    chunk_index: int | None = None


class VectorSearchResponse(BaseModel):
    """Response from vector search."""
    chunks: list[ChunkResult]
    total: int
    query: str
    collection: str | None


class CollectionStats(BaseModel):
    """Statistics for a Qdrant collection."""
    name: str
    vectors_count: int
    points_count: int
    indexed_vectors_count: int
    status: str
    dimensions: int
    distance_metric: str
    disk_data_size: int
    ram_data_size: int


class CollectionsResponse(BaseModel):
    """Response with all collections info."""
    collections: list[CollectionStats]
    total_vectors: int
    total_collections: int


class VectorBrowseResponse(BaseModel):
    """Response from browsing vectors."""
    points: list[dict]
    next_offset: str | None
    total_count: int
    collection: str


class EmbeddingRequest(BaseModel):
    """Request to generate an embedding."""
    text: str = Field(..., min_length=1, max_length=10000)


class EmbeddingResponse(BaseModel):
    """Response with embedding vector."""
    text: str
    vector: list[float]
    dimensions: int
    model: str


class RAGPipelineInfo(BaseModel):
    """Information about the RAG pipeline for educational purposes."""
    pipeline_stages: list[dict]
    retrieval_config: dict
    embedding_config: dict
    reranking_available: bool
    hybrid_search_enabled: bool


def _update_job_progress(
    source_id: int,
    status: str,
    progress: int,
    stage: str,
    message: str,
    **extra,
):
    """Update job progress with detailed info."""
    _ingestion_jobs[source_id] = {
        "status": status,
        "progress": progress,
        "stage": stage,
        "message": message,
        "updated_at": datetime.now().isoformat(),
        **extra,
    }
    logger.info(f"[Source {source_id}] {stage}: {message}")


def _is_cancelled(source_id: int) -> bool:
    """Check if a job has been cancelled."""
    return source_id in _cancelled_jobs


async def run_ingestion(source_id: int, request: IngestRequest):
    """Background task to run document ingestion."""
    db = get_db()
    start_time = time.time()

    try:
        _update_job_progress(
            source_id, "running", 0, "initializing", f"Starting ingestion for {request.name}..."
        )
        db.update_document_source(source_id, status="indexing")

        # Import ingesters
        from kgpt.ingestion import GitHubIngester, SitemapIngester
        from kgpt.ingestion.custom import CustomIngester
        from kgpt.vectorstore import get_vectorstore

        if _is_cancelled(source_id):
            raise InterruptedError("Ingestion cancelled by user")

        _update_job_progress(source_id, "running", 5, "connecting", "Connecting to vector store...")
        vectorstore = get_vectorstore()

        _update_job_progress(
            source_id, "running", 10, "fetching", f"Fetching content from {request.url}..."
        )

        logger.info(
            f"Ingesting source type: {request.source_type} (value: {request.source_type.value})"
        )

        # Create a progress callback that updates the job status and checks for cancellation
        def progress_callback(stage: str, progress: int, message: str, **extra):
            if _is_cancelled(source_id):
                raise InterruptedError("Ingestion cancelled by user")
            _update_job_progress(source_id, "running", progress, stage, message, **extra)

        if request.source_type.value == "sitemap":
            ingester = SitemapIngester(
                url=request.url,
                name=request.name,
                progress_callback=progress_callback,
            )
        elif request.source_type.value == "github":
            ingester = GitHubIngester(
                repo_url=request.url,
            )
        elif request.source_type.value == "url":
            ingester = CustomIngester(
                source=request.url,
                name=request.name,
            )
        else:
            raise ValueError(f"Unsupported source type: {request.source_type}")

        # Run document loading (progress updates happen via callback for sitemap)
        documents = await asyncio.to_thread(ingester.load_documents)
        doc_count_raw = len(documents)

        # Add to vector store
        if documents:
            _update_job_progress(
                source_id,
                "running",
                52,
                "chunking",
                f"Splitting {doc_count_raw} documents into chunks...",
            )
            chunks = ingester.split_documents(documents)
            chunk_count = len(chunks)

            _update_job_progress(
                source_id,
                "running",
                55,
                "embedding",
                f"Generating embeddings for {chunk_count} chunks...",
                chunks=chunk_count,
            )

            # Embed in batches for progress updates
            # Larger batches = faster (FastEmbed uses parallel processing internally)
            batch_size = 500
            for i in range(0, len(chunks), batch_size):
                # Check for cancellation before each batch
                if _is_cancelled(source_id):
                    raise InterruptedError("Ingestion cancelled by user")

                batch = chunks[i : i + batch_size]
                await asyncio.to_thread(vectorstore.add_documents, batch)

                done = min(i + batch_size, len(chunks))
                progress = int(55 + (done / len(chunks)) * 40)  # 55-95%
                _update_job_progress(
                    source_id,
                    "running",
                    progress,
                    "embedding",
                    f"Embedded {done}/{chunk_count} chunks...",
                    chunks=chunk_count,
                    chunks_embedded=done,
                )

            doc_count = chunk_count
        else:
            doc_count = 0
            logger.warning(f"No documents loaded from {request.url}")

        elapsed = time.time() - start_time

        # Update database
        db.update_document_source(
            source_id,
            status="indexed",
            document_count=doc_count,
            indexed_at=datetime.now(),
        )

        _update_job_progress(
            source_id,
            "completed",
            100,
            "done",
            f"Successfully indexed {doc_count} chunks from {doc_count_raw} pages in {elapsed:.1f}s",
            count=doc_count,
            pages=doc_count_raw,
            elapsed_seconds=round(elapsed, 1),
        )

    except InterruptedError:
        elapsed = time.time() - start_time
        logger.info(f"Ingestion cancelled for source {source_id}")
        db.update_document_source(source_id, status="cancelled")
        _update_job_progress(
            source_id,
            "cancelled",
            0,
            "cancelled",
            f"Ingestion cancelled after {elapsed:.1f}s",
            elapsed_seconds=round(elapsed, 1),
        )
        # Clean up cancelled set
        _cancelled_jobs.discard(source_id)
        return

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"Ingestion error for source {source_id}: {error_msg}")
        db.update_document_source(source_id, status="error")
        _update_job_progress(
            source_id,
            "error",
            0,
            "failed",
            f"Ingestion failed: {error_msg}",
            error=error_msg,
            elapsed_seconds=round(elapsed, 1),
        )


@router.get("", response_model=DocumentsListResponse)
async def list_documents() -> DocumentsListResponse:
    """List all document sources."""
    db = get_db()
    sources = db.get_document_sources()

    return DocumentsListResponse(
        sources=[DocumentSource(**s) for s in sources],
        total=len(sources),
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
) -> IngestResponse:
    """
    Start a document ingestion job.

    This endpoint returns immediately and runs ingestion in the background.
    Use GET /documents/{id}/status to check progress.
    """
    db = get_db()

    # Create document source entry
    source_id = db.add_document_source(
        name=request.name,
        source_type=request.source_type.value,
        url=request.url,
        collection_name=request.collection_name,
    )

    # Start background ingestion
    background_tasks.add_task(run_ingestion, source_id, request)

    return IngestResponse(
        source_id=source_id,
        status="started",
        message=f"Ingestion started for {request.name}",
    )


@router.get("/{source_id}/status")
async def get_ingestion_status(source_id: int) -> dict:
    """Get the status of an ingestion job."""
    if source_id in _ingestion_jobs:
        return _ingestion_jobs[source_id]

    # Check database for status
    db = get_db()
    sources = db.get_document_sources()
    for source in sources:
        if source["id"] == source_id:
            return {
                "status": source["status"],
                "document_count": source["document_count"],
            }

    raise HTTPException(status_code=404, detail="Source not found")


@router.post("/{source_id}/cancel")
async def cancel_ingestion(source_id: int) -> dict:
    """Cancel an ongoing ingestion job."""
    db = get_db()
    sources = db.get_document_sources()
    source = next((s for s in sources if s["id"] == source_id), None)

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source["status"] != "indexing":
        raise HTTPException(status_code=400, detail="Source is not currently indexing")

    # Mark as cancelled - the background task will pick this up
    _cancelled_jobs.add(source_id)
    logger.info(f"Cancellation requested for source {source_id}")

    return {"status": "cancelling", "source_id": source_id}


@router.delete("/{source_id}")
async def delete_document_source(source_id: int) -> dict:
    """Delete a document source and optionally its vectors."""
    db = get_db()

    # Get source info first
    sources = db.get_document_sources()
    source = next((s for s in sources if s["id"] == source_id), None)

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # If it's indexing, cancel it first
    if source["status"] == "indexing":
        _cancelled_jobs.add(source_id)

    # Delete from database
    db.delete_document_source(source_id)

    # Clean up job tracking
    if source_id in _ingestion_jobs:
        del _ingestion_jobs[source_id]
    _cancelled_jobs.discard(source_id)

    return {"status": "deleted", "source_id": source_id}


@router.post("/ingest/confluent")
async def ingest_confluent_docs(background_tasks: BackgroundTasks) -> IngestResponse:
    """Convenience endpoint to ingest Confluent documentation."""
    request = IngestRequest(
        name="Confluent Documentation",
        source_type=SourceType.SITEMAP,
        url="https://docs.confluent.io/home/sitemap.xml",
        collection_name="kgpt_docs",
    )
    return await ingest_documents(request, background_tasks)


@router.post("/ingest/kafka")
async def ingest_kafka_docs(background_tasks: BackgroundTasks) -> IngestResponse:
    """Convenience endpoint to ingest Apache Kafka documentation."""
    request = IngestRequest(
        name="Apache Kafka Documentation",
        source_type=SourceType.SITEMAP,
        url="https://kafka.apache.org/sitemap.xml",
        collection_name="kgpt_docs",
    )
    return await ingest_documents(request, background_tasks)


# ============================================================================
# Vector Search and Browsing Endpoints
# ============================================================================


@router.post("/search", response_model=VectorSearchResponse)
async def search_documents(request: VectorSearchRequest) -> VectorSearchResponse:
    """
    Perform semantic search across indexed documents.
    
    This endpoint demonstrates the core of RAG retrieval:
    1. Your query text is converted to an embedding vector
    2. The vector is compared against all stored document chunks
    3. The most similar chunks are returned with their similarity scores
    """
    from kgpt.vectorstore import get_vectorstore
    
    store = get_vectorstore()
    
    try:
        chunks = store.search_chunks(
            query=request.query,
            collection_name=request.collection_name,
            k=request.k,
            source_filter=request.source_filter,
            with_vectors=request.with_vectors,
        )
        
        return VectorSearchResponse(
            chunks=[ChunkResult(**c) for c in chunks],
            total=len(chunks),
            query=request.query,
            collection=request.collection_name,
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_documents_get(
    q: str = Query(..., description="Search query"),
    k: int = Query(default=10, ge=1, le=100),
    collection: str | None = Query(default=None),
    source: str | None = Query(default=None),
) -> VectorSearchResponse:
    """GET version of search for convenience."""
    return await search_documents(
        VectorSearchRequest(
            query=q,
            k=k,
            collection_name=collection,
            source_filter=source,
        )
    )


# ============================================================================
# Collection Management Endpoints
# ============================================================================


@router.get("/collections", response_model=CollectionsResponse)
async def list_collections() -> CollectionsResponse:
    """
    Get information about all Qdrant collections.
    
    Shows the underlying vector database state, including:
    - Number of vectors stored
    - Embedding dimensions
    - Index status
    - Memory usage
    """
    from kgpt.vectorstore import get_vectorstore
    
    store = get_vectorstore()
    
    try:
        collections_info = store.get_all_collections_info()
        
        total_vectors = sum(c.get("vectors_count", 0) for c in collections_info)
        
        return CollectionsResponse(
            collections=[CollectionStats(**c) for c in collections_info],
            total_vectors=total_vectors,
            total_collections=len(collections_info),
        )
        
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}", response_model=CollectionStats)
async def get_collection(collection_name: str) -> CollectionStats:
    """Get detailed information about a specific collection."""
    from kgpt.vectorstore import get_vectorstore
    
    store = get_vectorstore()
    info = store.get_collection_info(collection_name)
    
    if info.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return CollectionStats(**info)


@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str) -> dict:
    """Delete a collection and all its vectors."""
    from kgpt.vectorstore import get_vectorstore
    
    store = get_vectorstore()
    
    try:
        store.delete_collection(collection_name)
        return {"status": "deleted", "collection": collection_name}
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/sources")
async def get_collection_sources(collection_name: str) -> dict:
    """Get unique source names in a collection."""
    from kgpt.vectorstore import get_vectorstore
    
    store = get_vectorstore()
    
    try:
        sources = store.get_metadata_values("source_name", collection_name)
        return {
            "collection": collection_name,
            "sources": sources,
            "count": len(sources),
        }
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Vector Browsing Endpoints
# ============================================================================


@router.get("/vectors/browse", response_model=VectorBrowseResponse)
async def browse_vectors(
    collection: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: str | None = Query(default=None),
    source: str | None = Query(default=None),
    with_vectors: bool = Query(default=False),
) -> VectorBrowseResponse:
    """
    Browse vectors in a collection with pagination.
    
    This is useful for inspecting what's actually stored in the vector database.
    Each point includes:
    - The document chunk text (in payload)
    - Metadata (source, timestamps, etc.)
    - Optionally, a preview of the embedding vector
    """
    from kgpt.vectorstore import get_vectorstore
    
    store = get_vectorstore()
    collection_name = collection or store.collection_name
    
    filter_metadata = {"source_name": source} if source else None
    
    try:
        result = store.scroll_vectors(
            collection_name=collection_name,
            limit=limit,
            offset=offset,
            filter_metadata=filter_metadata,
            with_vectors=with_vectors,
        )
        
        return VectorBrowseResponse(
            points=result["points"],
            next_offset=result["next_offset"],
            total_count=result["total_count"],
            collection=collection_name,
        )
        
    except Exception as e:
        logger.error(f"Error browsing vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vectors/{point_id}")
async def get_vector(
    point_id: str,
    collection: str | None = Query(default=None),
    with_vector: bool = Query(default=True),
) -> dict:
    """
    Get a specific vector point by ID.
    
    Returns the full document chunk, all metadata, and optionally
    the complete embedding vector (useful for debugging).
    """
    from kgpt.vectorstore import get_vectorstore
    
    store = get_vectorstore()
    collection_name = collection or store.collection_name
    
    point = store.get_point_by_id(point_id, collection_name, with_vector)
    
    if not point:
        raise HTTPException(status_code=404, detail="Vector not found")
    
    return point


@router.delete("/vectors/by-source/{source_name}")
async def delete_vectors_by_source(
    source_name: str,
    collection: str | None = Query(default=None),
) -> dict:
    """
    Delete all vectors from a specific source.
    
    This removes all document chunks that were ingested from a particular source,
    without affecting other documents in the collection.
    """
    from kgpt.vectorstore import get_vectorstore
    
    store = get_vectorstore()
    collection_name = collection or store.collection_name
    
    deleted_count = store.delete_by_source(source_name, collection_name)
    
    return {
        "status": "deleted",
        "source_name": source_name,
        "deleted_count": deleted_count,
        "collection": collection_name,
    }


# ============================================================================
# Embedding Endpoints (Educational)
# ============================================================================


@router.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    """
    Generate an embedding vector for a text string.
    
    This shows how text is converted to vectors in the RAG pipeline:
    1. Text is passed through an embedding model
    2. The model outputs a dense vector (e.g., 1536 dimensions for OpenAI)
    3. This vector captures the semantic meaning of the text
    4. Similar texts have vectors that are close together
    """
    from kgpt.db import get_db
    from kgpt.vectorstore import get_vectorstore
    
    db = get_db()
    store = get_vectorstore()
    
    try:
        vector = store.get_embedding_for_text(request.text)
        
        # Get current embedding model name
        embedding_model = db.get_setting("embedding_model") or "text-embedding-3-small"
        
        return EmbeddingResponse(
            text=request.text[:200] + "..." if len(request.text) > 200 else request.text,
            vector=vector,
            dimensions=len(vector),
            model=embedding_model,
        )
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed/compare")
async def compare_embeddings(
    text1: str = Query(..., description="First text to compare"),
    text2: str = Query(..., description="Second text to compare"),
) -> dict:
    """
    Compare the similarity between two text strings.
    
    This demonstrates how semantic search works:
    1. Both texts are converted to embedding vectors
    2. We calculate the cosine similarity between them
    3. Higher similarity (closer to 1.0) means more related meaning
    """
    from kgpt.vectorstore import get_vectorstore
    import math
    
    store = get_vectorstore()
    
    try:
        vec1 = store.get_embedding_for_text(text1)
        vec2 = store.get_embedding_for_text(text2)
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        similarity = dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0
        
        return {
            "text1": text1[:100] + "..." if len(text1) > 100 else text1,
            "text2": text2[:100] + "..." if len(text2) > 100 else text2,
            "cosine_similarity": round(similarity, 4),
            "similarity_percent": round(similarity * 100, 1),
            "interpretation": (
                "Very similar" if similarity > 0.8 else
                "Somewhat similar" if similarity > 0.6 else
                "Loosely related" if similarity > 0.4 else
                "Not very similar" if similarity > 0.2 else
                "Unrelated"
            ),
        }
        
    except Exception as e:
        logger.error(f"Error comparing embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RAG Pipeline Info (Educational)
# ============================================================================


@router.get("/rag/pipeline", response_model=RAGPipelineInfo)
async def get_rag_pipeline_info() -> RAGPipelineInfo:
    """
    Get information about the RAG pipeline configuration.
    
    This endpoint explains how the retrieval-augmented generation system works,
    including all the stages from query to answer.
    """
    from kgpt.db import get_db
    
    db = get_db()
    
    # Check if reranking is available
    cohere_key = db.get_setting("cohere_api_key")
    reranking_available = bool(cohere_key)
    
    # Try to detect sentence-transformers
    try:
        from sentence_transformers import CrossEncoder
        reranking_available = True
    except ImportError:
        pass
    
    return RAGPipelineInfo(
        pipeline_stages=[
            {
                "name": "Query Expansion",
                "description": "Generate alternative phrasings of the user's question to improve recall",
                "example": "Original: 'How do I configure Kafka?' → Variations: 'Kafka configuration settings', 'Setting up Kafka parameters'",
            },
            {
                "name": "Embedding Generation",
                "description": "Convert the query into a dense vector representation",
                "example": "Text → [0.012, -0.034, 0.056, ...] (1536 dimensions)",
            },
            {
                "name": "Vector Search",
                "description": "Find document chunks with similar embeddings using cosine similarity",
                "example": "Query vector compared against ~10,000 stored document vectors",
            },
            {
                "name": "Hybrid Scoring",
                "description": "Combine dense vector similarity with keyword matching (BM25-style)",
                "example": "RRF fusion: 0.7 × dense_score + 0.3 × keyword_score",
            },
            {
                "name": "Reranking",
                "description": "Use a cross-encoder model to re-score and reorder results",
                "example": "Cohere rerank-v3 or ms-marco MiniLM cross-encoder",
            },
            {
                "name": "Context Assembly",
                "description": "Combine top-ranked chunks into a context window for the LLM",
                "example": "Top 5-10 chunks assembled as context",
            },
            {
                "name": "Answer Generation",
                "description": "LLM generates an answer based on the retrieved context",
                "example": "GPT-4 synthesizes answer from context + question",
            },
        ],
        retrieval_config={
            "top_k_initial": 20,
            "top_k_final": 10,
            "hybrid_alpha": 0.7,
            "query_expansion_count": 3,
        },
        embedding_config={
            "model": db.get_setting("embedding_model") or "text-embedding-3-small",
            "provider": db.get_setting("embedding_provider") or "openai",
            "dimensions": 1536,
        },
        reranking_available=reranking_available,
        hybrid_search_enabled=True,
    )


@router.get("/rag/demo")
async def rag_demo(query: str = Query(..., description="Demo query")) -> dict:
    """
    Demonstrate the full RAG pipeline step by step.
    
    This endpoint shows what happens at each stage of retrieval,
    making it educational for understanding how RAG works.
    """
    from kgpt.vectorstore import get_vectorstore
    from kgpt.agents.retrieval import expand_queries
    
    store = get_vectorstore()
    
    steps = []
    
    # Step 1: Query expansion
    try:
        expanded = await expand_queries(query)
        steps.append({
            "step": 1,
            "name": "Query Expansion",
            "input": query,
            "output": expanded,
            "description": "Generated alternative phrasings to improve search coverage",
        })
    except Exception as e:
        expanded = [query]
        steps.append({
            "step": 1,
            "name": "Query Expansion",
            "input": query,
            "output": [query],
            "error": str(e),
        })
    
    # Step 2: Generate embedding
    try:
        embedding = store.get_embedding_for_text(query)
        steps.append({
            "step": 2,
            "name": "Embedding Generation",
            "input": query[:100],
            "output": {
                "dimensions": len(embedding),
                "preview": embedding[:5],
                "model": "text-embedding-3-small",
            },
            "description": "Converted query text to a dense vector representation",
        })
    except Exception as e:
        steps.append({
            "step": 2,
            "name": "Embedding Generation",
            "error": str(e),
        })
        embedding = []
    
    # Step 3: Vector search
    try:
        results = store.search_chunks(query, k=5)
        steps.append({
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
        })
    except Exception as e:
        steps.append({
            "step": 3,
            "name": "Vector Search",
            "error": str(e),
        })
        results = []
    
    # Step 4: Summary
    steps.append({
        "step": 4,
        "name": "Context Assembly",
        "description": f"Would assemble top {len(results)} chunks as context for LLM",
        "total_context_length": sum(len(r.get("content", "")) for r in results),
    })
    
    return {
        "query": query,
        "pipeline_steps": steps,
        "total_steps": len(steps),
    }
