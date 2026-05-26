"""Password hashing plus JWT artefacts for judiciary operator sessions.

Includes server-side revocation via Redis blacklist keyed by ``jti``:
on logout, the token's ``jti`` is added to ``revoked:{jti}`` with TTL equal to
remaining token lifetime, so subsequent uses (cookie or Bearer) are rejected.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger("heillon.legal.auth")

_REVOKED_KEY_PREFIX = "heillon:revoked_jti:"


class AuthCredentialsError(RuntimeError):
    """Raised whenever authentication material is absent or malformed."""


def _redis_get_client():  # pragma: no cover - thin wrapper around rate_limit_redis
    """Return Redis client if available, else None (graceful degradation)."""
    try:
        from app.core.rate_limit_redis import _get_redis  # type: ignore[attr-defined]

        return _get_redis()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Redis unavailable for JWT blacklist: %s", exc)
        return None


class AuthService:
    """Thin facade around bcrypt digests plus HS256 signed envelopes."""

    def __init__(
        self,
        *,
        secret_key: str,
        algorithm: str = "HS256",
        expire_minutes: int = 60,
    ) -> None:
        if len(secret_key) < 32:
            msg = (
                "`AUTH_SECRET_KEY` must expose at least 32 characters "
                "(rotate immediately for production fleets)."
            )
            raise AuthCredentialsError(msg)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password[:72])

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password[:72], hashed_password)

    def create_access_token(self, *, subject: str, claims: dict[str, Any] | None = None) -> str:
        """Mint signed JWT with ``jti`` claim for revocation tracking."""
        to_encode: dict[str, Any] = {
            "sub": subject,
            "jti": uuid.uuid4().hex,
            "iat": int(datetime.now(UTC).timestamp()),
        }
        expire = datetime.now(UTC) + timedelta(minutes=self.expire_minutes)
        to_encode["exp"] = int(expire.timestamp())
        if claims:
            to_encode.update(claims)
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str | None) -> dict[str, Any] | None:
        """Decode + verify signature/exp + check Redis blacklist."""
        if token is None:
            return None
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            return None

        subject = payload.get("sub")
        if subject is None:
            return None

        # Reject revoked tokens (best-effort: if Redis is down, do not block auth)
        jti = payload.get("jti")
        if jti:
            client = _redis_get_client()
            if client is not None:
                try:
                    if client.exists(f"{_REVOKED_KEY_PREFIX}{jti}"):
                        return None
                except Exception as exc:  # noqa: BLE001
                    logger.warning("JWT blacklist check failed (allowing token): %s", exc)
        return payload

    def revoke_token(self, token: str | None) -> bool:
        """Add token's ``jti`` to Redis blacklist with TTL = remaining lifetime.

        Returns True if revocation succeeded, False otherwise (best-effort).
        Caller should still clear the cookie regardless.
        """
        if token is None:
            return False
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},  # revoke even slightly-expired tokens
            )
        except JWTError:
            return False

        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not isinstance(exp, (int, float)):
            return False

        ttl = max(int(exp) - int(time.time()), 1)
        client = _redis_get_client()
        if client is None:
            logger.warning("JWT revocation skipped: Redis unavailable (jti=%s)", jti)
            return False
        try:
            client.setex(f"{_REVOKED_KEY_PREFIX}{jti}", ttl, b"1")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("JWT revocation failed for jti=%s: %s", jti, exc)
            return False
