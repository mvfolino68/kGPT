"""Document ingestion module for kGPT."""

from kgpt.ingestion.base import DocumentIngester
from kgpt.ingestion.custom import CustomIngester
from kgpt.ingestion.github import GitHubIngester
from kgpt.ingestion.preprocessing import (
    TextPreprocessor,
    get_text_quality_score,
    preprocess_for_rag,
)
from kgpt.ingestion.sitemap import SitemapIngester
from kgpt.ingestion.smart_naming import (
    generate_smart_name,
    generate_smart_name_sync,
    sanitize_collection_name,
    suggest_names_for_url,
)

__all__ = [
    "DocumentIngester",
    "SitemapIngester",
    "GitHubIngester",
    "CustomIngester",
    "TextPreprocessor",
    "preprocess_for_rag",
    "get_text_quality_score",
    "generate_smart_name",
    "generate_smart_name_sync",
    "suggest_names_for_url",
    "sanitize_collection_name",
]
