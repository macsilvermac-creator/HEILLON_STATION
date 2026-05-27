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

    @staticmethod
    def get_tier_state(
        conn: Any, organization_id: str
    ) -> tuple[Tier, datetime, datetime] | None:
        """Return (tier, period_start, period_end) or None if org not found.

        period_end is auto-initialized to period_start + 30d on first read
        if the column was left NULL by the migration.
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
        period_start_raw = row[1] if not hasattr(row, "keys") else row["tier_period_start"]
        period_end_raw = row[2] if not hasattr(row, "keys") else row["tier_period_end"]

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
        dt = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
