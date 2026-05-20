"""User artefacts for judiciary-grade authentication scaffolding."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    """Horizontal privilege separation for EASY operators."""

    ADMIN = "admin"
    PERITO = "perito"
    ADVOGADO = "advogado"
    AUDITOR = "auditor"


class UserPublic(BaseModel):
    """Court-safe projection excluding password material."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    user_id: str
    email: str
    name: str
    role: UserRole
    organization_id: str
    is_active: bool = True


class UserCreate(BaseModel):
    """Registration payload anchored to deterministic tenant onboarding."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.ADVOGADO
    organization_id: str | None = None


class UserLogin(BaseModel):
    """Authenticate returning JWT artefacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    email: str = Field(min_length=3, max_length=320)
    password: str


class TokenResponse(BaseModel):
    """Bearer surface plus sanitized operator metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    access_token: str
    token_type: str = Field(default="bearer")
    user: dict[str, Any]


class UserRecord(BaseModel):
    """Hydrated datastore mirror for bearer resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str
    email: str
    name: str
    role: UserRole
    organization_id: str
    hashed_password: str
    is_active: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
