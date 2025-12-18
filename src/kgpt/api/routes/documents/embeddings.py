"""Embedding generation and comparison endpoints for educational purposes."""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class EmbeddingRequest(BaseModel):
    """Request to generate an embedding."""

    text: str = Field(..., min_length=1, max_length=10000)


class EmbeddingResponse(BaseModel):
    """Response with embedding vector."""

    text: str
    vector: list[float]
    dimensions: int
    model: str


# ============================================================================
# Embedding Endpoints
# ============================================================================


@router.post("/generate", response_model=EmbeddingResponse)
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


@router.post("/compare")
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
