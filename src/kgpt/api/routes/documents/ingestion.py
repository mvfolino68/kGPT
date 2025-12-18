"""Ingestion endpoints for managing document sources and background ingestion jobs."""

import asyncio
import time
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from kgpt.api.schemas import (
    DocumentsListResponse,
    DocumentSource,
    IngestRequest,
    IngestResponse,
    NameSuggestionRequest,
    NameSuggestionResponse,
)
from kgpt.db import get_db
from kgpt.ingestion import generate_smart_name, suggest_names_for_url

router = APIRouter()

# Track ongoing ingestion jobs with detailed progress
_ingestion_jobs: dict[int, dict] = {}
# Track cancelled jobs
_cancelled_jobs: set[int] = set()


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

            # Add metadata to chunks (source_name is critical for retrieval display)
            source_name = ingester.get_source_name()
            source_type = ingester.get_source_type()
            for chunk in chunks:
                chunk.metadata["source_name"] = source_name
                chunk.metadata["source_type"] = source_type
                chunk.metadata["ingested_at"] = datetime.now().isoformat()

            _update_job_progress(
                source_id,
                "running",
                55,
                "embedding",
                f"Generating embeddings for {chunk_count} chunks...",
                chunks=chunk_count,
            )

            # Embed in batches for progress updates
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


@router.post("/suggest-name", response_model=NameSuggestionResponse)
async def suggest_name(request: NameSuggestionRequest) -> NameSuggestionResponse:
    """Get AI-powered name suggestions for a document source URL."""
    # Get quick suggestions from URL parsing
    suggestions = suggest_names_for_url(request.url)

    # Get smart AI-generated name
    smart_name = None
    try:
        smart_name = await generate_smart_name(
            url=request.url,
            source_type=request.source_type.value,
        )
    except Exception as e:
        logger.warning(f"Smart naming failed: {e}")

    return NameSuggestionResponse(
        suggestions=suggestions,
        smart_name=smart_name,
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

    If name is not provided and auto_name is True, an AI-generated name will be used.
    """
    db = get_db()

    # Generate smart name if needed
    source_name = request.name
    if not source_name and request.auto_name and request.url:
        try:
            source_name = await generate_smart_name(
                url=request.url,
                source_type=request.source_type.value,
            )
        except Exception as e:
            logger.warning(f"Smart naming failed, using URL fallback: {e}")
            from kgpt.ingestion import suggest_names_for_url

            suggestions = suggest_names_for_url(request.url)
            source_name = suggestions[0] if suggestions else "Unnamed Source"
    elif not source_name:
        source_name = "Unnamed Source"

    # Create document source entry
    source_id = db.add_document_source(
        name=source_name,
        source_type=request.source_type.value,
        url=request.url,
        collection_name=request.collection_name,
    )

    # Update request with the resolved name for the background task
    request_with_name = IngestRequest(
        name=source_name,
        source_type=request.source_type,
        url=request.url,
        collection_name=request.collection_name,
        auto_name=False,
    )

    # Start background ingestion
    background_tasks.add_task(run_ingestion, source_id, request_with_name)

    return IngestResponse(
        source_id=source_id,
        status="started",
        message=f"Ingestion started for {source_name}",
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


# Legacy convenience endpoints removed - use Exa web search for public docs
# For internal docs, use the /ingest endpoint with URL, GitHub, or File source types
