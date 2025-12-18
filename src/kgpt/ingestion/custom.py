"""Custom document ingester for URLs and file uploads."""

import io
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse

import httpx
from langchain_core.documents import Document
from loguru import logger

from kgpt.ingestion.base import DocumentIngester


class CustomIngester(DocumentIngester):
    """Ingest documents from custom URLs or file uploads."""

    def __init__(
        self,
        source: str | Path | BinaryIO,
        name: str | None = None,
        source_type: str | None = None,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ):
        """
        Initialize custom ingester.

        Args:
            source: URL string, file path, or file-like object
            name: Human-readable name for this source
            source_type: Type of source (url, file, pdf)
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.source = source
        self._name = name
        self._source_type = source_type
        self._detected_type = self._detect_source_type()

    def _detect_source_type(self) -> str:
        """Detect the type of source."""
        if self._source_type:
            return self._source_type

        if isinstance(self.source, str):
            if self.source.startswith(("http://", "https://")):
                return "url"
            path = Path(self.source)
            if path.suffix.lower() == ".pdf":
                return "pdf"
            return "file"
        elif isinstance(self.source, Path):
            if self.source.suffix.lower() == ".pdf":
                return "pdf"
            return "file"
        else:
            # File-like object
            return "upload"

    def get_source_name(self) -> str:
        """Get source name."""
        if self._name:
            return self._name

        if isinstance(self.source, str):
            if self._detected_type == "url":
                parsed = urlparse(self.source)
                return parsed.netloc
            return Path(self.source).stem
        elif isinstance(self.source, Path):
            return self.source.stem
        else:
            return "uploaded_file"

    def get_source_type(self) -> str:
        """Get source type."""
        return self._detected_type

    def get_collection_name(self) -> str:
        """Get collection name."""
        name = self.get_source_name().lower()
        sanitized = "".join(c if c.isalnum() else "_" for c in name)
        return f"custom_{sanitized}"

    def load_documents(self) -> list[Document]:
        """Load documents from the source."""
        if self._detected_type == "url":
            return self._load_from_url()
        elif self._detected_type == "pdf":
            return self._load_pdf()
        else:
            return self._load_file()

    def _load_from_url(self) -> list[Document]:
        """Load document from a URL."""
        from bs4 import BeautifulSoup

        logger.info(f"Fetching content from {self.source}")

        try:
            response = httpx.get(str(self.source), follow_redirects=True, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            if "text/html" in content_type:
                # Parse HTML
                soup = BeautifulSoup(response.text, "lxml")
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.decompose()
                text = soup.get_text(separator="\n", strip=True)
            else:
                # Plain text
                text = response.text

            doc = Document(
                page_content=text,
                metadata={
                    "source": str(self.source),
                    "content_type": content_type,
                },
            )
            return [doc]

        except Exception as e:
            logger.error(f"Error fetching URL: {e}")
            raise

    def _load_pdf(self) -> list[Document]:
        """Load document from a PDF file."""
        from pypdf import PdfReader

        logger.info(f"Loading PDF from {self.source}")

        try:
            if isinstance(self.source, (str, Path)):
                reader = PdfReader(str(self.source))
            else:
                reader = PdfReader(self.source)

            documents = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": str(self.source)
                            if isinstance(self.source, (str, Path))
                            else "uploaded_pdf",
                            "page": i + 1,
                        },
                    )
                    documents.append(doc)

            logger.info(f"Loaded {len(documents)} pages from PDF")
            return documents

        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            raise

    def _load_file(self) -> list[Document]:
        """Load document from a text file."""
        logger.info(f"Loading file from {self.source}")

        try:
            if isinstance(self.source, (str, Path)):
                content = Path(self.source).read_text(encoding="utf-8", errors="ignore")
            elif hasattr(self.source, "read"):
                content = self.source.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="ignore")
            else:
                raise ValueError(f"Unsupported source type: {type(self.source)}")

            doc = Document(
                page_content=content,
                metadata={
                    "source": str(self.source)
                    if isinstance(self.source, (str, Path))
                    else "uploaded_file",
                },
            )
            return [doc]

        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise


class FileUploadIngester(CustomIngester):
    """Convenience class for handling Streamlit file uploads."""

    def __init__(
        self,
        uploaded_file,  # Streamlit UploadedFile
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ):
        """
        Initialize from a Streamlit uploaded file.

        Args:
            uploaded_file: Streamlit UploadedFile object
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        # Determine source type from filename
        filename = uploaded_file.name
        source_type = None
        if filename.lower().endswith(".pdf"):
            source_type = "pdf"

        # Read content into BytesIO
        content = io.BytesIO(uploaded_file.read())

        super().__init__(
            source=content,
            name=Path(filename).stem,
            source_type=source_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.filename = filename

    def get_collection_name(self) -> str:
        """Get collection name based on filename."""
        name = Path(self.filename).stem.lower()
        sanitized = "".join(c if c.isalnum() else "_" for c in name)
        return f"upload_{sanitized}"
