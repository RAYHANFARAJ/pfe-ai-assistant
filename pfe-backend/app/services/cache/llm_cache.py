"""Redis-backed cache for LLM extraction results with file-based fallback.

Key insight: if the same criterion is evaluated against identical passages
(same client re-scored, or two clients with the same source text), GPT
returns the same answer. We cache keyed by:

    sha256(criterion_id + answer_type + joined_passages[:2000])

TTL: 24 hours (configurable). Never caches invalid/empty results.

Toggle: set LLM_CACHE_ENABLED=false to disable.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ENABLED   = os.getenv("LLM_CACHE_ENABLED", "true").lower() != "false"
TTL_HOURS = int(os.getenv("LLM_CACHE_TTL_HOURS", "24"))
_CACHE_FILE = Path(__file__).parent.parent.parent.parent / "output" / "llm_cache.json"
_lock   = threading.Lock()
_PREFIX = "llm:"


def _cache_key(criterion_id: str, answer_type: str, passages: List[str]) -> str:
    payload = f"{criterion_id}::{answer_type}::" + "|".join(passages)[:2000]
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _redis():
    try:
        from app.services.cache.redis_client import get_redis
        return get_redis()
    except Exception:
        return None


# ── File-based fallback helpers ───────────────────────────────────────────────

def _load() -> Dict[str, Any]:
    try:
        if _CACHE_FILE.exists():
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("LLMCache file load failed: %s", exc)
    return {}


def _save(cache: Dict[str, Any]) -> None:
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        logger.error("LLMCache file save failed: %s", exc)


# ── Public API ────────────────────────────────────────────────────────────────

def get_extraction(
    criterion_id: str,
    answer_type: str,
    passages: List[str],
) -> Optional[Dict[str, Any]]:
    """Return cached extraction result or None."""
    if not ENABLED:
        return None
    key = _cache_key(criterion_id, answer_type, passages)
    r = _redis()
    if r:
        try:
            data = r.get(f"{_PREFIX}{key}")
            if data:
                logger.debug("LLMCache HIT (Redis) criterion=%s", criterion_id)
                return json.loads(data)
            return None
        except Exception as exc:
            logger.warning("LLMCache Redis get error: %s", exc)
    # fallback: file-based
    cache = _load()
    entry = cache.get(key)
    if not entry:
        return None
    try:
        if datetime.fromisoformat(entry["expires_at"]) < datetime.now():
            return None
    except (KeyError, ValueError):
        return None
    logger.debug("LLMCache HIT (file) criterion=%s", criterion_id)
    return entry["result"]


def set_extraction(
    criterion_id: str,
    answer_type: str,
    passages: List[str],
    result: Dict[str, Any],
) -> None:
    """Persist extraction result. Only caches valid answers."""
    if not ENABLED:
        return
    if not result or result.get("predicted_answer") in (None, "", "unknown"):
        return
    if result.get("confidence", 0) < 0.3:
        return
    key = _cache_key(criterion_id, answer_type, passages)
    r = _redis()
    if r:
        try:
            r.set(
                f"{_PREFIX}{key}",
                json.dumps(result, ensure_ascii=False),
                ex=TTL_HOURS * 3600,
            )
            logger.debug("LLMCache SET (Redis) criterion=%s", criterion_id)
            return
        except Exception as exc:
            logger.warning("LLMCache Redis set error: %s", exc)
    # fallback: file-based
    now = datetime.now()
    with _lock:
        cache = _load()
        cache[key] = {
            "result":       result,
            "criterion_id": criterion_id,
            "answer_type":  answer_type,
            "cached_at":    now.isoformat(),
            "expires_at":   (now + timedelta(hours=TTL_HOURS)).isoformat(),
        }
        if len(cache) > 5000:
            oldest = sorted(cache.items(), key=lambda x: x[1].get("cached_at", ""))
            cache = dict(oldest[-5000:])
        _save(cache)
    logger.debug("LLMCache SET (file) criterion=%s", criterion_id)


def stats() -> Dict[str, Any]:
    r = _redis()
    if r:
        try:
            keys = r.keys(f"{_PREFIX}*")
            return {
                "backend":   "redis",
                "enabled":   ENABLED,
                "ttl_hours": TTL_HOURS,
                "total":     len(keys),
            }
        except Exception:
            pass
    cache = _load()
    now   = datetime.now()
    valid = sum(
        1 for e in cache.values()
        if datetime.fromisoformat(e.get("expires_at", "2000-01-01")) > now
    )
    return {
        "backend":   "file",
        "enabled":   ENABLED,
        "ttl_hours": TTL_HOURS,
        "total":     len(cache),
        "valid":     valid,
        "expired":   len(cache) - valid,
    }
