"""Text preprocessing utilities for RAG document ingestion.

Cleans and normalizes text before embedding to improve retrieval quality.
Uses ftfy for Unicode fixing and provides custom cleaning for documentation.
"""

import re
import unicodedata

from loguru import logger


def fix_unicode(text: str) -> str:
    """Fix Unicode issues like mojibake, broken encoding, etc.

    Uses ftfy if available, otherwise falls back to basic normalization.
    """
    if not text:
        return text

    try:
        import ftfy

        return ftfy.fix_text(text)
    except ImportError:
        # Fallback to basic Unicode normalization
        return unicodedata.normalize("NFKC", text)


def normalize_whitespace(text: str) -> str:
    """Normalize all whitespace to single spaces and clean up line breaks."""
    if not text:
        return text

    # Replace multiple newlines with double newline (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Replace tabs and other whitespace with space
    text = re.sub(r"[\t\r\f\v]+", " ", text)

    # Replace multiple spaces with single space
    text = re.sub(r"  +", " ", text)

    # Clean up spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    return text.strip()


def remove_boilerplate(text: str) -> str:
    """Remove common boilerplate patterns from documentation.

    Removes:
    - Cookie notices
    - Navigation breadcrumbs
    - Footer content
    - Share buttons text
    - "Skip to content" links
    """
    if not text:
        return text

    # Common boilerplate patterns
    boilerplate_patterns = [
        # Cookie notices
        r"(?i)we use cookies.*?(?:accept|agree|continue)",
        r"(?i)this (site|website) uses cookies.*?(?:\.|$)",
        # Skip links
        r"(?i)skip to (main )?content",
        r"(?i)jump to navigation",
        # Social sharing
        r"(?i)share (this|on)( article| page)?:?\s*(twitter|facebook|linkedin|email|reddit)*",
        r"(?i)(tweet|share|pin|email) (this|it)",
        # Navigation breadcrumbs (common patterns)
        r"(?i)^(home|docs?|documentation)\s*[>/»]\s*",
        # Edit on GitHub links
        r"(?i)edit (this page )?on github",
        r"(?i)view source on github",
        # Table of contents headers
        r"(?i)^(table of contents|on this page|in this article):?\s*$",
        # Last updated notices at start of lines
        r"(?i)^(last )?(updated|modified|edited):?\s*\d{4}[-/]\d{2}[-/]\d{2}",
        # Print/PDF buttons
        r"(?i)(print|download) (this )?(page|article|as pdf)",
    ]

    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text)

    return text


def clean_markdown_artifacts(text: str) -> str:
    """Clean up markdown artifacts that might interfere with embeddings.

    Preserves semantic content but removes formatting noise.
    """
    if not text:
        return text

    # Remove image references (keep alt text if meaningful)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # Convert links to just text (remove URLs)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove HTML tags (common in markdown docs)
    text = re.sub(r"<[^>]+>", "", text)

    # Remove markdown emphasis markers but keep text
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)  # bold
    text = re.sub(r"\*([^*]+)\*", r"\1", text)  # italic
    text = re.sub(r"__([^_]+)__", r"\1", text)  # bold
    text = re.sub(r"_([^_]+)_", r"\1", text)  # italic
    text = re.sub(r"~~([^~]+)~~", r"\1", text)  # strikethrough
    text = re.sub(r"`([^`]+)`", r"\1", text)  # inline code

    # Clean up header markers (keep text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Clean up list markers
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)

    return text


def remove_code_blocks(text: str, keep_comments: bool = True) -> str:
    """Remove code blocks from text.

    Optionally keeps comments which often contain useful documentation.

    Args:
        text: Input text
        keep_comments: If True, extracts and keeps code comments
    """
    if not text:
        return text

    if keep_comments:
        # Extract comments from code blocks before removing
        code_block_pattern = r"```[\w]*\n(.*?)```"

        def extract_comments(match):
            code = match.group(1)
            comments = []
            # Python/shell comments
            comments.extend(re.findall(r"#\s*(.+)$", code, re.MULTILINE))
            # JS/Java/C comments
            comments.extend(re.findall(r"//\s*(.+)$", code, re.MULTILINE))
            # Multi-line comments
            comments.extend(re.findall(r"/\*\s*(.*?)\s*\*/", code, re.DOTALL))
            return " ".join(comments) if comments else ""

        text = re.sub(code_block_pattern, extract_comments, text, flags=re.DOTALL)
    else:
        # Simply remove code blocks
        text = re.sub(r"```[\w]*\n.*?```", "", text, flags=re.DOTALL)

    return text


def normalize_for_embedding(text: str) -> str:
    """Normalize text specifically for embedding quality.

    - Lowercases text
    - Removes excessive punctuation
    - Normalizes numbers
    """
    if not text:
        return text

    # Lowercase
    text = text.lower()

    # Normalize numbers to reduce sparsity
    # Keep years intact, normalize other numbers
    text = re.sub(r"\b(19|20)\d{2}\b", lambda m: m.group(), text)  # Keep years
    text = re.sub(r"\b\d{5,}\b", "NUM", text)  # Long numbers to NUM

    # Normalize URLs
    text = re.sub(r"https?://\S+", "URL", text)

    # Remove excessive punctuation
    text = re.sub(r"[!?]{2,}", "!", text)
    text = re.sub(r"\.{3,}", "...", text)

    return text


def preprocess_for_rag(
    text: str,
    clean_boilerplate: bool = True,
    clean_markdown: bool = True,
    remove_code: bool = False,
    normalize_embedding: bool = False,
) -> str:
    """Full preprocessing pipeline for RAG document ingestion.

    Applies a sequence of cleaning operations to prepare text for embedding.

    Args:
        text: Raw text to process
        clean_boilerplate: Remove common boilerplate patterns
        clean_markdown: Clean markdown formatting artifacts
        remove_code: Remove code blocks (default False - code can be valuable)
        normalize_embedding: Apply aggressive normalization for embedding
            (lowercase, number normalization - may reduce readability)

    Returns:
        Cleaned text ready for chunking and embedding
    """
    if not text:
        return text

    # Step 1: Fix Unicode issues (always do this)
    text = fix_unicode(text)

    # Step 2: Remove boilerplate
    if clean_boilerplate:
        text = remove_boilerplate(text)

    # Step 3: Clean markdown artifacts
    if clean_markdown:
        text = clean_markdown_artifacts(text)

    # Step 4: Optionally remove code blocks
    if remove_code:
        text = remove_code_blocks(text, keep_comments=True)

    # Step 5: Normalize whitespace (always do this)
    text = normalize_whitespace(text)

    # Step 6: Optional aggressive normalization for embedding
    if normalize_embedding:
        text = normalize_for_embedding(text)

    return text


def extract_title_from_content(text: str, max_length: int = 100) -> str | None:
    """Try to extract a title from document content.

    Looks for common title patterns in documentation.
    """
    if not text:
        return None

    # Check first few lines for a title
    lines = text.strip().split("\n")[:10]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip very short or very long lines
        if len(line) < 3 or len(line) > max_length:
            continue

        # Skip lines that look like metadata
        if re.match(r"^(date|author|updated|published|by|copyright):", line, re.I):
            continue

        # Skip lines that are mostly punctuation or numbers
        alpha_ratio = sum(c.isalpha() for c in line) / len(line)
        if alpha_ratio < 0.5:
            continue

        # This looks like a title
        return line

    return None


def get_text_quality_score(text: str) -> float:
    """Calculate a quality score for the text (0-1).

    Higher scores indicate higher quality content.
    Useful for filtering out low-quality pages.
    """
    if not text:
        return 0.0

    # Length check
    if len(text) < 100:
        return 0.1

    score = 0.5

    # Ratio of alphabetic characters
    alpha_ratio = sum(c.isalpha() for c in text) / len(text)
    score += alpha_ratio * 0.2

    # Sentence structure (periods followed by capital letters)
    sentences = len(re.findall(r"\.\s+[A-Z]", text))
    if sentences > 3:
        score += 0.1

    # Word diversity
    words = text.lower().split()
    if words:
        unique_ratio = len(set(words)) / len(words)
        score += unique_ratio * 0.1

    # Penalize excessive repetition
    if re.search(r"(.{20,})\1{2,}", text):
        score -= 0.2

    # Penalize excessive special characters
    special_ratio = len(re.findall(r"[^\w\s]", text)) / len(text)
    if special_ratio > 0.2:
        score -= 0.1

    return max(0.0, min(1.0, score))


class TextPreprocessor:
    """Configurable text preprocessor for document ingestion."""

    def __init__(
        self,
        clean_boilerplate: bool = True,
        clean_markdown: bool = True,
        remove_code: bool = False,
        normalize_embedding: bool = False,
        min_quality_score: float = 0.3,
    ):
        """Initialize preprocessor with configuration.

        Args:
            clean_boilerplate: Remove navigation, cookies, etc.
            clean_markdown: Strip markdown formatting
            remove_code: Remove code blocks
            normalize_embedding: Aggressive normalization (lowercase, etc.)
            min_quality_score: Minimum quality score to accept (0-1)
        """
        self.clean_boilerplate = clean_boilerplate
        self.clean_markdown = clean_markdown
        self.remove_code = remove_code
        self.normalize_embedding = normalize_embedding
        self.min_quality_score = min_quality_score

    def process(self, text: str) -> str | None:
        """Process text through the pipeline.

        Returns None if text doesn't meet quality threshold.
        """
        if not text:
            return None

        # Preprocess
        cleaned = preprocess_for_rag(
            text,
            clean_boilerplate=self.clean_boilerplate,
            clean_markdown=self.clean_markdown,
            remove_code=self.remove_code,
            normalize_embedding=self.normalize_embedding,
        )

        # Check quality
        quality = get_text_quality_score(cleaned)
        if quality < self.min_quality_score:
            logger.debug(f"Rejecting low-quality text (score={quality:.2f})")
            return None

        return cleaned

    def process_batch(self, texts: list[str]) -> list[str]:
        """Process multiple texts, filtering out low-quality ones."""
        results = []
        for text in texts:
            processed = self.process(text)
            if processed:
                results.append(processed)

        logger.info(f"Processed {len(texts)} texts, kept {len(results)} after quality filter")
        return results
