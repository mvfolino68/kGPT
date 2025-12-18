"""Text extraction utilities for handling various LLM chunk formats."""

from typing import Any

from loguru import logger


def extract_text_from_chunk(chunk: Any, debug: bool = False) -> str | None:
    """
    Extract text content from an LLM streaming chunk.

    Handles various formats:
    - Plain string content
    - List of content blocks [{"type": "text", "text": "..."}] (Claude format)
    - AIMessageChunk with string or list content
    - Other formats that might contain text

    Args:
        chunk: The chunk to extract text from
        debug: If True, log detailed information about chunk processing

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
        if debug:
            logger.debug("Chunk content is None")
        return None

    # Handle plain strings
    if isinstance(content, str):
        result = content if content else None
        if debug and result:
            logger.debug(f"Extracted string content: {result[:50]}...")
        return result

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
        result = "".join(texts) if texts else None
        if debug:
            logger.debug(f"Extracted from list: {len(texts)} items, result={bool(result)}")
        return result

    # Handle dict with text/content keys
    if isinstance(content, dict):
        if "text" in content and isinstance(content["text"], str):
            if debug:
                logger.debug(f"Extracted from dict.text: {content['text'][:50]}...")
            return content["text"]
        if "content" in content and isinstance(content["content"], str):
            if debug:
                logger.debug(f"Extracted from dict.content: {content['content'][:50]}...")
            return content["content"]
        if debug:
            logger.debug(f"Dict has no extractable text. Keys: {content.keys()}")
        return None

    # Handle numbers
    if isinstance(content, (int, float)):
        if debug:
            logger.debug(f"Converted number to string: {content}")
        return str(content)

    # Skip unhandled types
    if debug:
        logger.warning(f"Unhandled chunk type: {type(content)}")
    return None
