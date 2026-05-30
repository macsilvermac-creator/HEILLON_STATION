"""Domain models for the admin metrics bounded context.

Aggregate-only — these models never carry prompts, responses or PII; they back
operator dashboards during the beta and beyond.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OrganizationMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = 0
    by_tier: dict[str, int] = Field(default_factory=dict)


class UserMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = 0
    active_last_7d: int = 0


class ApiKeyMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: int = 0
    revoked: int = 0
    total: int = 0


class HdrMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = 0
    last_24h: int = 0
    last_7d: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    latest_at: str | None = None


class DailyCount(BaseModel):
    """HDRs created on a given UTC day (YYYY-MM-DD)."""

    model_config = ConfigDict(extra="forbid")

    date: str
    count: int = 0


class ActivationFunnel(BaseModel):
    """Org-level activation funnel: created → has key → has HDR → active (7d)."""

    model_config = ConfigDict(extra="forbid")

    organizations: int = 0
    with_api_key: int = 0
    with_hdr: int = 0
    active_7d: int = 0


class BetaMetrics(BaseModel):
    """Aggregate snapshot of beta adoption."""

    model_config = ConfigDict(extra="forbid")

    snapshot_at: str
    organizations: OrganizationMetrics
    users: UserMetrics
    api_keys: ApiKeyMetrics
    hdrs: HdrMetrics
    daily_hdrs: list[DailyCount] = Field(default_factory=list)
    funnel: ActivationFunnel = Field(default_factory=ActivationFunnel)


class FeedEvent(BaseModel):
    """One sanitized HDR activity event (no prompt/response content)."""

    model_config = ConfigDict(extra="forbid")

    hdr_id: str
    created_at: str
    mission_id: str
    hdr_type: str
    organization_id: str


class BetaFeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events: list[FeedEvent] = Field(default_factory=list)
    count: int = 0
