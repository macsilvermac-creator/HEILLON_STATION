"""API key service — secure mint, hash storage, lookup, revocation."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from app.domain.api_keys.models import (
    API_KEY_PREFIX,
    ApiKeyMintResponse,
    ApiKeyPublic,
    ApiKeyRecord,
)


def _hash_key(plaintext: str) -> str:
    """SHA-256 of the plaintext key — never store the plaintext itself."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def _generate_plaintext() -> str:
    """Cryptographically random key with stable prefix for identification."""
    # 32 URL-safe chars = 192 bits of entropy (more than enough)
    suffix = secrets.token_urlsafe(24)  # ~32 chars
    return f"{API_KEY_PREFIX}{suffix}"


class ApiKeyService:
    """Stateless service for API key lifecycle."""

    @staticmethod
    def mint(
        conn: Any, *, organization_id: str, user_id: str, name: str
    ) -> ApiKeyMintResponse:
        """Create a new API key; returns plaintext ONCE, stores only hash."""
        plaintext = _generate_plaintext()
        key_hash = _hash_key(plaintext)
        prefix = plaintext[:16]  # heillon_live_ + 4 chars
        api_key_id = f"key_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        conn.execute(
            """INSERT INTO api_keys (
                       api_key_id, organization_id, user_id, name,
                       prefix, key_hash, last_used_at, revoked_at, created_at
                   ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?)
            """,
            (
                api_key_id,
                organization_id,
                user_id,
                name,
                prefix,
                key_hash,
                now.isoformat(),
            ),
        )

        return ApiKeyMintResponse(
            api_key_id=api_key_id,
            name=name,
            plaintext_key=plaintext,
            prefix=prefix,
            created_at=now,
        )

    @staticmethod
    def list_by_org(conn: Any, *, organization_id: str) -> list[ApiKeyPublic]:
        """List all keys for an org (no plaintext, no hash exposed)."""
        rows = conn.execute(
            """SELECT api_key_id, name, prefix, last_used_at, revoked_at, created_at
               FROM api_keys
               WHERE organization_id = ?
               ORDER BY created_at DESC""",
            (organization_id,),
        ).fetchall()

        result: list[ApiKeyPublic] = []
        for row in rows:
            from datetime import timezone

            def parse_dt(value: Any) -> datetime | None:
                if value is None or value == "":
                    return None
                text = str(value).strip().replace(" ", "T")
                if text.endswith("Z"):
                    text = text[:-1] + "+00:00"
                try:
                    dt = datetime.fromisoformat(text)
                    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    return None

            def get(field: str, idx: int) -> Any:
                return row[field] if hasattr(row, "keys") else row[idx]

            result.append(
                ApiKeyPublic(
                    api_key_id=str(get("api_key_id", 0)),
                    name=str(get("name", 1)),
                    prefix=str(get("prefix", 2)),
                    last_used_at=parse_dt(get("last_used_at", 3)),
                    revoked_at=parse_dt(get("revoked_at", 4)),
                    created_at=parse_dt(get("created_at", 5))
                    or datetime.now(timezone.utc),
                )
            )
        return result

    @staticmethod
    def find_active_by_plaintext(conn: Any, plaintext: str) -> ApiKeyRecord | None:
        """Lookup by hashing the supplied plaintext; returns None if revoked or unknown."""
        if not plaintext or not plaintext.startswith(API_KEY_PREFIX):
            return None
        key_hash = _hash_key(plaintext)
        row = conn.execute(
            """SELECT api_key_id, organization_id, user_id, name, prefix,
                      key_hash, last_used_at, revoked_at, created_at
               FROM api_keys
               WHERE key_hash = ? AND revoked_at IS NULL""",
            (key_hash,),
        ).fetchone()
        if row is None:
            return None
        return ApiKeyRecord.from_row(row)

    @staticmethod
    def touch_last_used(conn: Any, api_key_id: str) -> None:
        """Update last_used_at to NOW — called after successful auth."""
        conn.execute(
            "UPDATE api_keys SET last_used_at = ? WHERE api_key_id = ?",
            (datetime.now(timezone.utc).isoformat(), api_key_id),
        )

    @staticmethod
    def revoke(
        conn: Any, *, api_key_id: str, organization_id: str
    ) -> bool:
        """Mark a key as revoked. Returns True if a row was affected."""
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """UPDATE api_keys
               SET revoked_at = ?
               WHERE api_key_id = ?
                 AND organization_id = ?
                 AND revoked_at IS NULL""",
            (now, api_key_id, organization_id),
        )
        # SQLite/Postgres compat: rowcount may be on cursor or on conn
        affected = getattr(cursor, "rowcount", None)
        if affected is None:
            affected = getattr(conn, "rowcount", 0)
        return bool(affected and affected > 0)
