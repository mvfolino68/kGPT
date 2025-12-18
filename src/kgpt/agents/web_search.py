"""Web search agent using Exa for real-time information retrieval."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from kgpt.config import settings


def _get_exa_api_key() -> str | None:
    """Get Exa API key from DB or environment."""
    try:
        from kgpt.db import get_db

        db = get_db()
        key = db.get_setting("exa_api_key")
        if key:
            return key
    except Exception:
        pass
    return settings.exa_api_key


def is_web_search_enabled() -> bool:
    """Check if web search is enabled and configured."""
    try:
        from kgpt.db import get_db

        db = get_db()
        enabled = db.get_setting("web_search_enabled")
        if enabled is not None:
            return enabled.lower() == "true"
    except Exception:
        pass
    return settings.web_search_enabled and _get_exa_api_key() is not None


def _web_search_sync(query: str, api_key: str, num_results: int = 5) -> list[dict]:
    """
    Synchronous web search function (runs in thread pool).

    Args:
        query: The search query
        api_key: Exa API key
        num_results: Number of results to return

    Returns:
        List of search results with title, url, content, and highlights
    """
    try:
        from exa_py import Exa

        exa = Exa(api_key=api_key)
        logger.info(f"Performing web search: {query[:100]}...")

        # Use the new search() API (search_and_contents is deprecated)
        # Request text content - highlights may be included automatically
        response = exa.search(
            query,
            num_results=num_results,
            contents={"text": {"maxCharacters": 2000}},
        )

        results = []
        for r in response.results:
            # Extract highlights - check various possible attributes
            highlights = []
            if hasattr(r, "highlights") and r.highlights:
                if isinstance(r.highlights, list):
                    highlights = r.highlights
                elif isinstance(r.highlights, str):
                    highlights = [r.highlights]
            elif hasattr(r, "text") and r.text:
                # If no explicit highlights, extract a snippet from text
                text_preview = r.text[:300] if len(r.text) > 300 else r.text
                highlights = [text_preview]

            # Get text content
            text_content = ""
            if hasattr(r, "text") and r.text:
                text_content = r.text[:2000]

            result = {
                "title": getattr(r, "title", None) or "Untitled",
                "url": getattr(r, "url", ""),
                "content": text_content,
                "highlights": highlights,
                "published_date": getattr(r, "published_date", None),
            }
            results.append(result)

        logger.info(f"Web search returned {len(results)} results")
        return results

    except ImportError:
        logger.error("exa-py not installed. Run: pip install exa-py")
        return []
    except Exception as e:
        logger.error(f"Web search error: {e}", exc_info=True)
        return []


async def web_search(query: str, num_results: int = 5) -> list[dict]:
    """
    Search the web using Exa for real-time information.

    Args:
        query: The search query
        num_results: Number of results to return

    Returns:
        List of search results with title, url, content, and highlights
    """
    api_key = _get_exa_api_key()

    if not api_key:
        logger.warning("Exa API key not configured, skipping web search")
        return []

    # Run the synchronous Exa API call in a thread pool executor
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        results = await loop.run_in_executor(
            executor, _web_search_sync, query, api_key, num_results
        )

    return results


def format_web_results_for_context(results: list[dict]) -> str:
    """Format web search results for inclusion in LLM context."""
    if not results:
        return ""

    formatted = ["Web Search Results:"]
    for i, result in enumerate(results, 1):
        formatted.append(f"\n[{i}] {result['title']}")
        formatted.append(f"URL: {result['url']}")

        # Include highlights if available, otherwise use content preview
        if result.get("highlights"):
            highlights = result["highlights"]
            if isinstance(highlights, list):
                formatted.append(f"Key excerpts: {' ... '.join(highlights[:3])}")
            else:
                formatted.append(f"Key excerpt: {highlights}")
        elif result.get("content"):
            formatted.append(f"Content: {result['content'][:500]}...")

    return "\n".join(formatted)


def extract_web_citations(results: list[dict]) -> list[dict]:
    """Extract citation information from web search results with content previews and metadata."""
    citations = []
    for result in results:
        # Build content preview from highlights or content
        content_preview = ""
        if result.get("highlights"):
            highlights = result["highlights"]
            if isinstance(highlights, list):
                content_preview = " ... ".join(highlights[:3])
            else:
                content_preview = highlights
        elif result.get("content"):
            content_preview = result["content"][:500]

        citation = {
            "title": result.get("title", "Web Result"),
            "url": result.get("url", ""),
            "type": "web",
            "content_preview": content_preview,
        }

        # Add metadata for educational display
        metadata = {}
        if result.get("published_date"):
            metadata["published_date"] = result["published_date"]

        if metadata:
            citation["metadata"] = metadata

        citations.append(citation)
    return citations
