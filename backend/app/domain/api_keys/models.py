"""API key models — plaintext is ephemeral; only hash persists."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

API_KEY_PREFIX = "heillon_live_"


class ApiKeyCreate(BaseModel):
    """Operator request to mint a new API key."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(
        min_length=1,
        max_length=120,
        description="Human-readable label, e.g. 'Browser Extension - Chrome Pessoal'.",
    )


class ApiKeyPublic(BaseModel):
    """Sanitized projection for listing (no plaintext, no hash)."""

    model_config = ConfigDict(extra="forbid")

    api_key_id: str
    name: str
    prefix: str = Field(
        description="First 12 chars of plaintext for visual identification"
    )
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


class ApiKeyMintResponse(BaseModel):
    """Response when minting a key — plaintext is included ONCE."""

    model_config = ConfigDict(extra="forbid")

    api_key_id: str
    name: str
    plaintext_key: str = Field(
        description="Full key value — SHOW ONCE in UI and instruct user to store it.",
    )
    prefix: str
    created_at: datetime


class ApiKeyRecord(BaseModel):
    """Hydrated row for internal use (carries hash, not plaintext)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    api_key_id: str
    organization_id: str
    user_id: str
    name: str
    prefix: str
    key_hash: str
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> "ApiKeyRecord":
        from datetime import timezone

        def parse_dt(value: Any) -> datetime | None:
            if value is None:
                return None
            if isinstance(value, datetime):
                return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
            text = str(value).strip().replace(" ", "T")
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(text)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return None

        def get(field: str) -> Any:
            return (
                row[field] if hasattr(row, "keys") else row[_FIELD_ORDER.index(field)]
            )

        return cls(
            api_key_id=str(get("api_key_id")),
            organization_id=str(get("organization_id")),
            user_id=str(get("user_id")),
            name=str(get("name")),
            prefix=str(get("prefix")),
            key_hash=str(get("key_hash")),
            last_used_at=parse_dt(get("last_used_at")),
            revoked_at=parse_dt(get("revoked_at")),
            created_at=parse_dt(get("created_at")) or datetime.now(timezone.utc),
        )


_FIELD_ORDER = (
    "api_key_id",
    "organization_id",
    "user_id",
    "name",
    "prefix",
    "key_hash",
    "last_used_at",
    "revoked_at",
    "created_at",
)
