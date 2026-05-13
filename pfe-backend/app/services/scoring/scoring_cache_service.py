"""Scoring cache — persists (client_id, product_id) results to a JSON file.

Cache hits make campaign scoring instant for already-scored clients.
Batch scoring (SearchCompany) populates the cache automatically so
campaign scoring can reuse those rich results without re-crawling.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_CACHE_FILE = Path(__file__).parent.parent.parent.parent / "output" / "scoring_cache.json"
_TTL_DAYS   = 7
_lock       = threading.Lock()


class ScoringCacheService:

    def get(self, client_id: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Return cached result or None if missing / expired."""
        key = _key(client_id, product_id)
        cache = _load()
        entry = cache.get(key)
        if not entry:
            return None
        try:
            if datetime.fromisoformat(entry["expires_at"]) < datetime.now():
                logger.debug("Cache EXPIRED for %s", key)
                return None
        except (KeyError, ValueError):
            return None
        logger.info("Cache HIT  for client=%s product=%s", client_id, product_id)
        return {**entry["result"], "cache_hit": True}

    def set(self, client_id: str, product_id: str, result: Dict[str, Any]) -> None:
        """Store a scoring result, overwriting any previous entry for this key."""
        if result.get("status") == "failed" or "error" in result:
            return          # never cache failures
        key = _key(client_id, product_id)
        now = datetime.now()
        with _lock:
            cache = _load()
            cache[key] = {
                "result":     result,
                "cached_at":  now.isoformat(),
                "expires_at": (now + timedelta(days=_TTL_DAYS)).isoformat(),
                "client_id":  client_id,
                "product_id": product_id,
            }
            _save(cache)
        logger.info("Cache SET  for client=%s product=%s (TTL %dd)", client_id, product_id, _TTL_DAYS)

    def invalidate(self, client_id: str, product_id: Optional[str] = None) -> int:
        """Remove cache entries for a client (all products if product_id is None)."""
        with _lock:
            cache = _load()
            before = len(cache)
            if product_id:
                cache.pop(_key(client_id, product_id), None)
            else:
                cache = {k: v for k, v in cache.items() if v.get("client_id") != client_id}
            _save(cache)
        removed = before - len(cache)
        logger.info("Cache INVALIDATED %d entry(ies) for client=%s", removed, client_id)
        return removed

    def stats(self) -> Dict[str, Any]:
        cache = _load()
        now   = datetime.now()
        valid = sum(
            1 for e in cache.values()
            if datetime.fromisoformat(e.get("expires_at", "2000-01-01")) > now
        )
        return {"total": len(cache), "valid": valid, "expired": len(cache) - valid}


# ── Module-level singleton ────────────────────────────────────────────────────
scoring_cache = ScoringCacheService()


# ── Internal helpers ──────────────────────────────────────────────────────────
def _key(client_id: str, product_id: str) -> str:
    return f"{client_id}::{product_id}"


def _load() -> Dict[str, Any]:
    try:
        if _CACHE_FILE.exists():
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Cache load failed: %s — starting fresh", exc)
    return {}


def _save(cache: Dict[str, Any]) -> None:
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.error("Cache save failed: %s", exc)
