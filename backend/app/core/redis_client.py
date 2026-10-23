"""
app/core/redis_client.py
========================
Redis connection pool lifecycle for the token revocation blocklist.

Usage
-----
  from app.core.redis_client import get_redis, init_redis, close_redis

  # In FastAPI startup:
  await init_redis()

  # In dependencies / services:
  r = get_redis()
  if r is not None:
      await r.set("key", "value")

  # In FastAPI shutdown:
  await close_redis()

The pool is created once at startup and shared across all requests.
If REDIS_URL is not configured (dev mode), all operations gracefully
return None and log warnings — the app still runs without Redis,
but token revocation is disabled.
"""
from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger("security.redis")

# Module-level pool — initialized once at startup
_redis_pool: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """
    Initialize the async Redis connection pool.

    Called from FastAPI's startup event. No-op if REDIS_URL is not set
    (development mode without Redis).
    """
    global _redis_pool

    if not settings.REDIS_URL:
        logger.warning(
            "REDIS_URL not configured — token revocation is DISABLED. "
            "Set REDIS_URL in .env for production use."
        )
        return

    try:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        # Verify connectivity
        await _redis_pool.ping()
        logger.info("Redis connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis at {settings.REDIS_URL}: {e}")
        _redis_pool = None
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(
                f"Cannot start production server without Redis: {e}"
            ) from e


async def close_redis() -> None:
    """
    Cleanly close the Redis connection pool.

    Called from FastAPI's shutdown event.
    """
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
        logger.info("Redis connection pool closed")


def get_redis() -> Optional[aioredis.Redis]:
    """
    Return the Redis connection pool instance.

    Returns None if Redis was not initialized (REDIS_URL not set
    or connection failed in non-production).
    """
    return _redis_pool


def set_redis(client: Optional[aioredis.Redis]) -> None:
    """
    Override the Redis client instance (used in tests with fakeredis).

    Args:
        client: A Redis-compatible client, or None to clear.
    """
    global _redis_pool
    _redis_pool = client


async def is_redis_available() -> bool:
    """
    Health check — returns True if Redis is reachable.
    """
    if _redis_pool is None:
        return False
    try:
        await _redis_pool.ping()
        return True
    except Exception:
        return False
