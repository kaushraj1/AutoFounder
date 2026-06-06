"""Async Redis connection pool — app-level singleton.

Initialized once in FastAPI lifespan (main.py); all code calls get_redis().
On shutdown, close_redis() drains the pool cleanly.
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import get_settings

_client: aioredis.Redis | None = None


async def init_redis() -> None:
    """Open the connection pool. Called once at startup."""
    global _client
    settings = get_settings()
    _client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=20,
    )


async def close_redis() -> None:
    """Drain the connection pool. Called once at shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def get_redis() -> aioredis.Redis:
    """Return the app-level Redis client. Raises if pool not initialized."""
    if _client is None:
        raise RuntimeError("Redis pool not initialized — call init_redis() first.")
    return _client
