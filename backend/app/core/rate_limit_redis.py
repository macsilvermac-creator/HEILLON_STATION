"""Redis-backed rate limiting with in-memory fallback when Redis is unavailable."""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    import redis

logger = logging.getLogger("heillon.legal.rate_limit")

_redis_client: redis.Redis | None = None
_redis_disabled = False

# Atomically: clean expired entries, count, conditionally add — no TOCTOU window.
_SLIDING_WINDOW_LUA = """
local key      = KEYS[1]
local now      = tonumber(ARGV[1])
local win_start = tonumber(ARGV[2])
local max_req  = tonumber(ARGV[3])
local ttl      = tonumber(ARGV[4])
local member   = ARGV[5]

redis.call('ZREMRANGEBYSCORE', key, '-inf', win_start)
local count = redis.call('ZCARD', key)
if count >= max_req then
    return 0
end
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, ttl)
return 1
"""


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
        logger.warning(
            "Redis rate limiter unavailable, using in-memory fallback: %s", exc
        )
        _redis_disabled = True
        return None


class RedisRateLimiter:
    """Sliding-window limiter backed by Redis sorted sets (atomic Lua script)."""

    def __init__(self, redis_url: str | None = None) -> None:
        import redis as redis_lib

        settings = get_settings()
        self._redis = redis_lib.from_url(redis_url or settings.REDIS_URL)
        self._script = self._redis.register_script(_SLIDING_WINDOW_LUA)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        member = f"{now}:{uuid.uuid4().hex}"
        result = self._script(
            keys=[key],
            args=[now, window_start, max_requests, window_seconds + 1, member],
        )
        return bool(result)


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
        member = f"{now}:{uuid.uuid4().hex}"
        result = client.eval(
            _SLIDING_WINDOW_LUA,
            1,
            key,
            now,
            window_start,
            max_requests,
            window_seconds + 1,
            member,
        )
        return bool(result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis rate limit check failed: %s", exc)
        return None
