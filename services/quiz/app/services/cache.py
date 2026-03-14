"""In-memory TTL cache for quiz responses.

Simple dict-based cache with 5-minute TTL and prefix-based invalidation.
No Redis dependency — keeps the setup lightweight.
"""

import time
from typing import Any


class TTLCache:
    """A simple in-memory cache with time-to-live eviction."""

    def __init__(self, ttl_seconds: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Any | None:
        """Get a value from the cache. Returns None if not found or expired."""
        if key in self._store:
            value, expires_at = self._store[key]
            if time.time() < expires_at:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache with TTL."""
        self._store[key] = (value, time.time() + self._ttl)

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove all cache entries whose key starts with the given prefix."""
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]


# Global quiz cache instance — 5-minute TTL
quiz_cache = TTLCache(ttl_seconds=300)
