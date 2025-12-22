"""
Reranking module for retrieval.

This module isolates the heavy reranking logic (Cohere/Cross-Encoder)
from the main retrieval orchestration.
"""

from langchain_core.documents import Document
from loguru import logger

# Minimum rerank score threshold - documents below this are filtered out
# Cohere rerank scores: 0.0 = irrelevant, 1.0 = highly relevant
# Using 0.01 as a very low threshold - primary filtering is via top_k ranking
# The reranker's main job is ordering, not filtering
MIN_RERANK_SCORE_COHERE = 0.01

# Minimum number of documents to keep even if below threshold
# This ensures we always have some context for synthesis
MIN_DOCS_TO_KEEP = 3

# Cross-encoder scores are different and can be very low/negative
# Using a more permissive threshold to avoid empty results
MIN_RERANK_SCORE_CROSS_ENCODER = -1.0


def create_rerank_query(original_query: str, enhanced_query: str) -> str:
    """
    Create an optimized query for Cohere reranking.

    Cohere reranker needs domain context to score Kafka documents correctly.
    For example, "what is kraft" scores 0.001 but "What is KRaft in Apache Kafka?"
    scores 1.0 for the same Kafka documentation.

    Args:
        original_query: The user's original question
        enhanced_query: The domain-enhanced query (kraft -> KRaft)

    Returns:
        Query optimized for Cohere reranking with Kafka context
    """
    # Truncate query for reranking to avoid model confusion and truncation
    # Cross-encoders perform best with concise queries
    if len(enhanced_query) > 300:
        enhanced_query = enhanced_query[:300].rsplit(" ", 1)[0] + "..."

    # If query already has Kafka context, use it as is
    query_lower = enhanced_query.lower()
    if "kafka" in query_lower or "confluent" in query_lower or "kraft" in query_lower:
        return enhanced_query

    # Add Kafka context for reranking
    return f"{enhanced_query} in Apache Kafka"


async def rerank_documents(
    query: str,
    documents: list[Document],
    top_k: int = 10,
    min_score_threshold: float | None = None,
) -> list[Document]:
    """
    Rerank documents using Cohere's reranker or a cross-encoder fallback.

    Reranking significantly improves retrieval quality by using a more
    sophisticated model to score query-document relevance. Documents below
    the minimum relevance threshold are filtered out.

    Args:
        query: The original user query
        documents: List of candidate documents
        top_k: Number of documents to return after reranking
        min_score_threshold: Optional override for minimum score filtering

    Returns:
        Reranked list of documents (best first), filtered by relevance
    """
    if not documents:
        return []

    # Try Cohere reranking first (best quality)
    try:
        from kgpt.db import get_db

        db = get_db()
        cohere_key = db.get_setting("cohere_api_key")

        if cohere_key:
            import cohere

            co = cohere.Client(cohere_key)

            # Prepare documents for reranking
            doc_texts = [doc.page_content for doc in documents]

            # Rerank using Cohere
            rerank_response = co.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=doc_texts,
                top_n=min(top_k * 2, len(documents)),  # Get more for filtering
                return_documents=False,
            )

            # Apply minimum score threshold
            threshold = (
                min_score_threshold if min_score_threshold is not None else MIN_RERANK_SCORE_COHERE
            )

            # Reorder and filter documents based on reranking
            reranked_docs = []
            all_scored_docs = []
            filtered_count = 0
            scores_preview = []

            for result in rerank_response.results:
                doc = documents[result.index]
                score = float(result.relevance_score)
                doc.metadata["rerank_score"] = score
                doc.metadata["reranking_model"] = "cohere-rerank-v3"
                scores_preview.append(f"{score:.3f}")
                all_scored_docs.append((doc, score))

                # Filter by threshold
                if score >= threshold:
                    reranked_docs.append(doc)
                else:
                    filtered_count += 1

            # Ensure we keep at least MIN_DOCS_TO_KEEP even if below threshold
            # This prevents returning empty results when scores are low
            if len(reranked_docs) < MIN_DOCS_TO_KEEP and len(all_scored_docs) > len(reranked_docs):
                # Add more docs from the scored list (they're already sorted by score)
                for doc, _ in all_scored_docs:
                    if doc not in reranked_docs:
                        reranked_docs.append(doc)
                        if len(reranked_docs) >= MIN_DOCS_TO_KEEP:
                            break

            # Limit to top_k after filtering
            reranked_docs = reranked_docs[:top_k]

            logger.info(
                f"Reranked docs using Cohere. "
                f"Scores: [{', '.join(scores_preview[:5])}], "
                f"kept {len(reranked_docs)}, filtered {filtered_count} below {threshold:.2f}"
            )
            return reranked_docs

    except ImportError:
        logger.debug("Cohere not installed, using fallback reranking")
    except Exception as e:
        logger.warning(f"Cohere reranking failed: {e}, using fallback")

    # Fallback: Use cross-encoder reranking with sentence-transformers
    try:
        from sentence_transformers import CrossEncoder

        # Use a lightweight cross-encoder model
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)

        # Score each document
        pairs = [[query, doc.page_content[:1000]] for doc in documents]
        scores = model.predict(pairs)

        # Apply minimum score threshold
        threshold = (
            min_score_threshold
            if min_score_threshold is not None
            else MIN_RERANK_SCORE_CROSS_ENCODER
        )

        # Reorder and filter documents based on reranking
        scored_docs = sorted(zip(documents, scores, strict=False), key=lambda x: x[1], reverse=True)

        reranked_docs = []
        all_scored_docs = []
        filtered_count = 0
        scores_preview = []

        for doc, score_val in scored_docs:
            score_float = float(score_val)
            doc.metadata["rerank_score"] = score_float
            doc.metadata["reranking_model"] = "ms-marco-MiniLM"
            scores_preview.append(f"{score_float:.2f}")
            all_scored_docs.append((doc, score_float))

            if score_float >= threshold:
                reranked_docs.append(doc)
            else:
                filtered_count += 1

        # Ensure we keep at least MIN_DOCS_TO_KEEP even if below threshold
        # This prevents returning empty results when scores are low
        if len(reranked_docs) < MIN_DOCS_TO_KEEP and len(all_scored_docs) > len(reranked_docs):
            for doc, _ in all_scored_docs:
                if doc not in reranked_docs:
                    reranked_docs.append(doc)
                    if len(reranked_docs) >= MIN_DOCS_TO_KEEP:
                        break

        # Limit to top_k
        reranked_docs = reranked_docs[:top_k]

        logger.info(
            f"Reranked {len(reranked_docs)} docs using cross-encoder. "
            f"Scores: [{', '.join(scores_preview[:5])}], "
            f"filtered {filtered_count} below {threshold:.1f}"
        )
        return reranked_docs

    except ImportError:
        logger.debug("sentence-transformers not installed, skipping reranking")
    except Exception as e:
        logger.warning(f"Cross-encoder reranking failed: {e}")

    # Final fallback: Return documents sorted by original similarity score
    logger.info("Using similarity scores for ranking (no reranking model available)")
    sorted_docs = sorted(
        documents,
        key=lambda d: d.metadata.get("relevance_score", 0),
        reverse=True,
    )
    return sorted_docs[:top_k]
