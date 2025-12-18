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


class HNSWConfig(BaseModel):
    """HNSW index configuration - critical for search performance."""

    m: int | None = None  # Number of edges per node (higher = better recall, more memory)
    ef_construct: int | None = None  # Construction-time search width
    full_scan_threshold: int | None = None  # Below this, brute force is used
    on_disk: bool = False  # Whether HNSW graph is stored on disk


class CollectionStats(BaseModel):
    """Comprehensive statistics for a Qdrant collection."""

    name: str
    vectors_count: int = 0
    points_count: int = 0
    indexed_vectors_count: int = 0
    segments_count: int = 0
    status: str = "unknown"
    optimizer_status: str = "ok"
    dimensions: int = 0
    distance_metric: str = "unknown"
    on_disk_vectors: bool | None = False
    on_disk_payload: bool | None = False
    disk_data_size: int = 0
    ram_data_size: int = 0
    hnsw_config: HNSWConfig | None = None
    optimizer_config: dict | None = None
    quantization_config: dict | None = None
    payload_schema: dict | None = None


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


# ============================================================================
# Sync and Cleanup Endpoints (MUST be before parametric /{source_id} routes)
# ============================================================================


@router.get("/sync/status")
async def get_sync_status() -> dict:
    """
    Compare database sources with actual Qdrant vectors.

    Returns information about:
    - Sources in DB that have no vectors in Qdrant
    - Sources in Qdrant that aren't tracked in DB (orphans)
    - Mismatched counts
    """
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    try:
        # Get sources from database
        db_sources = db.get_document_sources()
        db_source_names = {s["name"] for s in db_sources}

        # Get sources actually in Qdrant
        qdrant_sources = set(store.get_metadata_values("source_name"))

        # Find discrepancies
        orphaned_in_qdrant = qdrant_sources - db_source_names  # In Qdrant but not DB
        missing_in_qdrant = db_source_names - qdrant_sources  # In DB but not Qdrant

        # Get collection info
        collection_info = store.get_collection_info()

        # Build detailed source status
        source_status = []
        for source in db_sources:
            name = source["name"]
            in_qdrant = name in qdrant_sources
            source_status.append(
                {
                    "id": source["id"],
                    "name": name,
                    "db_status": source["status"],
                    "db_count": source["document_count"],
                    "in_qdrant": in_qdrant,
                    "synced": in_qdrant and source["status"] == "indexed",
                }
            )

        return {
            "synced": len(orphaned_in_qdrant) == 0 and len(missing_in_qdrant) == 0,
            "collection": collection_info,
            "db_sources_count": len(db_sources),
            "qdrant_sources_count": len(qdrant_sources),
            "orphaned_sources": list(orphaned_in_qdrant),
            "missing_sources": list(missing_in_qdrant),
            "source_status": source_status,
        }

    except Exception as e:
        logger.error(f"Error checking sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/cleanup-orphans")
async def cleanup_orphan_vectors() -> dict:
    """
    Delete vectors from Qdrant that don't have a corresponding source in the database.

    This cleans up orphaned vectors from partial ingestions or deleted sources.
    """
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    try:
        # Get sources from database
        db_sources = db.get_document_sources()
        db_source_names = {s["name"] for s in db_sources}

        # Get sources actually in Qdrant
        qdrant_sources = set(store.get_metadata_values("source_name"))

        # Find orphans (in Qdrant but not in DB)
        orphaned_sources = qdrant_sources - db_source_names

        total_deleted = 0
        deleted_sources = []

        for source_name in orphaned_sources:
            try:
                deleted_count = store.delete_by_source(source_name)
                total_deleted += deleted_count
                deleted_sources.append(
                    {
                        "name": source_name,
                        "vectors_deleted": deleted_count,
                    }
                )
                logger.info(f"Cleaned up orphan source '{source_name}': {deleted_count} vectors")
            except Exception as e:
                logger.warning(f"Failed to clean up '{source_name}': {e}")
                deleted_sources.append(
                    {
                        "name": source_name,
                        "error": str(e),
                    }
                )

        return {
            "status": "completed",
            "orphans_found": len(orphaned_sources),
            "total_vectors_deleted": total_deleted,
            "deleted_sources": deleted_sources,
        }

    except Exception as e:
        logger.error(f"Error cleaning up orphans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/cleanup-stale")
async def cleanup_stale_db_entries() -> dict:
    """
    Remove database entries that have no corresponding vectors in Qdrant.

    This cleans up DB entries from failed or cancelled ingestions.
    """
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    try:
        # Get sources from database
        db_sources = db.get_document_sources()

        # Get sources actually in Qdrant
        qdrant_sources = set(store.get_metadata_values("source_name"))

        cleaned_entries = []

        for source in db_sources:
            name = source["name"]
            # If source is "indexed" but not in Qdrant, or is in error/cancelled state
            if name not in qdrant_sources and source["status"] in [
                "indexed",
                "error",
                "cancelled",
            ]:
                try:
                    db.delete_document_source(source["id"])
                    cleaned_entries.append(
                        {
                            "id": source["id"],
                            "name": name,
                            "status": source["status"],
                        }
                    )
                    logger.info(f"Cleaned up stale DB entry: {name} (id={source['id']})")
                except Exception as e:
                    logger.warning(f"Failed to clean up DB entry {source['id']}: {e}")

        return {
            "status": "completed",
            "entries_cleaned": len(cleaned_entries),
            "cleaned": cleaned_entries,
        }

    except Exception as e:
        logger.error(f"Error cleaning up stale entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sync/purge-all")
async def purge_all_data() -> dict:
    """
    DANGER: Delete ALL vectors and database entries.

    This is a nuclear option to start fresh.
    """
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    try:
        # Get counts before
        db_sources = db.get_document_sources()
        collection_info = store.get_collection_info()

        # Delete all sources from database
        for source in db_sources:
            db.delete_document_source(source["id"])

        # Delete the collection (recreates empty)
        store.delete_collection()

        return {
            "status": "purged",
            "db_entries_deleted": len(db_sources),
            "vectors_deleted": collection_info.get("vectors_count", 0),
        }

    except Exception as e:
        logger.error(f"Error purging data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Parametric Source ID Routes (must be after specific routes like /sync/*)
# ============================================================================


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
    """Delete a document source AND its vectors from Qdrant."""
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    # Get source info first
    sources = db.get_document_sources()
    source = next((s for s in sources if s["id"] == source_id), None)

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source_name = source["name"]
    deleted_vectors = 0

    # If it's indexing, cancel it first
    if source["status"] == "indexing":
        _cancelled_jobs.add(source_id)

    # Delete vectors from Qdrant using the source name
    try:
        deleted_vectors = store.delete_by_source(source_name)
        logger.info(f"Deleted {deleted_vectors} vectors for source '{source_name}'")
    except Exception as e:
        logger.warning(f"Failed to delete vectors for source '{source_name}': {e}")

    # Delete from database
    db.delete_document_source(source_id)

    # Clean up job tracking
    if source_id in _ingestion_jobs:
        del _ingestion_jobs[source_id]
    _cancelled_jobs.discard(source_id)

    return {
        "status": "deleted",
        "source_id": source_id,
        "source_name": source_name,
        "vectors_deleted": deleted_vectors,
    }


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
    import math

    from kgpt.vectorstore import get_vectorstore

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
                "Very similar"
                if similarity > 0.8
                else "Somewhat similar"
                if similarity > 0.6
                else "Loosely related"
                if similarity > 0.4
                else "Not very similar"
                if similarity > 0.2
                else "Unrelated"
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
    including all the stages from query to answer. Stages are dynamically
    determined based on actual system configuration.
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

    # Check if hybrid search is actually enabled
    hybrid_enabled = True  # Qdrant supports hybrid search by default

    # Get actual embedding config from vectorstore
    embedding_model = db.get_setting("embedding_model") or "text-embedding-3-small"
    embedding_provider = db.get_setting("embedding_provider") or "openai"

    # Determine embedding dimensions based on model and provider
    embedding_dims = 1536  # default fallback

    # Provider-specific dimension detection
    if embedding_provider == "openai":
        if "text-embedding-3-large" in embedding_model:
            embedding_dims = 3072
        elif "text-embedding-3-small" in embedding_model or "ada-002" in embedding_model:
            embedding_dims = 1536
    elif embedding_provider == "fastembed":
        # FastEmbed model dimensions
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
        elif "gte-small" in embedding_model:
            embedding_dims = 384
    elif embedding_provider == "cohere":
        if "embed-english-v3" in embedding_model or "embed-multilingual-v3" in embedding_model:
            embedding_dims = 1024
    elif embedding_provider == "huggingface":
        # Try to get actual dimensions from the vectorstore collection if available
        try:
            if collections:
                # Get the first collection and check its vector size
                collection_info = store.get_collection(collections[0])
                if hasattr(collection_info, "config") and hasattr(collection_info.config, "params"):
                    embedding_dims = collection_info.config.params.vectors.size
        except Exception:
            pass  # Keep default if we can't detect

    # Build pipeline stages dynamically based on what's actually configured
    stages = []

    # Stage 1: Query Expansion (always enabled)
    stages.append(
        {
            "name": "Query Expansion",
            "description": "Generate alternative phrasings of the user's question to improve recall",
            "example": "Original: 'How do I configure Kafka?' → Generates 2-3 alternative phrasings",
        }
    )

    # Stage 2: Embedding Generation (always enabled)
    stages.append(
        {
            "name": "Embedding Generation",
            "description": f"Convert the query into a dense vector using {embedding_provider} {embedding_model}",
            "example": f"Text → [{embedding_dims}-dimensional vector]",
        }
    )

    # Stage 3: Vector Search (always enabled)
    collections = store.list_collections()
    stages.append(
        {
            "name": "Vector Search",
            "description": f"Search {len(collections)} collection(s) using cosine similarity",
            "example": f"Query vector compared against document vectors in: {', '.join(collections[:3])}{'...' if len(collections) > 3 else ''}",
        }
    )

    # Stage 4: Hybrid Scoring (if enabled)
    if hybrid_enabled:
        stages.append(
            {
                "name": "Hybrid Scoring",
                "description": "Combine dense vector similarity with keyword matching (BM25-style)",
                "example": "RRF fusion: 0.7 × dense_score + 0.3 × keyword_score",
            }
        )

    # Stage 5: Reranking (if available)
    if reranking_available:
        stages.append(
            {
                "name": "Reranking",
                "description": f"Re-score and reorder results using {reranking_method}",
                "example": "Cross-encoder model scores query-document pairs for better precision",
            }
        )

    # Stage 6: Deduplication (always enabled)
    stages.append(
        {
            "name": "Deduplication",
            "description": "Remove duplicate content from multiple query expansions",
            "example": "Hash-based deduplication ensures unique results",
        }
    )

    # Stage 7: Context Assembly (always enabled)
    stages.append(
        {
            "name": "Context Assembly",
            "description": "Combine top-ranked chunks into a context window for the LLM",
            "example": "Top 10 chunks assembled as context",
        }
    )

    # Stage 8: Answer Generation (always enabled)
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


@router.get("/rag/demo")
async def rag_demo(query: str = Query(..., description="Demo query")) -> dict:
    """
    Demonstrate the full RAG pipeline step by step.

    This endpoint shows what happens at each stage of retrieval,
    making it educational for understanding how RAG works.
    """
    from kgpt.agents.retrieval import expand_queries
    from kgpt.vectorstore import get_vectorstore

    store = get_vectorstore()

    steps = []

    # Step 1: Query expansion
    try:
        expanded = await expand_queries(query)
        steps.append(
            {
                "step": 1,
                "name": "Query Expansion",
                "input": query,
                "output": expanded,
                "description": "Generated alternative phrasings to improve search coverage",
            }
        )
    except Exception as e:
        expanded = [query]
        steps.append(
            {
                "step": 1,
                "name": "Query Expansion",
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


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get("/analytics/chunks")
async def get_chunk_analytics(
    collection: str | None = Query(default=None),
    sample_size: int = Query(default=100, ge=10, le=1000),
) -> dict:
    """
    Get analytics about stored document chunks.

    Provides insights into:
    - Chunk size distribution
    - Source breakdown
    - Content type analysis
    """
    from kgpt.vectorstore import get_vectorstore

    store = get_vectorstore()
    collection_name = collection or store.collection_name

    try:
        # Sample chunks for analysis
        result = store.scroll_vectors(
            collection_name=collection_name,
            limit=sample_size,
            with_vectors=False,
        )

        chunks = result.get("points", [])

        if not chunks:
            return {
                "collection": collection_name,
                "total_sampled": 0,
                "message": "No chunks found",
            }

        # Analyze chunk sizes
        chunk_sizes = []
        sources: dict[str, int] = {}
        source_types: dict[str, int] = {}

        for chunk in chunks:
            payload = chunk.get("payload", {})
            metadata = payload.get("metadata", {})
            content = payload.get("page_content", "")

            # Track chunk size
            chunk_sizes.append(len(content))

            # Track sources
            source_name = metadata.get("source_name", "unknown")
            sources[source_name] = sources.get(source_name, 0) + 1

            # Track source types
            source_type = metadata.get("source_type", "unknown")
            source_types[source_type] = source_types.get(source_type, 0) + 1

        # Calculate statistics
        avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
        min_size = min(chunk_sizes) if chunk_sizes else 0
        max_size = max(chunk_sizes) if chunk_sizes else 0

        # Size distribution buckets
        size_distribution = {
            "0-500": 0,
            "500-1000": 0,
            "1000-2000": 0,
            "2000-4000": 0,
            "4000+": 0,
        }
        for size in chunk_sizes:
            if size < 500:
                size_distribution["0-500"] += 1
            elif size < 1000:
                size_distribution["500-1000"] += 1
            elif size < 2000:
                size_distribution["1000-2000"] += 1
            elif size < 4000:
                size_distribution["2000-4000"] += 1
            else:
                size_distribution["4000+"] += 1

        # Get collection info for total count
        collection_info = store.get_collection_info(collection_name)

        return {
            "collection": collection_name,
            "total_vectors": collection_info.get("vectors_count", 0),
            "total_sampled": len(chunks),
            "chunk_size_stats": {
                "avg_chars": round(avg_size),
                "min_chars": min_size,
                "max_chars": max_size,
                "avg_tokens_estimate": round(avg_size / 4),  # Rough token estimate
            },
            "size_distribution": size_distribution,
            "sources": dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)),
            "source_types": source_types,
            "index_health": {
                "indexed_vectors": collection_info.get("indexed_vectors_count", 0),
                "segments": collection_info.get("segments_count", 0),
                "optimizer_status": collection_info.get("optimizer_status", "unknown"),
            },
        }

    except Exception as e:
        logger.error(f"Error getting chunk analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/search-quality")
async def test_search_quality(
    query: str = Query(..., description="Test query"),
    expected_source: str | None = Query(default=None, description="Expected source name"),
) -> dict:
    """
    Test search quality for a given query.

    Returns metrics about how well the search performs.
    """
    from kgpt.vectorstore import get_vectorstore

    store = get_vectorstore()

    try:
        # Run search
        results = store.search_chunks(query, k=10)

        if not results:
            return {
                "query": query,
                "results_found": 0,
                "message": "No results found",
            }

        # Analyze results
        scores = [r["similarity_percent"] for r in results]
        sources_found = list({r.get("source_name", "unknown") for r in results})

        # Calculate quality metrics
        avg_score = sum(scores) / len(scores) if scores else 0
        score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores) if scores else 0

        # Check if expected source is in top results
        expected_match = None
        if expected_source:
            for i, r in enumerate(results):
                if r.get("source_name") == expected_source:
                    expected_match = {"rank": i + 1, "score": r["similarity_percent"]}
                    break

        return {
            "query": query,
            "results_found": len(results),
            "quality_metrics": {
                "avg_similarity": round(avg_score, 1),
                "top_score": max(scores) if scores else 0,
                "score_spread": round(max(scores) - min(scores), 1) if scores else 0,
                "score_variance": round(score_variance, 2),
            },
            "sources_matched": sources_found,
            "expected_source_match": expected_match,
            "top_3_preview": [
                {
                    "rank": i + 1,
                    "score": r["similarity_percent"],
                    "source": r.get("source_name"),
                    "preview": r["content_preview"][:100] + "...",
                }
                for i, r in enumerate(results[:3])
            ],
        }

    except Exception as e:
        logger.error(f"Error testing search quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))
