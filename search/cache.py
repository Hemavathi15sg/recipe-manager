"""
In-process cache for search results.

A ``NullCache`` (no-op) is provided so tests never need a running Redis
instance.  The ``InMemoryCache`` replaces the original global-dict cache
that had an unbounded memory leak (expired entries were never evicted).

Production systems should swap ``InMemoryCache`` for a Redis-backed
implementation using the same ``get`` / ``set`` / ``clear`` interface.
"""
import hashlib
import json
import logging
import threading
import time
from typing import Optional

from search.config import CACHE_TTL_SECONDS, ENABLE_CACHE

logger = logging.getLogger(__name__)


class NullCache:
    """No-op cache.  Used in tests and when caching is disabled."""

    def get(self, key: str) -> Optional[dict]:
        return None

    def set(self, key: str, value: dict) -> None:
        pass

    def clear(self) -> None:
        pass


class InMemoryCache:
    """Thread-safe in-memory cache with TTL-based expiry.

    Expired entries are evicted on access so memory does not grow
    unboundedly (fixes the original memory-leak bug — Issue #183).
    """

    def __init__(self, ttl: int = CACHE_TTL_SECONDS) -> None:
        self._store: dict[str, dict] = {}
        self._timestamps: dict[str, float] = {}
        self._ttl = ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[dict]:
        with self._lock:
            if key not in self._store:
                logger.debug("Cache MISS: %s", key[:60])
                return None

            age = time.time() - self._timestamps[key]
            if age >= self._ttl:
                # Evict expired entry on access
                del self._store[key]
                del self._timestamps[key]
                logger.debug("Cache EXPIRED (age=%.1fs): %s", age, key[:60])
                return None

            logger.debug("Cache HIT (age=%.1fs): %s", age, key[:60])
            return self._store[key]

    def set(self, key: str, value: dict) -> None:
        with self._lock:
            self._store[key] = value
            self._timestamps[key] = time.time()
            logger.debug("Cache SET: %s (%d entries total)", key[:60], len(self._store))

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._timestamps.clear()
            logger.debug("Cache cleared")


def make_cache_key(request_dict: dict) -> str:
    """Return a deterministic cache key for *request_dict*.

    The key is derived from a SHA-256 digest of the canonicalised JSON
    representation so that identical requests always produce the same key
    regardless of insertion order.  The ``v1:`` prefix allows safe
    cache-busting if the schema changes.
    """
    canonical = json.dumps(request_dict, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    return f"search:v1:{digest}"


def build_cache() -> InMemoryCache | NullCache:
    """Return the configured cache implementation."""
    if ENABLE_CACHE:
        return InMemoryCache()
    return NullCache()
