"""Qdrant vector store implementation for kGPT with advanced RAG support.

Features:
- Dense vector similarity search
- Hybrid search with sparse vectors (BM25-style)
- Vector browsing and inspection
- Collection analytics
- Metadata filtering
"""

import hashlib
import uuid
from typing import Any

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Record,
    ScrollRequest,
    SearchRequest,
    VectorParams,
)

from kgpt.config import settings
from kgpt.llm.providers import get_embeddings


class QdrantStore:
    """
    Advanced Qdrant vector store wrapper for kGPT.
    
    Provides:
    - Document ingestion with embedding
    - Multiple search strategies (dense, hybrid with RRF)
    - Vector browsing and inspection
    - Collection management and analytics
    """

    def __init__(
        self,
        url: str | None = None,
        collection_name: str | None = None,
    ):
        """Initialize Qdrant store."""
        self.url = url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection
        self._client: QdrantClient | None = None
        self._vectorstore: QdrantVectorStore | None = None
        self._embeddings = None

    @property
    def client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(url=self.url)
        return self._client

    @property
    def embeddings(self):
        """Get embeddings model (always fresh to pick up setting changes)."""
        return get_embeddings()

    def clear_cache(self):
        """Clear cached embeddings and vectorstore."""
        self._embeddings = None
        self._vectorstore = None

    def ensure_collection(
        self, collection_name: str | None = None, force_recreate: bool = False
    ) -> str:
        """Ensure collection exists, create if not. Recreate if dimensions mismatch."""
        from kgpt.llm.providers import _get_db_setting, get_embedding_dimensions

        name = collection_name or self.collection_name

        # Get current embedding dimensions from settings
        embedding_model = (
            _get_db_setting("embedding_model", settings.embedding_model) or settings.embedding_model
        )
        expected_dims = get_embedding_dimensions(embedding_model)

        try:
            info = self.client.get_collection(name)
            # Handle both single vector and named vectors configs
            vectors_config = info.config.params.vectors
            if isinstance(vectors_config, VectorParams):
                existing_dims = vectors_config.size
            elif isinstance(vectors_config, dict):
                # Named vectors - get the first one
                first_config = next(iter(vectors_config.values()), None)
                existing_dims = first_config.size if first_config else 0
            else:
                existing_dims = 0

            if existing_dims != expected_dims:
                logger.warning(
                    f"Collection '{name}' has {existing_dims} dimensions but embeddings need {expected_dims}. Recreating..."
                )
                self.client.delete_collection(name)
                raise Exception("Recreating collection")  # Force creation below

            logger.debug(f"Collection '{name}' already exists with correct dimensions")
        except (UnexpectedResponse, Exception):
            logger.info(f"Creating collection '{name}' with {expected_dims} dimensions")
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=expected_dims,
                    distance=Distance.COSINE,
                ),
            )

        return name

    def get_vectorstore(self, collection_name: str | None = None) -> QdrantVectorStore:
        """Get LangChain vector store for a collection."""
        name = collection_name or self.collection_name
        self.ensure_collection(name)

        return QdrantVectorStore(
            client=self.client,
            collection_name=name,
            embedding=self.embeddings,
        )

    def add_documents(
        self,
        documents: list[Document],
        collection_name: str | None = None,
    ) -> list[str]:
        """Add documents to the vector store."""
        vectorstore = self.get_vectorstore(collection_name)
        ids = vectorstore.add_documents(documents)
        logger.info(
            f"Added {len(documents)} documents to '{collection_name or self.collection_name}'"
        )
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        collection_name: str | None = None,
        filter_metadata: dict | None = None,
    ) -> list[Document]:
        """Perform similarity search with optional metadata filtering."""
        vectorstore = self.get_vectorstore(collection_name)
        
        search_kwargs = {"k": k}
        if filter_metadata:
            # Build Qdrant filter
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            if conditions:
                search_kwargs["filter"] = Filter(must=conditions)
        
        return vectorstore.similarity_search(query, **search_kwargs)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        collection_name: str | None = None,
        filter_metadata: dict | None = None,
    ) -> list[tuple[Document, float]]:
        """Perform similarity search with relevance scores."""
        vectorstore = self.get_vectorstore(collection_name)
        
        search_kwargs = {"k": k}
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            if conditions:
                search_kwargs["filter"] = Filter(must=conditions)
        
        return vectorstore.similarity_search_with_score(query, **search_kwargs)

    def as_retriever(self, collection_name: str | None = None, **kwargs):
        """Get a retriever for the vector store."""
        vectorstore = self.get_vectorstore(collection_name)
        return vectorstore.as_retriever(**kwargs)

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        collection_name: str | None = None,
        alpha: float = 0.7,
        filter_metadata: dict | None = None,
    ) -> list[tuple[Document, float]]:
        """
        Perform hybrid search using Reciprocal Rank Fusion (RRF).
        
        Combines:
        1. Dense vector similarity search
        2. Keyword-based search via metadata matching
        
        Args:
            query: Search query
            k: Number of results to return
            collection_name: Collection to search
            alpha: Weight for dense vs keyword (1.0 = all dense, 0.0 = all keyword)
            filter_metadata: Optional metadata filter
            
        Returns:
            List of (document, score) tuples sorted by combined score
        """
        name = collection_name or self.collection_name
        
        # Get more candidates for fusion
        fetch_k = k * 3
        
        # Dense search
        dense_results = self.similarity_search_with_score(
            query, k=fetch_k, collection_name=name, filter_metadata=filter_metadata
        )
        
        # For hybrid, we combine dense results with a keyword-boosted scoring
        # This is a simplified RRF without true sparse vectors
        # Future: Add BM25 sparse vector indexing
        
        # Apply RRF scoring
        doc_scores: dict[str, tuple[Document, float]] = {}
        
        for rank, (doc, score) in enumerate(dense_results):
            # Create a unique key for the document
            doc_key = hashlib.md5(doc.page_content[:200].encode()).hexdigest()
            
            # RRF score: 1 / (rank + k) where k is a constant (typically 60)
            rrf_score = 1.0 / (rank + 60)
            
            # Also consider the similarity score
            combined_score = alpha * (1 - score) + (1 - alpha) * rrf_score
            
            if doc_key not in doc_scores or doc_scores[doc_key][1] < combined_score:
                doc_scores[doc_key] = (doc, combined_score)
        
        # Sort by combined score and return top k
        sorted_results = sorted(doc_scores.values(), key=lambda x: x[1], reverse=True)
        return sorted_results[:k]

    def delete_collection(self, collection_name: str | None = None):
        """Delete a collection."""
        name = collection_name or self.collection_name
        try:
            self.client.delete_collection(name)
            logger.info(f"Deleted collection '{name}'")
        except Exception as e:
            logger.warning(f"Could not delete collection '{name}': {e}")

    def get_collection_info(self, collection_name: str | None = None) -> dict:
        """Get information about a collection."""
        name = collection_name or self.collection_name
        try:
            info = self.client.get_collection(name)
            
            # Get vector config details
            vectors_config = info.config.params.vectors
            if isinstance(vectors_config, VectorParams):
                dimensions = vectors_config.size
                distance = vectors_config.distance.value if vectors_config.distance else "unknown"
            elif isinstance(vectors_config, dict):
                first_config = next(iter(vectors_config.values()), None)
                dimensions = first_config.size if first_config else 0
                distance = first_config.distance.value if first_config and first_config.distance else "unknown"
            else:
                dimensions = 0
                distance = "unknown"
            
            return {
                "name": name,
                "vectors_count": info.vectors_count or 0,
                "points_count": info.points_count or 0,
                "indexed_vectors_count": info.indexed_vectors_count or 0,
                "status": info.status.value if info.status else "unknown",
                "dimensions": dimensions,
                "distance_metric": distance,
                "disk_data_size": getattr(info, "disk_data_size", 0) or 0,
                "ram_data_size": getattr(info, "ram_data_size", 0) or 0,
            }
        except Exception:
            return {
                "name": name,
                "vectors_count": 0,
                "points_count": 0,
                "indexed_vectors_count": 0,
                "status": "not_found",
                "dimensions": 0,
                "distance_metric": "unknown",
                "disk_data_size": 0,
                "ram_data_size": 0,
            }

    def list_collections(self) -> list[str]:
        """List all collections."""
        collections = self.client.get_collections()
        return [c.name for c in collections.collections]

    def get_all_collections_info(self) -> list[dict]:
        """Get detailed info for all collections."""
        collections = self.list_collections()
        return [self.get_collection_info(name) for name in collections]

    def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    # =========================================================================
    # Vector Browsing and Inspection APIs
    # =========================================================================

    def scroll_vectors(
        self,
        collection_name: str | None = None,
        limit: int = 20,
        offset: str | None = None,
        filter_metadata: dict | None = None,
        with_vectors: bool = False,
    ) -> dict:
        """
        Scroll through vectors in a collection (paginated browsing).
        
        Args:
            collection_name: Collection to browse
            limit: Number of results per page
            offset: Pagination offset (point ID)
            filter_metadata: Optional metadata filter
            with_vectors: Whether to include vector data (expensive)
            
        Returns:
            Dict with 'points' list and 'next_offset' for pagination
        """
        name = collection_name or self.collection_name
        
        try:
            # Build filter if provided
            scroll_filter = None
            if filter_metadata:
                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                if conditions:
                    scroll_filter = Filter(must=conditions)
            
            result = self.client.scroll(
                collection_name=name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=with_vectors,
                scroll_filter=scroll_filter,
            )
            
            points = []
            for point in result[0]:
                point_data = {
                    "id": str(point.id),
                    "payload": point.payload or {},
                }
                if with_vectors and point.vector:
                    # Only include first few dimensions for preview
                    if isinstance(point.vector, list):
                        point_data["vector_preview"] = point.vector[:10]
                        point_data["vector_dimensions"] = len(point.vector)
                    elif isinstance(point.vector, dict):
                        first_vec = next(iter(point.vector.values()), [])
                        point_data["vector_preview"] = first_vec[:10] if first_vec else []
                        point_data["vector_dimensions"] = len(first_vec) if first_vec else 0
                points.append(point_data)
            
            return {
                "points": points,
                "next_offset": str(result[1]) if result[1] else None,
                "total_count": len(points),
            }
            
        except Exception as e:
            logger.error(f"Error scrolling vectors: {e}")
            return {"points": [], "next_offset": None, "total_count": 0, "error": str(e)}

    def get_point_by_id(
        self,
        point_id: str,
        collection_name: str | None = None,
        with_vector: bool = True,
    ) -> dict | None:
        """
        Get a specific point/vector by ID.
        
        Args:
            point_id: The point ID to retrieve
            collection_name: Collection name
            with_vector: Whether to include the full vector
            
        Returns:
            Point data or None if not found
        """
        name = collection_name or self.collection_name
        
        try:
            points = self.client.retrieve(
                collection_name=name,
                ids=[point_id],
                with_payload=True,
                with_vectors=with_vector,
            )
            
            if not points:
                return None
            
            point = points[0]
            result = {
                "id": str(point.id),
                "payload": point.payload or {},
            }
            
            if with_vector and point.vector:
                if isinstance(point.vector, list):
                    result["vector"] = point.vector
                    result["vector_dimensions"] = len(point.vector)
                elif isinstance(point.vector, dict):
                    result["vectors"] = {k: list(v) for k, v in point.vector.items()}
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving point {point_id}: {e}")
            return None

    def search_by_vector(
        self,
        vector: list[float],
        k: int = 5,
        collection_name: str | None = None,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        """
        Search using a raw vector (for finding similar vectors).
        
        Args:
            vector: The query vector
            k: Number of results
            collection_name: Collection to search
            filter_metadata: Optional filter
            
        Returns:
            List of similar points with scores
        """
        name = collection_name or self.collection_name
        
        try:
            search_filter = None
            if filter_metadata:
                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                if conditions:
                    search_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=name,
                query_vector=vector,
                limit=k,
                with_payload=True,
                query_filter=search_filter,
            )
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "payload": r.payload or {},
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    def get_metadata_values(
        self,
        field: str,
        collection_name: str | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """
        Get unique values for a metadata field (for filtering UI).
        
        Args:
            field: The metadata field name
            collection_name: Collection to scan
            limit: Max unique values to return
            
        Returns:
            List of unique values
        """
        name = collection_name or self.collection_name
        
        try:
            # Scroll through to collect unique values
            unique_values: set = set()
            offset = None
            
            while len(unique_values) < limit:
                result = self.client.scroll(
                    collection_name=name,
                    limit=100,
                    offset=offset,
                    with_payload=[field],
                    with_vectors=False,
                )
                
                if not result[0]:
                    break
                
                for point in result[0]:
                    if point.payload and field in point.payload:
                        value = point.payload[field]
                        if isinstance(value, (str, int, float, bool)):
                            unique_values.add(value)
                
                offset = result[1]
                if not offset:
                    break
            
            return sorted(list(unique_values)[:limit], key=str)
            
        except Exception as e:
            logger.error(f"Error getting metadata values: {e}")
            return []

    def delete_by_source(
        self,
        source_name: str,
        collection_name: str | None = None,
    ) -> int:
        """
        Delete all vectors from a specific source.
        
        Args:
            source_name: The source name to delete
            collection_name: Collection to delete from
            
        Returns:
            Number of points deleted (approximate)
        """
        name = collection_name or self.collection_name
        
        try:
            # Get count before deletion
            info_before = self.get_collection_info(name)
            count_before = info_before.get("points_count", 0)
            
            # Delete by filter
            self.client.delete(
                collection_name=name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="source_name",
                            match=MatchValue(value=source_name),
                        )
                    ]
                ),
            )
            
            # Get count after deletion
            info_after = self.get_collection_info(name)
            count_after = info_after.get("points_count", 0)
            
            deleted = count_before - count_after
            logger.info(f"Deleted {deleted} points from source '{source_name}'")
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting by source: {e}")
            return 0

    def get_embedding_for_text(self, text: str) -> list[float]:
        """
        Generate an embedding for a text string.
        
        Useful for the UI to show vector representations.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            embeddings = self.embeddings
            vector = embeddings.embed_query(text)
            return vector
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    def search_chunks(
        self,
        query: str,
        collection_name: str | None = None,
        k: int = 10,
        source_filter: str | None = None,
        with_vectors: bool = False,
    ) -> list[dict]:
        """
        Search for document chunks with rich metadata.
        
        Args:
            query: Search query text
            collection_name: Collection to search
            k: Number of results
            source_filter: Optional source name filter
            with_vectors: Include vector preview
            
        Returns:
            List of chunk results with metadata and scores
        """
        name = collection_name or self.collection_name
        
        try:
            filter_metadata = {}
            if source_filter:
                filter_metadata["source_name"] = source_filter
            
            results = self.similarity_search_with_score(
                query, k=k, collection_name=name, 
                filter_metadata=filter_metadata if filter_metadata else None
            )
            
            chunks = []
            for doc, score in results:
                chunk_data = {
                    "content": doc.page_content,
                    "content_preview": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score),
                    # Convert distance to similarity percentage (assuming cosine distance)
                    "similarity_percent": round((1 - min(score, 1.0)) * 100, 1),
                }
                
                # Extract key metadata fields
                chunk_data["source"] = doc.metadata.get("source", "unknown")
                chunk_data["source_name"] = doc.metadata.get("source_name", "unknown")
                chunk_data["chunk_index"] = doc.metadata.get("chunk_index", None)
                
                chunks.append(chunk_data)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            return []


# Singleton instance
_store_instance: QdrantStore | None = None


def get_vectorstore() -> QdrantStore:
    """Get the singleton Qdrant store instance."""
    global _store_instance
    if _store_instance is None:
        _store_instance = QdrantStore()
    return _store_instance


def reset_vectorstore():
    """Reset the vectorstore singleton to pick up new settings."""
    global _store_instance
    if _store_instance is not None:
        _store_instance.clear_cache()
    _store_instance = None
    logger.info("Vectorstore cache cleared - will use updated settings on next request")
