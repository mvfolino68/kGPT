"""Simple in-memory cache for kGPT."""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class CacheEntry:
    """A single cache entry with TTL support."""

    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: float = 3600  # Default 1 hour

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, max_size: int = 100, default_ttl: float = 3600):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds
        """
        self._cache: dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        """Create a hash key."""
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        hashed = self._make_key(key)
        entry = self._cache.get(hashed)

        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[hashed]
            return None

        logger.debug(f"Cache hit for key: {key[:50]}...")
        return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None):
        """Set a value in cache."""
        # Evict oldest entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        hashed = self._make_key(key)
        self._cache[hashed] = CacheEntry(
            value=value,
            ttl=ttl or self.default_ttl,
        )
        logger.debug(f"Cached value for key: {key[:50]}...")

    def _evict_oldest(self):
        """Remove the oldest cache entry."""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def cleanup_expired(self):
        """Remove all expired entries."""
        expired = [k for k, v in self._cache.items() if v.is_expired()]
        for k in expired:
            del self._cache[k]
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired cache entries")


# Global cache instances
_query_cache: SimpleCache | None = None
_embedding_cache: SimpleCache | None = None


def get_query_cache() -> SimpleCache:
    """Get the query result cache."""
    global _query_cache
    if _query_cache is None:
        _query_cache = SimpleCache(max_size=50, default_ttl=1800)  # 30 min TTL
    return _query_cache


def get_embedding_cache() -> SimpleCache:
    """Get the embedding cache."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = SimpleCache(max_size=200, default_ttl=86400)  # 24 hour TTL
    return _embedding_cache
