"""Redis-backed TTL cache for reference data (products, criteria, choices).

ESReferenceTool reads products.json, criteria.json, choice.json from disk
on every call. During a 15-product batch this means 45+ file reads for
data that never changes between runs.

This cache stores the parsed JSON in Redis with a configurable TTL.
When the admin updates a product/criterion, the cache expires naturally
or can be invalidated explicitly.

Toggle: set REFERENCE_CACHE_ENABLED=false to disable.
"""
from __future__ import annotations

import json
import os
import time
import logging
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

ENABLED  = os.getenv("REFERENCE_CACHE_ENABLED", "true").lower() != "false"
TTL_SECS = int(os.getenv("REFERENCE_CACHE_TTL", "3600"))
_PREFIX  = "ref:"


class ReferenceDataCache:
    """Redis-backed TTL cache for arbitrary reference keys, with in-memory fallback."""

    def __init__(self, ttl: int = TTL_SECS) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._ttl   = ttl
        self._lock  = threading.Lock()
        self._hits  = 0
        self._misses = 0

    def _redis(self):
        try:
            from app.services.cache.redis_client import get_redis
            return get_redis()
        except Exception:
            return None

    def get(self, key: str) -> Optional[Any]:
        if not ENABLED:
            return None
        r = self._redis()
        if r:
            try:
                data = r.get(f"{_PREFIX}{key}")
                if data:
                    self._hits += 1
                    return json.loads(data)
                self._misses += 1
                return None
            except Exception as exc:
                logger.warning("ReferenceCache Redis get error: %s", exc)
        # fallback: in-memory TTL
        with self._lock:
            entry = self._store.get(key)
            if entry and time.monotonic() - entry["ts"] < self._ttl:
                self._hits += 1
                return entry["data"]
            if entry:
                del self._store[key]
            self._misses += 1
            return None

    def set(self, key: str, data: Any) -> None:
        if not ENABLED:
            return
        r = self._redis()
        if r:
            try:
                r.set(f"{_PREFIX}{key}", json.dumps(data, ensure_ascii=False), ex=self._ttl)
                return
            except Exception as exc:
                logger.warning("ReferenceCache Redis set error: %s", exc)
        # fallback: in-memory TTL
        with self._lock:
            self._store[key] = {"data": data, "ts": time.monotonic()}

    def invalidate(self, key: Optional[str] = None) -> None:
        """Invalidate one key or the entire cache (key=None)."""
        r = self._redis()
        if r:
            try:
                if key:
                    r.delete(f"{_PREFIX}{key}")
                else:
                    redis_keys = r.keys(f"{_PREFIX}*")
                    if redis_keys:
                        r.delete(*redis_keys)
                logger.info("ReferenceCache (Redis): invalidated %s", key or "ALL")
                return
            except Exception as exc:
                logger.warning("ReferenceCache Redis invalidate error: %s", exc)
        # fallback: in-memory
        with self._lock:
            if key:
                self._store.pop(key, None)
            else:
                self._store.clear()
        logger.info("ReferenceCache (in-memory): invalidated %s", key or "ALL")

    def stats(self) -> dict:
        total = self._hits + self._misses
        rate  = round(self._hits / total * 100, 1) if total else 0
        r = self._redis()
        if r:
            try:
                raw_keys = r.keys(f"{_PREFIX}*")
                keys = [k.decode() if isinstance(k, bytes) else k for k in raw_keys]
                return {
                    "backend":  "redis",
                    "enabled":  ENABLED,
                    "ttl_secs": self._ttl,
                    "keys":     keys,
                    "hits":     self._hits,
                    "misses":   self._misses,
                    "hit_rate": f"{rate}%",
                }
            except Exception:
                pass
        with self._lock:
            keys = list(self._store.keys())
        return {
            "backend":  "in-memory",
            "enabled":  ENABLED,
            "ttl_secs": self._ttl,
            "keys":     keys,
            "hits":     self._hits,
            "misses":   self._misses,
            "hit_rate": f"{rate}%",
        }


# Module-level singleton
reference_cache = ReferenceDataCache()
