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
    real_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=20,
    )
    try:
        # Test connection with a ping
        await real_client.ping()
        _client = real_client
    except Exception as e:
        if settings.app_env.lower() == "development":
            import logging

            import fakeredis.aioredis

            logger = logging.getLogger("app.db.redis")
            logger.warning(
                "Could not connect to Redis at %s (%s). Falling back to fakeredis in development.",
                settings.redis_url,
                e,
            )
            _client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        else:
            raise e


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
