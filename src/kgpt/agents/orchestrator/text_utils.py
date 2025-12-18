"""Text extraction utilities for handling various LLM chunk formats."""

from typing import Any


def extract_text_from_chunk(chunk: Any) -> str | None:
    """
    Extract text content from an LLM streaming chunk.

    Handles various formats:
    - Plain string content
    - List of content blocks [{"type": "text", "text": "..."}] (Claude format)
    - AIMessageChunk with string or list content
    - Other formats that might contain text

    Returns:
        The extracted text string, or None if no text could be extracted.
    """
    # Get the content from the chunk
    if hasattr(chunk, "content"):
        content = chunk.content
    else:
        content = chunk

    # Handle None or empty
    if content is None:
        return None

    # Handle plain strings
    if isinstance(content, str):
        return content if content else None

    # Handle list of content blocks (Claude format)
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict):
                # {"type": "text", "text": "..."} format
                if "text" in item and isinstance(item["text"], str):
                    texts.append(item["text"])
                # {"content": "..."} format
                elif "content" in item and isinstance(item["content"], str):
                    texts.append(item["content"])
            elif isinstance(item, str):
                texts.append(item)
            # Skip any non-string items that couldn't be extracted
        return "".join(texts) if texts else None

    # Handle dict with text/content keys
    if isinstance(content, dict):
        if "text" in content and isinstance(content["text"], str):
            return content["text"]
        if "content" in content and isinstance(content["content"], str):
            return content["content"]
        # Don't log warning for every dict - just return None
        return None

    # Handle numbers
    if isinstance(content, (int, float)):
        return str(content)

    # Skip unhandled types silently
    return None
