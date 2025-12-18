"""Analytics endpoints for chunk and search quality analysis."""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger


router = APIRouter()


@router.get("/chunks")
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


@router.get("/search-quality")
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
