"""Document ingestion module for kGPT."""

from kgpt.ingestion.base import DocumentIngester
from kgpt.ingestion.custom import CustomIngester
from kgpt.ingestion.github import GitHubIngester
from kgpt.ingestion.sitemap import SitemapIngester

__all__ = ["DocumentIngester", "SitemapIngester", "GitHubIngester", "CustomIngester"]
