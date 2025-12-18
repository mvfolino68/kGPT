"""Documents API module - orchestrates all document-related endpoints."""

from fastapi import APIRouter

from . import analytics, collections, embeddings, ingestion, rag_pipeline, search, sync

# Create main router
router = APIRouter(prefix="/documents", tags=["documents"])

# Include submodule routers with their specific prefixes
router.include_router(ingestion.router, prefix="/sources", tags=["ingestion"])
router.include_router(search.router, tags=["search"])  # Has its own /search and /vectors paths
router.include_router(collections.router, prefix="/collections", tags=["collections"])
router.include_router(sync.router, prefix="/sync", tags=["sync"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(embeddings.router, prefix="/embed", tags=["embeddings"])
router.include_router(rag_pipeline.router, prefix="/rag", tags=["rag-pipeline"])

__all__ = ["router"]
