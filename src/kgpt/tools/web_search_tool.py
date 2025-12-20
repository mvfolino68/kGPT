"""
Web search tool using Exa.
"""

from langchain_core.tools import tool

from kgpt.agents.web_search import web_search


@tool
async def search_web_tool(query: str) -> str:
    """
    Search the internet for up-to-date information about Kafka, error messages, or general technical questions.
    Use this when the internal knowledge base doesn't have the answer or when you need recent information.

    Args:
        query: The search query.
    """
    results = await web_search(query)

    if not results:
        return "No web search results found."

    formatted = ["Web Search Results:"]
    artifacts = []

    for i, res in enumerate(results[:5], 1):
        title = res.get("title", "Untitled")
        url = res.get("url", "")
        content = ""
        if res.get("highlights"):
            content = " ... ".join(res["highlights"][:3])
        elif res.get("content"):
            content = res["content"][:300]

        formatted.append(f"Source {i} ({title}):\nURL: {url}\n{content}\n")

        # Create structured artifact for UI
        artifacts.append(
            {
                "title": title,
                "url": url,
                "content": content,
                "type": "web",
                "metadata": {"published_date": res.get("published_date")},
            }
        )

    import json

    # Append artifacts as hidden JSON for the streaming handler to pick up
    return "\n".join(formatted) + "\n\n__ARTIFACTS__\n" + json.dumps(artifacts)
