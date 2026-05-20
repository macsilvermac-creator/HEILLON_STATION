"""Password hashing plus JWT artefacts for judiciary operator sessions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthCredentialsError(RuntimeError):
    """Raised whenever authentication material is absent or malformed."""


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
        to_encode: dict[str, Any] = {"sub": subject}
        expire = datetime.now(UTC) + timedelta(minutes=self.expire_minutes)
        to_encode["exp"] = int(expire.timestamp())
        if claims:
            to_encode.update(claims)
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str | None) -> dict[str, Any] | None:
        if token is None:
            return None
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            return None

        subject = payload.get("sub")
        if subject is None:
            return None
        return payload
