"""
Search tool for retrieving information from the knowledge base.
"""

from langchain_core.tools import tool

from kgpt.agents.retrieval import search_documents


@tool
async def search_knowledge_base_tool(query: str, sub_queries: list[str] | None = None) -> str:
    """
    Search the internal knowledge base for documents about Kafka, the specific cluster, or kGPT itself.
    Use this when you need to answer questions based on documentation, guides, or uploaded files.

    Args:
        query: The main search query (e.g., "how to configure retention").
        sub_queries: Optional list of related queries to broaden the search (e.g., ["topic retention config", "log.retention.ms"]).
    """
    docs = await search_documents(query, sub_queries)

    if not docs:
        return "No relevant documents found in the knowledge base."

    # Format docs for the LLM and UI
    content_parts = []
    artifacts = []

    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_name", "Unknown Source")
        text = doc.page_content
        content_parts.append(f"Source {i} ({source}):\n{text}\n")

        # Create structured artifact for UI
        artifacts.append(
            {
                "title": source,
                "url": doc.metadata.get("source_id", ""),
                "content": text,
                "type": "doc",
                "metadata": doc.metadata,
            }
        )

    import json

    from loguru import logger

    # Append artifacts as hidden JSON for the streaming handler to pick up
    result = "\n".join(content_parts) + "\n\n__ARTIFACTS__\n" + json.dumps(artifacts)
    logger.info(f"[TOOL DEBUG] search_knowledge_base_tool returning string length {len(result)}")
    return result
