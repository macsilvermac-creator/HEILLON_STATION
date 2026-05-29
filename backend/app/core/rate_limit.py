"""In-process ASGI rate limiting (P0) — does not read request bodies."""

from __future__ import annotations

import os
import time
from collections import defaultdict

from fastapi import Request, status
from starlette.responses import JSONResponse


class RateLimiter:
    """Simple in-memory limiter; replace with Redis for horizontal scale."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        bucket = [t for t in self._requests[key] if t >= window_start]
        self._requests[key] = bucket
        if len(bucket) >= max_requests:
            return False
        bucket.append(now)
        return True


limiter = RateLimiter()

EXEMPT_PATH_PREFIXES = ("/health", "/docs", "/openapi", "/redoc")


def _classify_rate_path(path: str) -> tuple[str, int, int] | None:
    """Return (limit_key, max_req, window_sec) or None if no dedicated bucket."""

    if not path.startswith("/api/v1"):
        return None
    if path.startswith("/api/v1/auth/login"):
        return (path.split("?")[0], 5, 60)
    if path.startswith("/api/v1/auth/register"):
        return (path.split("?")[0], 3, 60)
    if path.startswith("/api/v1/ingestion"):
        return ("/api/v1/ingestion", 10, 60)
    if path.startswith("/api/v1/mission/plan"):
        return ("/api/v1/mission/plan", 20, 60)
    if "/execute" in path and path.startswith("/api/v1/mission/"):
        return ("/api/v1/mission/execute", 10, 60)
    return None


async def rate_limit_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path.startswith(EXEMPT_PATH_PREFIXES):
        return await call_next(request)

    if path.endswith((".js", ".css", ".ico", ".png", ".jpg", ".svg", ".woff2")):
        return await call_next(request)

    classified = _classify_rate_path(path)
    if classified is None:
        return await call_next(request)

    bucket_key, max_req, window_sec = classified
    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI_E2E") == "true":
        return await call_next(request)
    from app.core.config import get_settings

    if get_settings().DISABLE_RATE_LIMIT:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{bucket_key}"
    from app.core.rate_limit_redis import redis_is_allowed

    redis_ok = redis_is_allowed(f"rate_limit:{key}", max_req, window_sec)
    allowed = (
        redis_ok
        if redis_ok is not None
        else limiter.is_allowed(key, max_req, window_sec)
    )
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please try again later."},
        )

    return await call_next(request)
