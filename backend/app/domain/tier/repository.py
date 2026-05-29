"""SQL-level access for tier and quota data.

Compatible with both SQLite (dev/test) and PostgreSQL (prod) via the
CompatConnection layer's ? placeholder translation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.tier.models import Tier


class TierRepository:
    """Read/write tier metadata on the organizations table.

    Tier lives at the ORG level (not user) — multi-user teams share quota.
    """

    # Sentinel value used by migration 021 as column DEFAULT (SQLite can't use
    # CURRENT_TIMESTAMP in ALTER TABLE ADD COLUMN). Any org with this value
    # was created AFTER migration ran (via ensure_organization) and needs
    # lazy backfill to NOW on first read.
    _SENTINEL_PERIOD_START = "1970-01-01T00:00:00Z"

    @staticmethod
    def get_tier_state(
        conn: Any, organization_id: str
    ) -> tuple[Tier, datetime, datetime] | None:
        """Return (tier, period_start, period_end) or None if org not found.

        Performs lazy backfill on first read for orgs created via
        ensure_organization (which doesn't set tier columns explicitly).
        """
        row = conn.execute(
            """SELECT tier, tier_period_start, tier_period_end
               FROM organizations
               WHERE organization_id = ?""",
            (organization_id,),
        ).fetchone()
        if row is None:
            return None

        tier = Tier(str(row[0] if not hasattr(row, "keys") else row["tier"]))
        period_start_raw = (
            row[1] if not hasattr(row, "keys") else row["tier_period_start"]
        )
        period_end_raw = row[2] if not hasattr(row, "keys") else row["tier_period_end"]

        now = datetime.now(timezone.utc)
        period_start_str = str(period_start_raw).strip()

        # Detect sentinel (new org via ensure_organization) → backfill from
        # the org's actual created_at (so HDRs inserted right after creation
        # are correctly captured in the first billing period).
        if (
            period_start_str == TierRepository._SENTINEL_PERIOD_START
            or period_start_str.startswith("1970")
        ):
            org_created_row = conn.execute(
                "SELECT created_at FROM organizations WHERE organization_id = ?",
                (organization_id,),
            ).fetchone()
            org_created_raw = (
                (
                    org_created_row[0]
                    if not hasattr(org_created_row, "keys")
                    else org_created_row["created_at"]
                )
                if org_created_row
                else None
            )
            try:
                org_created_at = (
                    _parse_db_timestamp(org_created_raw) if org_created_raw else now
                )
            except Exception:
                org_created_at = now
            # Cap look-back to 30d to avoid runaway windows for legacy orgs
            min_start = now - timedelta(days=30)
            period_start = max(org_created_at, min_start)
            period_end = period_start + timedelta(days=30)
            conn.execute(
                """UPDATE organizations
                   SET tier_period_start = ?, tier_period_end = ?
                   WHERE organization_id = ?""",
                (period_start.isoformat(), period_end.isoformat(), organization_id),
            )
            return tier, period_start, period_end

        period_start = _parse_db_timestamp(period_start_raw)
        period_end = (
            _parse_db_timestamp(period_end_raw)
            if period_end_raw
            else period_start + timedelta(days=30)
        )

        # Lazy backfill if period_end was NULL from migration
        if not period_end_raw:
            conn.execute(
                "UPDATE organizations SET tier_period_end = ? WHERE organization_id = ?",
                (period_end.isoformat(), organization_id),
            )

        return tier, period_start, period_end

    @staticmethod
    def update_tier(
        conn: Any,
        *,
        organization_id: str,
        tier: Tier,
        period_end: datetime | None = None,
    ) -> None:
        """Apply a tier change from a billing webhook.

        Resets period_start to NOW and period_end to NOW+30d if not provided.
        """
        now = datetime.now(timezone.utc)
        resolved_end = period_end or (now + timedelta(days=30))
        conn.execute(
            """UPDATE organizations
               SET tier = ?,
                   tier_period_start = ?,
                   tier_period_end = ?,
                   tier_updated_at = ?
               WHERE organization_id = ?""",
            (
                tier.value,
                now.isoformat(),
                resolved_end.isoformat(),
                now.isoformat(),
                organization_id,
            ),
        )

    @staticmethod
    def rollover_period(
        conn: Any, *, organization_id: str, new_period_start: datetime
    ) -> datetime:
        """Reset the billing period to start at `new_period_start` for 30 days.

        Called when the previous period_end has passed without a webhook
        update — keeps the tier but resets the quota counter.
        Returns the new period_end.
        """
        new_period_end = new_period_start + timedelta(days=30)
        conn.execute(
            """UPDATE organizations
               SET tier_period_start = ?, tier_period_end = ?
               WHERE organization_id = ?""",
            (new_period_start.isoformat(), new_period_end.isoformat(), organization_id),
        )
        return new_period_end


class HDRQuotaCounter:
    """Count HDRs created server-side within a billing period."""

    @staticmethod
    def count_in_period(
        conn: Any,
        *,
        organization_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        row = conn.execute(
            """SELECT COUNT(*) FROM hdrs
               WHERE organization_id = ?
                 AND created_at >= ?
                 AND created_at < ?""",
            (
                organization_id,
                period_start.isoformat(),
                period_end.isoformat(),
            ),
        ).fetchone()
        if row is None:
            return 0
        # tuple-like or row-like
        value = row[0] if not hasattr(row, "keys") else row[0]
        return int(value or 0)


def _parse_db_timestamp(value: Any) -> datetime:
    """Parse SQLite/Postgres timestamp into UTC datetime."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip().replace(" ", "T")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # Fallback: try common SQLite default 'YYYY-MM-DD HH:MM:SS'
        dt = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
