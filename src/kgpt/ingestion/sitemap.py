"""Sitemap-based document ingester with parallel fetching and improved HTML processing."""

import asyncio
from collections.abc import Callable
from urllib.parse import urlparse
from xml.etree import ElementTree

import aiohttp
from langchain_core.documents import Document
from loguru import logger

from kgpt.ingestion.base import DocumentIngester
from kgpt.ingestion.preprocessing import preprocess_for_rag

# Predefined documentation sources
PRESET_SITEMAPS = {
    "confluent": {
        "url": "https://docs.confluent.io/home/sitemap.xml",
        "name": "Confluent Documentation",
        "filter_urls": None,
    },
    "kafka": {
        "url": "https://kafka.apache.org/sitemap.xml",
        "name": "Apache Kafka Documentation",
        "filter_urls": None,
    },
}

# XML namespaces for sitemaps
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class SitemapIngester(DocumentIngester):
    """Ingest documents from a sitemap URL with parallel fetching."""

    def __init__(
        self,
        url: str,
        name: str | None = None,
        filter_urls: list[str] | None = None,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
        max_concurrent: int = 20,
        max_pages: int | None = None,
        progress_callback: Callable | None = None,
    ):
        """
        Initialize sitemap ingester.

        Args:
            url: Sitemap URL
            name: Human-readable name for this source
            filter_urls: Optional list of URL patterns to include
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            max_concurrent: Maximum concurrent HTTP requests
            max_pages: Maximum number of pages to fetch (None for all)
            progress_callback: Optional callback(stage, progress, message) for status updates
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.url = url
        self._name = name
        self.filter_urls = filter_urls
        self.max_concurrent = max_concurrent
        self.max_pages = max_pages
        self._markitdown = None
        self._progress_callback = progress_callback
        self._fetched_count = 0
        self._total_urls = 0

    def _report_progress(self, stage: str, progress: int, message: str, **extra):
        """Report progress via callback if available."""
        if self._progress_callback:
            self._progress_callback(stage, progress, message, **extra)
        logger.info(f"[{stage}] {message}")

    @classmethod
    def from_preset(cls, preset_name: str, **kwargs) -> "SitemapIngester":
        """Create a SitemapIngester from a preset configuration."""
        if preset_name not in PRESET_SITEMAPS:
            raise ValueError(
                f"Unknown preset: {preset_name}. Available: {list(PRESET_SITEMAPS.keys())}"
            )

        preset = PRESET_SITEMAPS[preset_name]
        return cls(
            url=preset["url"],
            name=preset["name"],
            filter_urls=preset.get("filter_urls"),
            **kwargs,
        )

    def get_source_name(self) -> str:
        """Get source name."""
        if self._name:
            return self._name
        parsed = urlparse(self.url)
        return parsed.netloc

    def get_source_type(self) -> str:
        """Get source type."""
        return "sitemap"

    def get_collection_name(self) -> str:
        """Get collection name based on the domain."""
        parsed = urlparse(self.url)
        domain = parsed.netloc.replace(".", "_").replace("-", "_")
        return f"sitemap_{domain}"

    def _get_markitdown(self):
        """Lazy load MarkItDown converter."""
        if self._markitdown is None:
            try:
                from markitdown import MarkItDown

                self._markitdown = MarkItDown()
                logger.info("Using MarkItDown for HTML→Markdown conversion")
            except ImportError:
                logger.warning("MarkItDown not installed, falling back to BeautifulSoup")
                self._markitdown = False
        return self._markitdown

    def _parse_html_to_text(self, html: str, url: str) -> str:
        """Convert HTML to clean text optimized for embeddings."""
        converter = self._get_markitdown()
        raw_text = ""

        if converter:
            try:
                # MarkItDown produces LLM-optimized markdown
                import os
                import tempfile

                # MarkItDown needs a file, so write temporarily
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".html", delete=False, encoding="utf-8"
                ) as f:
                    f.write(html)
                    temp_path = f.name

                try:
                    result = converter.convert(temp_path)
                    raw_text = result.text_content.strip()
                finally:
                    os.unlink(temp_path)
            except Exception as e:
                logger.debug(f"MarkItDown failed for {url}: {e}, falling back to BeautifulSoup")
                raw_text = self._parse_with_beautifulsoup(html)
        else:
            # Fallback to BeautifulSoup
            raw_text = self._parse_with_beautifulsoup(html)

        # Apply RAG preprocessing for cleaner embeddings
        cleaned = preprocess_for_rag(
            raw_text,
            clean_boilerplate=True,
            clean_markdown=True,
            remove_code=False,  # Keep code - it can be valuable
            normalize_embedding=False,  # Don't lowercase - keep readability
        )

        return cleaned

    def _parse_with_beautifulsoup(self, html: str) -> str:
        """Fallback parser using BeautifulSoup."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # Remove non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            element.decompose()

        # Try to find main content area
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find(class_=["content", "main-content", "documentation", "docs"])
            or soup.find(id=["content", "main-content", "documentation"])
            or soup.body
            or soup
        )

        text = main_content.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    async def _fetch_url(
        self,
        session: aiohttp.ClientSession,
        url: str,
        semaphore: asyncio.Semaphore,
    ) -> tuple[str, str | None]:
        """Fetch a single URL with rate limiting."""
        async with semaphore:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        html = await response.text()
                        return (url, html)
                    else:
                        logger.debug(f"HTTP {response.status} for {url}")
                        return (url, None)
            except Exception as e:
                logger.debug(f"Failed to fetch {url}: {e}")
                return (url, None)

    async def _fetch_all_urls(self, urls: list[str]) -> list[tuple[str, str]]:
        """Fetch all URLs in parallel with rate limiting."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        headers = {
            "User-Agent": "kGPT/2.0 Documentation Indexer (https://github.com/your-repo/kgpt)"
        }

        connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=10)
        self._total_urls = len(urls)
        self._fetched_count = 0

        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            tasks = [self._fetch_url(session, url, semaphore) for url in urls]

            results = []
            # Process in batches to show progress
            batch_size = 20
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i : i + batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)

                for result in batch_results:
                    if isinstance(result, tuple) and result[1] is not None:
                        results.append(result)

                self._fetched_count = min(i + batch_size, len(tasks))
                progress = int(15 + (self._fetched_count / len(tasks)) * 25)  # 15-40%
                self._report_progress(
                    "fetching",
                    progress,
                    f"Fetched {self._fetched_count}/{len(tasks)} pages ({len(results)} successful)",
                    pages_fetched=self._fetched_count,
                    pages_total=len(tasks),
                    pages_successful=len(results),
                )

        return results

    def _extract_urls_from_sitemap(self, xml_content: str) -> list[str]:
        """Extract URLs from sitemap XML."""
        urls = []
        try:
            root = ElementTree.fromstring(xml_content)

            # Check if this is a sitemap index
            sitemaps = root.findall(".//sm:sitemap/sm:loc", SITEMAP_NS)
            if sitemaps:
                # It's a sitemap index - we'd need to fetch nested sitemaps
                # For now, just extract URLs from this level
                logger.info(f"Found sitemap index with {len(sitemaps)} nested sitemaps")

            # Extract regular URLs
            locs = root.findall(".//sm:url/sm:loc", SITEMAP_NS)
            if not locs:
                # Try without namespace (some sitemaps don't use it)
                locs = root.findall(".//url/loc")

            for loc in locs:
                if loc.text:
                    url = loc.text.strip()
                    # Apply URL filters if specified
                    if self.filter_urls:
                        if any(pattern in url for pattern in self.filter_urls):
                            urls.append(url)
                    else:
                        urls.append(url)

        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse sitemap XML: {e}")

        return urls

    def load_documents(self) -> list[Document]:
        """Load documents from the sitemap using parallel fetching."""
        self._report_progress("starting", 5, f"Loading sitemap from {self.url}")

        # Fetch the sitemap XML
        import requests

        headers = {
            "User-Agent": "kGPT/2.0 Documentation Indexer (https://github.com/your-repo/kgpt)"
        }
        response = requests.get(self.url, timeout=30, headers=headers)
        response.raise_for_status()
        self._report_progress("parsing", 10, f"Sitemap fetched ({len(response.content)} bytes)")

        # Extract URLs
        urls = self._extract_urls_from_sitemap(response.text)
        self._report_progress("parsing", 12, f"Found {len(urls)} URLs in sitemap")

        if not urls:
            logger.warning("No URLs found in sitemap")
            return []

        # Limit pages if specified
        if self.max_pages and len(urls) > self.max_pages:
            self._report_progress("parsing", 14, f"Limiting to first {self.max_pages} pages")
            urls = urls[: self.max_pages]

        # Fetch all pages in parallel
        self._report_progress(
            "fetching",
            15,
            f"Fetching {len(urls)} pages in parallel (max {self.max_concurrent} concurrent)...",
            pages_total=len(urls),
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            fetched = loop.run_until_complete(self._fetch_all_urls(urls))
        finally:
            loop.close()

        self._report_progress(
            "processing",
            42,
            f"Processing {len(fetched)} fetched pages...",
            pages_fetched=len(fetched),
        )

        # Convert HTML to text and create documents
        documents = []
        total = len(fetched)
        for idx, (url, html) in enumerate(fetched):
            try:
                text = self._parse_html_to_text(html, url)
                if text and len(text) > 100:  # Skip very short pages
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": url,
                            "source_type": "sitemap",
                            "source_name": self.get_source_name(),
                        },
                    )
                    documents.append(doc)
            except Exception as e:
                logger.debug(f"Failed to parse {url}: {e}")

            # Report progress every 10 documents
            if (idx + 1) % 10 == 0 or idx == total - 1:
                progress = int(42 + ((idx + 1) / total) * 8)  # 42-50%
                self._report_progress(
                    "processing",
                    progress,
                    f"Processed {idx + 1}/{total} pages ({len(documents)} documents created)",
                    pages_processed=idx + 1,
                    documents_created=len(documents),
                )

        self._report_progress(
            "loaded", 50, f"Created {len(documents)} documents from {len(fetched)} pages"
        )
        return documents
