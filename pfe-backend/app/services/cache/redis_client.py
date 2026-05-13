"""Singleton Redis client with graceful fallback when Redis is unavailable."""
from __future__ import annotations

import logging
from typing import Optional

import redis as redis_lib

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[redis_lib.Redis] = None


def get_redis() -> Optional[redis_lib.Redis]:
    """Return Redis client, or None if disabled or unreachable."""
    global _client
    if not settings.redis_enabled:
        return None
    if _client is None:
        try:
            _client = redis_lib.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            _client.ping()
            logger.info("Redis connected at %s:%s db=%s", settings.redis_host, settings.redis_port, settings.redis_db)
        except Exception as exc:
            logger.warning("Redis unavailable — falling back to in-memory/file cache: %s", exc)
            _client = None
    return _client


def reset_client() -> None:
    """Force reconnect on next call (useful after Redis restart)."""
    global _client
    _client = None
