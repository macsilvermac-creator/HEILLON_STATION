"""Quota service — single source of truth for tier enforcement.

Use from API endpoints via the dependency `enforce_hdr_quota`. Internal
flows (tests, migrations, background jobs) can call `QuotaService.check`
directly without enforcement.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.domain.tier.models import (
    QuotaExceededError,
    QuotaSnapshot,
    Tier,
    TierLimits,
)
from app.domain.tier.repository import HDRQuotaCounter, TierRepository

logger = logging.getLogger("heillon.legal.tier")


class QuotaService:
    """Stateless façade over TierRepository + HDRQuotaCounter."""

    @staticmethod
    def snapshot(conn: Any, *, organization_id: str) -> QuotaSnapshot:
        """Compute the current quota state for an organization.

        Auto-rolls the billing period if past period_end (preserves tier).
        Raises ValueError if the org doesn't exist.
        """
        state = TierRepository.get_tier_state(conn, organization_id)
        if state is None:
            msg = f"Organization not found: {organization_id}"
            raise ValueError(msg)

        tier, period_start, period_end = state
        now = datetime.now(timezone.utc)

        # Auto-rollover if period expired (free tier keeps tier=free, counter resets)
        if now >= period_end:
            period_start = now
            period_end = TierRepository.rollover_period(
                conn, organization_id=organization_id, new_period_start=now
            )

        limits = TierLimits.for_tier(tier)
        used = HDRQuotaCounter.count_in_period(
            conn,
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
        )

        if limits.monthly_hdr_limit is None:
            remaining: int | None = None
            is_exceeded = False
        else:
            remaining = max(limits.monthly_hdr_limit - used, 0)
            is_exceeded = used >= limits.monthly_hdr_limit

        return QuotaSnapshot(
            organization_id=organization_id,
            tier=tier,
            monthly_hdr_limit=limits.monthly_hdr_limit,
            used_in_period=used,
            remaining=remaining,
            period_start=period_start,
            period_end=period_end,
            is_exceeded=is_exceeded,
            retention_days=limits.retention_days,
            forensic_pdf_enabled=limits.forensic_pdf_enabled,
        )

    @staticmethod
    def enforce(conn: Any, *, organization_id: str) -> QuotaSnapshot:
        """Raise QuotaExceededError if the org has hit its limit.

        Returns the current snapshot on success (so the caller can log usage).
        API layer catches QuotaExceededError and returns HTTP 402.
        """
        snap = QuotaService.snapshot(conn, organization_id=organization_id)
        if snap.is_exceeded:
            logger.info(
                "Quota exceeded for org=%s tier=%s used=%d limit=%s",
                organization_id,
                snap.tier.value,
                snap.used_in_period,
                snap.monthly_hdr_limit,
            )
            raise QuotaExceededError(snap)
        return snap

    @staticmethod
    def apply_tier_change(
        conn: Any,
        *,
        organization_id: str,
        new_tier: Tier,
        period_end: datetime | None = None,
    ) -> QuotaSnapshot:
        """Apply a tier change (from webhook), then return new snapshot."""
        TierRepository.update_tier(
            conn,
            organization_id=organization_id,
            tier=new_tier,
            period_end=period_end,
        )
        logger.info(
            "Tier updated for org=%s -> %s (period_end=%s)",
            organization_id,
            new_tier.value,
            period_end.isoformat() if period_end else "default+30d",
        )
        return QuotaService.snapshot(conn, organization_id=organization_id)
