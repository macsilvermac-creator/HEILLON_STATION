"""Redis-backed rate limiting with in-memory fallback when Redis is unavailable."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    import redis

logger = logging.getLogger("heillon.legal.rate_limit")

_redis_client: redis.Redis | None = None
_redis_disabled = False


def _get_redis() -> redis.Redis | None:
    global _redis_client, _redis_disabled

    if _redis_disabled:
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        import redis as redis_lib

        settings = get_settings()
        client = redis_lib.from_url(settings.REDIS_URL, decode_responses=False)
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis rate limiter unavailable, using in-memory fallback: %s", exc)
        _redis_disabled = True
        return None


class RedisRateLimiter:
    """Sliding-window limiter backed by Redis sorted sets."""

    def __init__(self, redis_url: str | None = None) -> None:
        import redis as redis_lib

        settings = get_settings()
        self._redis = redis_lib.from_url(redis_url or settings.REDIS_URL)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        _, count = pipe.execute()
        if int(count) >= max_requests:
            return False
        self._redis.zadd(key, {str(now): now})
        self._redis.expire(key, window_seconds + 1)
        return True


_redis_limiter: RedisRateLimiter | None = None


def redis_is_allowed(key: str, max_requests: int, window_seconds: int) -> bool | None:
    """
    Return True/False when Redis handled the check.
    Return None when Redis is down (caller should use in-memory limiter).
    """

    client = _get_redis()
    if client is None:
        return None

    try:
        now = time.time()
        window_start = now - window_seconds
        client.zremrangebyscore(key, 0, window_start)
        count = int(client.zcard(key))
        if count >= max_requests:
            return False
        client.zadd(key, {str(now).encode(): now})
        client.expire(key, window_seconds + 1)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis rate limit check failed: %s", exc)
        return None
