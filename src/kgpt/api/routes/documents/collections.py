"""Collection management endpoints for Qdrant collections."""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel


router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class HNSWConfig(BaseModel):
    """HNSW index configuration - critical for search performance."""

    m: int | None = None  # Number of edges per node
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


# ============================================================================
# Collection Endpoints
# ============================================================================


@router.get("", response_model=CollectionsResponse)
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


@router.get("/{collection_name}", response_model=CollectionStats)
async def get_collection(collection_name: str) -> CollectionStats:
    """Get detailed information about a specific collection."""
    from kgpt.vectorstore import get_vectorstore

    store = get_vectorstore()
    info = store.get_collection_info(collection_name)

    if info.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Collection not found")

    return CollectionStats(**info)


@router.delete("/{collection_name}")
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


@router.get("/{collection_name}/sources")
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
