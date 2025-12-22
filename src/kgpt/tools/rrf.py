"""
Reciprocal Rank Fusion (RRF) for merging ranked results from multiple sources.

RRF is a well-established technique used by Elasticsearch, Google, and production
RAG systems to combine results from different retrieval methods (semantic search,
keyword search, web search) into a unified ranking.

Formula: score(d) = Σ 1 / (k + rank(d))
Where k is a constant (typically 60) that prevents high-ranking items from
dominating too heavily.
"""

from loguru import logger


def reciprocal_rank_fusion(
    *result_lists: list[dict],
    k: int = 60,
    score_key: str = "rrf_score",
    id_key: str = "url",
) -> list[dict]:
    """
    Merge multiple ranked result lists using Reciprocal Rank Fusion.

    Args:
        *result_lists: Variable number of ranked result lists (dicts with url/title/content)
        k: Constant to prevent high-ranking items from dominating (default 60)
        score_key: Key to store the computed RRF score in each result
        id_key: Key used to identify unique results (default "url")

    Returns:
        Merged and re-ranked list of results sorted by RRF score (highest first)

    Example:
        doc_results = [{"url": "a", "title": "Doc A"}, {"url": "b", "title": "Doc B"}]
        web_results = [{"url": "c", "title": "Web C"}, {"url": "a", "title": "Same as Doc A"}]
        merged = reciprocal_rank_fusion(doc_results, web_results)
        # Result: Doc A ranks highest since it appeared in both lists
    """
    # Track scores and source appearances for each unique result
    scores: dict[str, float] = {}
    results_by_id: dict[str, dict] = {}
    source_counts: dict[str, int] = {}

    for list_idx, result_list in enumerate(result_lists):
        if result_list is None or isinstance(result_list, Exception):
            logger.warning(f"Skipping result list {list_idx}: {result_list}")
            continue

        for rank, result in enumerate(result_list):
            # Get unique identifier for this result
            result_id = result.get(id_key) or result.get("title", f"unknown_{rank}")

            # Calculate RRF contribution from this list
            rrf_contribution = 1.0 / (k + rank + 1)  # +1 because rank is 0-indexed

            # Accumulate score
            if result_id in scores:
                scores[result_id] += rrf_contribution
                source_counts[result_id] = source_counts.get(result_id, 1) + 1
            else:
                scores[result_id] = rrf_contribution
                results_by_id[result_id] = result.copy()
                source_counts[result_id] = 1

    # Add RRF scores to results
    for result_id, result in results_by_id.items():
        result[score_key] = round(scores[result_id], 6)
        result["source_count"] = source_counts[result_id]

    # Sort by RRF score descending
    merged = sorted(results_by_id.values(), key=lambda x: x[score_key], reverse=True)

    logger.info(
        f"[RRF] Merged {sum(len(r) for r in result_lists if r and not isinstance(r, Exception))} "
        f"results from {len(result_lists)} sources into {len(merged)} unique results"
    )

    return merged
