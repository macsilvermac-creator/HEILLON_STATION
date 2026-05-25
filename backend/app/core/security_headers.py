"""HTTP security headers middleware.

Adds defence-in-depth headers to every response:
- X-Content-Type-Options: prevents MIME-type sniffing attacks.
- X-Frame-Options: blocks clickjacking via iframe embedding.
- Referrer-Policy: limits referer leakage across origins.
- Permissions-Policy: disables unneeded browser features.
- Strict-Transport-Security: enforces HTTPS in production.
- Content-Security-Policy: restricts resource origins.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_CSP_PRODUCTION = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'; "
    "base-uri 'self';"
)

_CSP_DEVELOPMENT = (
    "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "connect-src 'self' ws: wss:; "
    "img-src 'self' data: blob:; "
    "frame-ancestors 'none';"
)

_STATIC_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject HTTP security headers on every response."""

    def __init__(self, app, *, is_production: bool = False) -> None:
        super().__init__(app)
        self._is_production = is_production
        self._csp = _CSP_PRODUCTION if is_production else _CSP_DEVELOPMENT

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        for header, value in _STATIC_HEADERS.items():
            response.headers[header] = value

        response.headers["Content-Security-Policy"] = self._csp

        if self._is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response
