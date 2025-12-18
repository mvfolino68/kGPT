"""Sync and cleanup operations for database/Qdrant consistency."""

from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


@router.get("/status")
async def get_sync_status() -> dict:
    """
    Compare database sources with actual Qdrant vectors.

    Each source is stored in its own Qdrant collection (collection_name from DB).

    Returns information about:
    - Sources in DB that have no vectors in their Qdrant collection
    - Orphaned collections in Qdrant that aren't tracked in DB
    - Per-source status with vector counts
    """
    from kgpt.db import get_db
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    try:
        # Get sources from database
        db_sources = db.get_document_sources()

        # Map collection names to source info for lookup
        db_collections = {s["collection_name"]: s for s in db_sources}

        # Get all Qdrant collections
        qdrant_collections = set(store.list_collections())

        # Find discrepancies
        db_collection_names = set(db_collections.keys())
        orphaned_in_qdrant = qdrant_collections - db_collection_names  # In Qdrant but not DB
        missing_in_qdrant = []  # Sources in DB but their collection has no vectors

        # Build detailed source status by checking each source's collection
        source_status = []
        total_vectors = 0

        for source in db_sources:
            name = source["name"]
            collection_name = source["collection_name"]

            # Check if the collection exists and has vectors
            collection_exists = collection_name in qdrant_collections
            vector_count = 0

            if collection_exists:
                try:
                    info = store.get_collection_info(collection_name)
                    vector_count = info.get("points_count", 0) or info.get("vectors_count", 0)
                    total_vectors += vector_count
                except Exception:
                    pass

            in_qdrant = collection_exists and vector_count > 0

            if not in_qdrant and source["status"] == "indexed":
                missing_in_qdrant.append(name)

            source_status.append(
                {
                    "id": source["id"],
                    "name": name,
                    "collection_name": collection_name,
                    "db_status": source["status"],
                    "db_count": source["document_count"],
                    "qdrant_count": vector_count,
                    "in_qdrant": in_qdrant,
                    "synced": in_qdrant and source["status"] == "indexed",
                }
            )

        return {
            "synced": len(orphaned_in_qdrant) == 0 and len(missing_in_qdrant) == 0,
            "total_vectors": total_vectors,
            "db_sources_count": len(db_sources),
            "qdrant_collections_count": len(qdrant_collections),
            "orphaned_collections": list(orphaned_in_qdrant),
            "missing_sources": missing_in_qdrant,
            "source_status": source_status,
        }

    except Exception as e:
        logger.error(f"Error checking sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-orphans")
async def cleanup_orphan_vectors() -> dict:
    """
    Delete Qdrant collections that don't have a corresponding source in the database.

    This cleans up orphaned collections from partial ingestions or deleted sources.
    """
    from kgpt.db import get_db
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    try:
        # Get sources from database
        db_sources = db.get_document_sources()
        db_collection_names = {s["collection_name"] for s in db_sources}

        # Get all Qdrant collections
        qdrant_collections = set(store.list_collections())

        # Find orphans (collections in Qdrant but not tracked in DB)
        orphaned_collections = qdrant_collections - db_collection_names

        total_deleted = 0
        deleted_collections = []

        for collection_name in orphaned_collections:
            try:
                # Get vector count before deleting
                info = store.get_collection_info(collection_name)
                vector_count = info.get("points_count", 0) or info.get("vectors_count", 0)

                store.delete_collection(collection_name)
                total_deleted += vector_count
                deleted_collections.append(
                    {
                        "collection": collection_name,
                        "vectors_deleted": vector_count,
                    }
                )
                logger.info(
                    f"Cleaned up orphan collection '{collection_name}': {vector_count} vectors"
                )
            except Exception as e:
                logger.warning(f"Failed to clean up collection '{collection_name}': {e}")
                deleted_collections.append(
                    {
                        "collection": collection_name,
                        "error": str(e),
                    }
                )

        return {
            "status": "completed",
            "orphans_found": len(orphaned_collections),
            "total_vectors_deleted": total_deleted,
            "deleted_collections": deleted_collections,
        }

    except Exception as e:
        logger.error(f"Error cleaning up orphans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-stale")
async def cleanup_stale_db_entries() -> dict:
    """
    Remove database entries that have no corresponding vectors in their Qdrant collection.

    This cleans up DB entries from failed or cancelled ingestions.
    """
    from kgpt.db import get_db
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    try:
        # Get sources from database
        db_sources = db.get_document_sources()

        # Get all Qdrant collections
        qdrant_collections = set(store.list_collections())

        cleaned_entries = []

        for source in db_sources:
            name = source["name"]
            collection_name = source["collection_name"]

            # Check if collection exists and has vectors
            has_vectors = False
            if collection_name in qdrant_collections:
                try:
                    info = store.get_collection_info(collection_name)
                    vector_count = info.get("points_count", 0) or info.get("vectors_count", 0)
                    has_vectors = vector_count > 0
                except Exception:
                    pass

            # If source is "indexed" but no vectors, or is in error/cancelled state
            should_clean = (source["status"] == "indexed" and not has_vectors) or source[
                "status"
            ] in ["error", "cancelled"]

            if should_clean:
                try:
                    db.delete_document_source(source["id"])
                    cleaned_entries.append(
                        {
                            "id": source["id"],
                            "name": name,
                            "collection_name": collection_name,
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


@router.delete("/purge-all")
async def purge_all_data() -> dict:
    """
    DANGER: Delete ALL vectors and database entries.

    This is a nuclear option to start fresh.
    Deletes all source-specific collections and their corresponding DB entries.
    """
    from kgpt.db import get_db
    from kgpt.vectorstore import get_vectorstore

    db = get_db()
    store = get_vectorstore()

    try:
        # Get all DB sources
        db_sources = db.get_document_sources()

        # Get all Qdrant collections
        qdrant_collections = store.list_collections()

        total_vectors_deleted = 0
        collections_deleted = []

        # Delete all collections tracked by DB sources
        for source in db_sources:
            collection_name = source["collection_name"]
            try:
                info = store.get_collection_info(collection_name)
                vector_count = info.get("points_count", 0) or info.get("vectors_count", 0)
                store.delete_collection(collection_name)
                total_vectors_deleted += vector_count
                collections_deleted.append(collection_name)
            except Exception:
                pass
            db.delete_document_source(source["id"])

        # Also delete any orphaned collections not in DB
        db_collection_names = {s["collection_name"] for s in db_sources}
        for collection_name in qdrant_collections:
            if collection_name not in db_collection_names:
                try:
                    info = store.get_collection_info(collection_name)
                    vector_count = info.get("points_count", 0) or info.get("vectors_count", 0)
                    store.delete_collection(collection_name)
                    total_vectors_deleted += vector_count
                    collections_deleted.append(collection_name)
                except Exception:
                    pass

        return {
            "status": "purged",
            "db_entries_deleted": len(db_sources),
            "collections_deleted": len(collections_deleted),
            "vectors_deleted": total_vectors_deleted,
        }

    except Exception as e:
        logger.error(f"Error purging data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
