"""Base document ingester class."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from kgpt.db import get_db
from kgpt.vectorstore import get_vectorstore


class DocumentIngester(ABC):
    """Abstract base class for document ingesters."""

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ):
        """Initialize the ingester."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    @abstractmethod
    def load_documents(self) -> list[Document]:
        """Load raw documents from the source."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get a human-readable name for this source."""
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        """Get the source type identifier."""
        pass

    def get_collection_name(self) -> str:
        """Get the collection name for this source."""
        # Default: use a sanitized version of the source name
        name = self.get_source_name().lower()
        return "".join(c if c.isalnum() else "_" for c in name)

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """Split documents into chunks."""
        return self.text_splitter.split_documents(documents)

    def ingest(
        self,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> int:
        """
        Ingest documents into the vector store.

        Args:
            progress_callback: Optional callback for progress updates (message, progress 0-1)

        Returns:
            Number of document chunks ingested
        """
        db = get_db()
        store = get_vectorstore()
        source_name = self.get_source_name()
        source_type = self.get_source_type()
        collection_name = self.get_collection_name()

        # Record source in database
        source_id = db.add_document_source(
            name=source_name,
            source_type=source_type,
            collection_name=collection_name,
            url=getattr(self, "url", None),
        )
        db.update_document_source(source_id, status="loading")

        try:
            # Load documents
            if progress_callback:
                progress_callback(f"Loading documents from {source_name}...", 0.1)

            logger.info(f"Loading documents from {source_name}")
            documents = self.load_documents()
            logger.info(f"Loaded {len(documents)} documents")

            if not documents:
                db.update_document_source(source_id, status="empty", document_count=0)
                return 0

            # Split documents
            if progress_callback:
                progress_callback("Splitting documents into chunks...", 0.3)

            logger.info("Splitting documents into chunks")
            chunks = self.split_documents(documents)
            logger.info(f"Created {len(chunks)} chunks")

            # Add metadata
            for chunk in chunks:
                chunk.metadata["source_name"] = source_name
                chunk.metadata["source_type"] = source_type
                chunk.metadata["ingested_at"] = datetime.now().isoformat()

            # Add to vector store
            if progress_callback:
                progress_callback("Adding to vector store...", 0.5)

            logger.info(f"Adding chunks to collection '{collection_name}'")
            store.add_documents(chunks, collection_name=collection_name)

            # Update database
            db.update_document_source(
                source_id,
                status="indexed",
                document_count=len(chunks),
                indexed_at=datetime.now(),
            )

            if progress_callback:
                progress_callback("Complete!", 1.0)

            logger.info(f"Successfully ingested {len(chunks)} chunks from {source_name}")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error ingesting from {source_name}: {e}")
            db.update_document_source(source_id, status="error")
            raise
