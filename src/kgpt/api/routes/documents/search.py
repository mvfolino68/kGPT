"""Search and browsing endpoints for vector operations."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter()


# ============================================================================
# Schemas
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


class VectorBrowseResponse(BaseModel):
    """Response from browsing vectors."""

    points: list[dict]
    next_offset: str | None
    total_count: int
    collection: str


# ============================================================================
# Search Endpoints
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
