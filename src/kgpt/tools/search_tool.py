"""
Portfolio-Quality Multi-Source Search Tool.

This module implements a sophisticated retrieval tool that:
1. Searches internal documentation (Qdrant) and web (Exa) in PARALLEL
2. Merges results using Reciprocal Rank Fusion (RRF)
3. Returns source-tagged citations for the UI

Design follows LangChain best practices:
- Pydantic input schema for structured validation
- asyncio.gather for concurrent execution
- Graceful error handling with fallbacks
- Rich artifact output for frontend rendering
"""

import asyncio
import json

from langchain_core.tools import tool
from loguru import logger
from pydantic import BaseModel, Field

from kgpt.agents.retrieval import search_documents
from kgpt.agents.web_search import is_web_search_enabled, web_search
from kgpt.tools.rrf import reciprocal_rank_fusion


class SearchInput(BaseModel):
    """
    Pydantic schema for the search tool input.

    Using a schema provides:
    - Clear documentation for the LLM
    - Input validation
    - Better type safety
    """

    query: str = Field(description="The search query to find relevant information")
    sub_queries: list[str] | None = Field(
        default=None, description="Optional additional queries to broaden internal doc search"
    )
    include_web: bool = Field(
        default=True,
        description="Whether to include real-time web search results. "
        "Set to True for questions about recent events, versions, or community discussions.",
    )


@tool("search", args_schema=SearchInput)
async def search_tool(
    query: str,
    sub_queries: list[str] | None = None,
    include_web: bool = True,
) -> str:
    """
    Search for information from internal documentation AND the web simultaneously.

    This tool searches your internal Kafka/kGPT documentation and optionally
    fetches real-time web results, then intelligently merges them using
    Reciprocal Rank Fusion to provide the most relevant combined results.

    Use this for ANY knowledge question - it automatically combines both sources.
    """
    logger.info(f"[SEARCH] Starting parallel search for: {query[:80]}...")

    # Prepare async tasks
    tasks = []

    # Task 1: Internal documentation search (always runs)
    async def fetch_docs():
        try:
            docs = await search_documents(query, sub_queries=sub_queries)
            # Convert to standard format for RRF
            return [
                {
                    "url": doc.metadata.get("source", doc.metadata.get("source_id", "")),
                    "title": doc.metadata.get("source_name", "Documentation"),
                    "content": doc.page_content,
                    "source_type": "doc",
                    "metadata": doc.metadata,
                }
                for doc in docs[:10]
            ]
        except Exception as e:
            logger.error(f"[SEARCH] Doc search failed: {e}")
            return []

    tasks.append(fetch_docs())

    # Task 2: Web search (optional, runs in parallel)
    async def fetch_web():
        if not include_web:
            return []
        if not is_web_search_enabled():
            logger.info("[SEARCH] Web search disabled, skipping")
            return []
        try:
            results = await web_search(query, num_results=5)
            # Convert to standard format for RRF
            return [
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", "Web Result"),
                    "content": r.get("content", ""),
                    "source_type": "web",
                    "metadata": {"published_date": r.get("published_date")},
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"[SEARCH] Web search failed: {e}")
            return []

    tasks.append(fetch_web())

    # Execute both searches in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    doc_results = results[0] if not isinstance(results[0], Exception) else []
    web_results = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else []

    logger.info(f"[SEARCH] Retrieved {len(doc_results)} docs, {len(web_results)} web results")

    # Merge results using Reciprocal Rank Fusion
    if doc_results and web_results:
        merged = reciprocal_rank_fusion(doc_results, web_results, id_key="url")
    elif doc_results:
        merged = doc_results
    elif web_results:
        merged = web_results
    else:
        return "No results found from documentation or web search."

    # Build response text with numbered citations
    content_parts = []
    artifacts = []

    # Add merged results with sequential numbering
    for i, result in enumerate(merged[:10], 1):
        source_type = result.get("source_type", "unknown")
        title = result.get("title", "Unknown")
        url = result.get("url", "")
        content = result.get("content", "")
        rrf_score = result.get("rrf_score", 0)

        # Format for LLM
        source_label = "📄 Doc" if source_type == "doc" else "🌐 Web"
        content_parts.append(
            f"[{i}] {source_label} - {title}\n"
            f"{'URL: ' + url if url.startswith('http') else ''}\n"
            f"{content[:1500]}{'...' if len(content) > 1500 else ''}\n"
        )

        # Build artifact for UI
        artifacts.append(
            {
                "title": title,
                "url": url if url.startswith("http") else "",
                "content": content,
                "content_preview": content[:500] + ("..." if len(content) > 500 else ""),
                "type": source_type,
                "relevance_score": rrf_score,
                "metadata": result.get("metadata", {}),
            }
        )

    header = (
        f"SEARCH RESULTS ({len([a for a in artifacts if a['type'] == 'doc'])} docs, "
        f"{len([a for a in artifacts if a['type'] == 'web'])} web):\n"
        f"{'=' * 60}\n"
    )

    result_text = header + "\n".join(content_parts)

    # Append artifacts as hidden JSON for streaming handler
    output = result_text + "\n\n__ARTIFACTS__\n" + json.dumps(artifacts)

    logger.info(
        f"[SEARCH] Returning {len(artifacts)} merged results "
        f"(docs: {len(doc_results)}, web: {len(web_results)})"
    )

    return output
