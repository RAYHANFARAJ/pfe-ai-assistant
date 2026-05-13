"""Redis-backed LRU cache for query embeddings with in-memory fallback.

embed_query() is called once per criterion per product scoring.
With 15 products × 30 criteria = 450 calls, many criterion labels
are shared across products ("Effectif total", "Secteur éligible", …).
Caching by query text avoids recomputing identical vectors.

Toggle: set EMBEDDING_CACHE_ENABLED=false to disable.
"""
from __future__ import annotations

import os
import pickle
import logging
from collections import OrderedDict
from typing import Any, Optional

logger = logging.getLogger(__name__)

ENABLED  = os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() != "false"
MAX_SIZE = int(os.getenv("EMBEDDING_CACHE_MAX_SIZE", "1000"))
_PREFIX  = "emb:"


class EmbeddingCache:
    """Redis-backed cache for query embedding vectors, with in-memory LRU fallback."""

    def __init__(self, maxsize: int = MAX_SIZE) -> None:
        self._maxsize  = maxsize
        self._fallback: OrderedDict[str, Any] = OrderedDict()
        self._hits   = 0
        self._misses = 0

    def _redis(self):
        from app.services.cache.redis_client import get_redis
        return get_redis()

    def get(self, query: str) -> Optional[Any]:
        if not ENABLED:
            return None
        key = query.strip().lower()
        r = self._redis()
        if r:
            try:
                data = r.get(f"{_PREFIX}{key}")
                if data:
                    self._hits += 1
                    return pickle.loads(data)
                self._misses += 1
                return None
            except Exception as exc:
                logger.warning("EmbeddingCache Redis get error: %s", exc)
        # fallback: in-memory LRU
        if key in self._fallback:
            self._fallback.move_to_end(key)
            self._hits += 1
            return self._fallback[key]
        self._misses += 1
        return None

    def set(self, query: str, embedding: Any) -> None:
        if not ENABLED or embedding is None:
            return
        key = query.strip().lower()
        r = self._redis()
        if r:
            try:
                from app.core.config import settings
                r.set(f"{_PREFIX}{key}", pickle.dumps(embedding), ex=settings.redis_cache_ttl)
                return
            except Exception as exc:
                logger.warning("EmbeddingCache Redis set error: %s", exc)
        # fallback: in-memory LRU
        self._fallback[key] = embedding
        self._fallback.move_to_end(key)
        if len(self._fallback) > self._maxsize:
            evicted = self._fallback.popitem(last=False)
            logger.debug("EmbeddingCache fallback: evicted '%s'", evicted[0][:40])

    def stats(self) -> dict:
        total = self._hits + self._misses
        rate  = round(self._hits / total * 100, 1) if total else 0
        r = self._redis()
        backend = "redis" if r else "in-memory"
        size = len(self._fallback)
        if r:
            try:
                size = len(r.keys(f"{_PREFIX}*"))
            except Exception:
                pass
        return {
            "backend":   backend,
            "enabled":   ENABLED,
            "size":      size,
            "max_size":  self._maxsize,
            "hits":      self._hits,
            "misses":    self._misses,
            "hit_rate":  f"{rate}%",
        }


# Module-level singleton
embedding_cache = EmbeddingCache()
