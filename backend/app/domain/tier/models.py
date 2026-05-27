"""Tier enum, quota snapshot, and webhook payload models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Tier(str, Enum):
    """Commercial tiers driving quota and retention policies.

    Tier semantics are owned by the platform; pricing is owned by the
    external marketing site (out of scope for this system).
    """

    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class TierLimits(BaseModel):
    """Quota + retention rules per tier.

    `monthly_hdr_limit = None` means unlimited.
    `retention_days = None` means indefinite (no purge job).
    """

    model_config = ConfigDict(frozen=True)

    monthly_hdr_limit: int | None
    retention_days: int | None
    max_users: int | None
    forensic_pdf_enabled: bool
    icp_brasil_enabled: bool

    @classmethod
    def for_tier(cls, tier: Tier) -> TierLimits:
        if tier == Tier.FREE:
            return cls(
                monthly_hdr_limit=50,
                retention_days=30,
                max_users=1,
                forensic_pdf_enabled=False,
                icp_brasil_enabled=True,  # selo básico sempre disponível
            )
        if tier == Tier.PRO:
            return cls(
                monthly_hdr_limit=None,
                retention_days=365,
                max_users=1,
                forensic_pdf_enabled=True,
                icp_brasil_enabled=True,
            )
        if tier == Tier.TEAM:
            return cls(
                monthly_hdr_limit=None,
                retention_days=1825,  # 5 years
                max_users=10,
                forensic_pdf_enabled=True,
                icp_brasil_enabled=True,
            )
        # Enterprise: no limits
        return cls(
            monthly_hdr_limit=None,
            retention_days=None,
            max_users=None,
            forensic_pdf_enabled=True,
            icp_brasil_enabled=True,
        )


class QuotaSnapshot(BaseModel):
    """Real-time quota visibility surface, consumed by /me/quota and collectors."""

    model_config = ConfigDict(frozen=True)

    organization_id: str
    tier: Tier
    monthly_hdr_limit: int | None = Field(
        description="None = unlimited (Pro/Team/Enterprise)"
    )
    used_in_period: int
    remaining: int | None = Field(
        description="None when unlimited; otherwise max(limit - used, 0)"
    )
    period_start: datetime
    period_end: datetime
    is_exceeded: bool
    retention_days: int | None
    forensic_pdf_enabled: bool

    @property
    def usage_pct(self) -> float | None:
        """0.0-1.0 (None if unlimited). Useful for UI progress bars."""
        if self.monthly_hdr_limit is None or self.monthly_hdr_limit == 0:
            return None
        return min(self.used_in_period / self.monthly_hdr_limit, 1.0)


class BillingWebhookEvent(str, Enum):
    """Event types accepted from the external billing site."""

    TIER_CHANGED = "tier_changed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_FAILED = "payment_failed"  # downgrade to free as fallback


class BillingWebhookPayload(BaseModel):
    """HMAC-signed payload from the external marketing/billing site.

    The site is the source of truth for purchases; this webhook is how that
    truth reaches the system. Signature verified against
    `BILLING_WEBHOOK_SECRET`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    event: BillingWebhookEvent
    organization_id: str = Field(min_length=1, max_length=200)
    tier: Tier
    period_end: datetime | None = Field(
        default=None,
        description="Optional explicit period end; defaults to 30d from now.",
    )
    occurred_at: datetime
    external_subscription_id: str | None = None


class QuotaExceededError(RuntimeError):
    """Raised when an HDR-creating operation hits the tier limit.

    The API layer catches this and returns HTTP 402 Payment Required.
    """

    def __init__(self, snapshot: QuotaSnapshot) -> None:
        self.snapshot = snapshot
        super().__init__(
            f"Quota exceeded for org {snapshot.organization_id}: "
            f"used {snapshot.used_in_period}/{snapshot.monthly_hdr_limit} on tier {snapshot.tier.value}"
        )
