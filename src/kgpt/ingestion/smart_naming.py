"""Smart naming service for document sources.

Uses a cheap LLM (gpt-4o-mini) to generate descriptive names for document sources
based on URL patterns and optionally content samples.
"""

import re
from urllib.parse import urlparse

from loguru import logger


def extract_name_from_url(url: str) -> str:
    """Extract a basic name from URL patterns.

    This is the fallback when LLM is not available.
    """
    if not url:
        return "Unknown Source"

    parsed = urlparse(url)

    # Extract domain without TLD
    domain = parsed.netloc.replace("www.", "")
    parts = domain.split(".")

    # Handle common patterns
    if "docs" in parts:
        # e.g., docs.confluent.io -> Confluent Docs
        parts = [p for p in parts if p not in ["docs", "io", "com", "org", "net"]]
        if parts:
            return f"{parts[0].title()} Documentation"

    if "github" in parts:
        # GitHub repo
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return f"{path_parts[0]}/{path_parts[1]}"

    # Use first meaningful part of domain
    if parts:
        main_part = parts[0]
        if main_part.lower() not in ["www", "docs", "api", "dev"]:
            return main_part.title()

    return parsed.netloc


def generate_smart_name_sync(
    url: str,
    content_sample: str | None = None,
    source_type: str = "url",
) -> str:
    """Generate a smart, descriptive name for a document source.

    Uses gpt-4o-mini for cost-effective naming with good quality.
    Falls back to URL parsing if LLM fails.

    Args:
        url: The URL of the document source
        content_sample: Optional sample of content (first few paragraphs)
        source_type: Type of source (sitemap, github, url)

    Returns:
        A short, descriptive name for the source
    """
    try:
        from kgpt.llm.providers import get_openai_api_key

        api_key = get_openai_api_key()
        if not api_key:
            logger.debug("No OpenAI API key available, using fallback naming")
            if source_type == "text" and content_sample:
                # For raw text without API key, use first line or first 50 chars
                first_line = content_sample.split("\n")[0].strip()
                if first_line and len(first_line) <= 50:
                    return first_line
                return (
                    content_sample[:50].strip() + "..."
                    if len(content_sample) > 50
                    else content_sample.strip()
                )
            return extract_name_from_url(url)

        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        # Build context for the LLM
        if source_type == "text" and content_sample:
            # For raw text, focus on content only
            sample = content_sample[:500] if len(content_sample) > 500 else content_sample
            context = f"Source type: Raw text content\nContent:\n{sample}"
        else:
            context_parts = [f"URL: {url}", f"Source type: {source_type}"]
            if content_sample:
                # Truncate content sample to keep costs low
                sample = content_sample[:500] if len(content_sample) > 500 else content_sample
                context_parts.append(f"Content sample: {sample}")
            context = "\n".join(context_parts)

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheap and effective for this task
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a naming assistant. Generate a short, descriptive name for "
                        "a document source that will be added to a RAG knowledge base. "
                        "The name should be:\n"
                        "- 2-5 words maximum\n"
                        "- Descriptive of what the documentation covers\n"
                        "- In title case\n"
                        "- Without 'Documentation' or 'Docs' suffix unless essential\n"
                        "Reply with ONLY the name, nothing else."
                    ),
                },
                {"role": "user", "content": context},
            ],
            max_tokens=30,
            temperature=0.3,  # Low temp for consistency
        )

        content = response.choices[0].message.content
        if not content:
            logger.warning("LLM returned empty content")
            return extract_name_from_url(url)

        name = content.strip()
        # Clean up the name
        name = name.strip("\"'")

        # Validate it's reasonable
        if len(name) > 50 or len(name) < 2:
            logger.warning(f"LLM returned invalid name length: {name}")
            if source_type == "text" and content_sample:
                first_line = content_sample.split("\n")[0].strip()
                if first_line and len(first_line) <= 50:
                    return first_line
                return (
                    content_sample[:50].strip() + "..."
                    if len(content_sample) > 50
                    else content_sample.strip()
                )
            return extract_name_from_url(url)

        if source_type == "text":
            logger.info(f"Generated smart name for raw text: {name}")
        else:
            logger.info(f"Generated smart name for {url}: {name}")
        return name

    except Exception as e:
        logger.warning(f"Smart naming failed, using fallback: {e}")
        if source_type == "text" and content_sample:
            first_line = content_sample.split("\n")[0].strip()
            if first_line and len(first_line) <= 50:
                return first_line
            return (
                content_sample[:50].strip() + "..."
                if len(content_sample) > 50
                else content_sample.strip()
            )
        return extract_name_from_url(url)


async def generate_smart_name(
    url: str,
    content_sample: str | None = None,
    source_type: str = "url",
) -> str:
    """Async version of smart name generation.

    Uses async OpenAI client for better performance in async contexts.
    """
    try:
        from kgpt.llm.providers import get_openai_api_key

        api_key = get_openai_api_key()
        if not api_key:
            logger.debug("No OpenAI API key available, using fallback naming")
            if source_type == "text" and content_sample:
                # For raw text without API key, use first line or first 50 chars
                first_line = content_sample.split("\n")[0].strip()
                if first_line and len(first_line) <= 50:
                    return first_line
                return (
                    content_sample[:50].strip() + "..."
                    if len(content_sample) > 50
                    else content_sample.strip()
                )
            return extract_name_from_url(url)

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)

        # Build context for the LLM
        if source_type == "text" and content_sample:
            # For raw text, focus on content only
            sample = content_sample[:500] if len(content_sample) > 500 else content_sample
            context = f"Source type: Raw text content\nContent:\n{sample}"
        else:
            context_parts = [f"URL: {url}", f"Source type: {source_type}"]
            if content_sample:
                sample = content_sample[:500] if len(content_sample) > 500 else content_sample
                context_parts.append(f"Content sample: {sample}")
            context = "\n".join(context_parts)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a naming assistant. Generate a short, descriptive name for "
                        "a document source that will be added to a RAG knowledge base. "
                        "The name should be:\n"
                        "- 2-5 words maximum\n"
                        "- Descriptive of what the documentation covers\n"
                        "- In title case\n"
                        "- Without 'Documentation' or 'Docs' suffix unless essential\n"
                        "Reply with ONLY the name, nothing else."
                    ),
                },
                {"role": "user", "content": context},
            ],
            max_tokens=30,
            temperature=0.3,
        )

        content = response.choices[0].message.content
        if not content:
            logger.warning("LLM returned empty content")
            return extract_name_from_url(url)

        name = content.strip()
        name = name.strip("\"'")

        if len(name) > 50 or len(name) < 2:
            logger.warning(f"LLM returned invalid name length: {name}")
            if source_type == "text" and content_sample:
                first_line = content_sample.split("\n")[0].strip()
                if first_line and len(first_line) <= 50:
                    return first_line
                return (
                    content_sample[:50].strip() + "..."
                    if len(content_sample) > 50
                    else content_sample.strip()
                )
            return extract_name_from_url(url)

        if source_type == "text":
            logger.info(f"Generated smart name for raw text: {name}")
        else:
            logger.info(f"Generated smart name for {url}: {name}")
        return name

    except Exception as e:
        logger.warning(f"Smart naming failed, using fallback: {e}")
        if source_type == "text" and content_sample:
            first_line = content_sample.split("\n")[0].strip()
            if first_line and len(first_line) <= 50:
                return first_line
            return (
                content_sample[:50].strip() + "..."
                if len(content_sample) > 50
                else content_sample.strip()
            )
        return extract_name_from_url(url)


def suggest_names_for_url(url: str) -> list[str]:
    """Generate multiple name suggestions for a URL.

    Useful for UI autocomplete or giving users options.
    Returns a list of 3-5 suggestions.
    """
    suggestions = []

    # Always include the URL-based extraction
    url_name = extract_name_from_url(url)
    suggestions.append(url_name)

    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/")

    # Add domain-based suggestion
    domain_parts = domain.split(".")
    if domain_parts:
        main_domain = domain_parts[0].title()
        if main_domain.lower() not in ["docs", "api", "www"]:
            suggestions.append(main_domain)

    # Add path-based suggestions
    if path:
        path_parts = path.split("/")
        meaningful_parts = [p for p in path_parts if p and len(p) > 2]
        if meaningful_parts:
            # First meaningful path segment
            suggestions.append(meaningful_parts[0].replace("-", " ").replace("_", " ").title())

            # Combined path
            if len(meaningful_parts) >= 2:
                combined = f"{meaningful_parts[0]} {meaningful_parts[1]}"
                suggestions.append(combined.replace("-", " ").replace("_", " ").title())

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in suggestions:
        normalized = s.lower().strip()
        if normalized not in seen and len(normalized) >= 2:
            seen.add(normalized)
            unique.append(s)

    return unique[:5]


def sanitize_collection_name(name: str) -> str:
    """Convert a display name to a valid Qdrant collection name.

    Collection names should be lowercase alphanumeric with underscores.
    """
    # Lowercase and replace spaces/hyphens with underscores
    sanitized = name.lower()
    sanitized = re.sub(r"[\s\-]+", "_", sanitized)
    sanitized = re.sub(r"[^a-z0-9_]", "", sanitized)
    sanitized = re.sub(r"_+", "_", sanitized)  # Collapse multiple underscores
    sanitized = sanitized.strip("_")

    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = "src_" + sanitized

    # Ensure reasonable length
    if len(sanitized) > 50:
        sanitized = sanitized[:50].rstrip("_")

    return sanitized or "unnamed_source"


def extract_name_from_message(message: str) -> str:
    """Extract a basic name from a chat message.

    This is the fallback when LLM is not available.
    """
    if not message:
        return "New Chat"

    # Remove common prefixes/questions
    message = message.strip()

    # Remove question marks and common question words
    message = re.sub(
        r"^(what|how|why|when|where|who|can|could|would|should|is|are|do|does|did)\s+",
        "",
        message,
        flags=re.IGNORECASE,
    )

    # Take first sentence or first 50 chars
    first_sentence = message.split(".")[0].split("?")[0].split("!")[0].strip()

    if not first_sentence:
        first_sentence = message

    # Limit to 50 chars
    if len(first_sentence) > 50:
        # Try to cut at word boundary
        truncated = first_sentence[:47]
        last_space = truncated.rfind(" ")
        if last_space > 20:  # Only use word boundary if reasonable
            truncated = truncated[:last_space]
        return truncated + "..."

    return first_sentence


async def generate_chat_smart_name(first_message: str) -> str:
    """Generate a smart, descriptive name for a chat session.

    Uses gpt-4o-mini for cost-effective naming with good quality.
    Falls back to message extraction if LLM fails.

    Args:
        first_message: The first user message in the chat session

    Returns:
        A short, descriptive name for the chat (2-5 words)
    """
    if not first_message or not first_message.strip():
        return "New Chat"

    try:
        from kgpt.llm.providers import get_openai_api_key

        api_key = get_openai_api_key()
        if not api_key:
            logger.debug("No OpenAI API key available, using fallback naming for chat")
            return extract_name_from_message(first_message)

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)

        # Truncate message to keep costs low
        message_sample = first_message[:500] if len(first_message) > 500 else first_message

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a naming assistant. Generate a short, descriptive title for "
                        "a chat conversation based on the first user message. "
                        "The title should be:\n"
                        "- 2-5 words maximum\n"
                        "- Descriptive of the conversation topic\n"
                        "- In title case\n"
                        "- Without question marks or punctuation\n"
                        "- Focused on the main topic or question\n"
                        "Reply with ONLY the title, nothing else."
                    ),
                },
                {"role": "user", "content": f"First message: {message_sample}"},
            ],
            max_tokens=30,
            temperature=0.3,
        )

        content = response.choices[0].message.content
        if not content:
            logger.warning("LLM returned empty content for chat name")
            return extract_name_from_message(first_message)

        name = content.strip()
        name = name.strip("\"'")
        name = name.rstrip("?!")

        # Validate it's reasonable
        if len(name) > 50 or len(name) < 2:
            logger.warning(f"LLM returned invalid chat name length: {name}")
            return extract_name_from_message(first_message)

        logger.info(f"Generated smart name for chat: {name}")
        return name

    except Exception as e:
        logger.warning(f"Smart naming for chat failed, using fallback: {e}")
        return extract_name_from_message(first_message)
