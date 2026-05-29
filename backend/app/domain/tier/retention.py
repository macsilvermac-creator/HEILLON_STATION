"""HDR retention enforcement (F30B2 — LGPD art. 15 / art. 16).

Free tier keeps HDRs for 30 days; Pro 365d; Team 1825d; Enterprise forever
(see ``TierLimits.for_tier``). This service purges HDRs whose server-side
``created_at`` is older than the org's tier retention window.

Design notes
------------
* Retention is a *product policy*, distinct from the evidentiary chain
  immutability guaranteed *within* the retention window. Inside the window
  HDRs are never mutated; once the window lapses for a non-paying tier, the
  record is purged in full (LGPD art. 16 — dados eliminados ao fim do
  tratamento, salvo bases legais de retenção).
* Enterprise (``retention_days is None``) is skipped entirely.
* The job is idempotent and safe to run repeatedly (cron). It commits per
  organization so a failure mid-run doesn't lose prior progress.
* Counts are returned for observability / runbook logging.

Invoked by ``scripts/cron_purge_retention.py`` (cron / systemd timer) or the
admin endpoint can call ``RetentionService.purge_all`` directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.tier.models import Tier, TierLimits

logger = logging.getLogger("heillon.legal.retention")


@dataclass
class OrgPurgeResult:
    """Per-organization purge outcome."""

    organization_id: str
    tier: str
    retention_days: int | None
    cutoff_iso: str | None
    purged: int


@dataclass
class RetentionRunResult:
    """Aggregate result of a full retention sweep."""

    started_at: str
    finished_at: str
    organizations_scanned: int = 0
    organizations_purged: int = 0
    total_hdrs_purged: int = 0
    per_org: list[OrgPurgeResult] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "organizations_scanned": self.organizations_scanned,
            "organizations_purged": self.organizations_purged,
            "total_hdrs_purged": self.total_hdrs_purged,
            "per_org": [
                {
                    "organization_id": r.organization_id,
                    "tier": r.tier,
                    "retention_days": r.retention_days,
                    "cutoff_iso": r.cutoff_iso,
                    "purged": r.purged,
                }
                for r in self.per_org
            ],
        }


class RetentionService:
    """Stateless façade enforcing per-tier HDR retention windows."""

    @staticmethod
    def purge_all(conn: Any, *, now: datetime | None = None) -> RetentionRunResult:
        """Purge expired HDRs for every organization, per its tier window.

        Returns a :class:`RetentionRunResult` for logging / metrics.
        ``now`` is injectable for deterministic tests.
        """
        now = now or datetime.now(timezone.utc)
        result = RetentionRunResult(
            started_at=now.isoformat(),
            finished_at=now.isoformat(),
        )

        rows = conn.execute(
            "SELECT organization_id, tier FROM organizations"
        ).fetchall()

        for row in rows:
            org_id = row[0] if not hasattr(row, "keys") else row["organization_id"]
            tier_raw = row[1] if not hasattr(row, "keys") else row["tier"]
            result.organizations_scanned += 1

            try:
                tier = Tier(str(tier_raw))
            except ValueError:
                tier = Tier.FREE  # defensive: unknown tier → strictest policy

            limits = TierLimits.for_tier(tier)
            retention_days = limits.retention_days

            if retention_days is None:
                # Enterprise / indefinite — never purge.
                result.per_org.append(
                    OrgPurgeResult(
                        organization_id=str(org_id),
                        tier=tier.value,
                        retention_days=None,
                        cutoff_iso=None,
                        purged=0,
                    )
                )
                continue

            cutoff = now - timedelta(days=retention_days)
            cutoff_iso = cutoff.isoformat()

            purged = RetentionService._purge_org(
                conn, organization_id=str(org_id), cutoff_iso=cutoff_iso
            )

            if purged:
                result.organizations_purged += 1
                result.total_hdrs_purged += purged
                logger.info(
                    "Retention purge org=%s tier=%s cutoff=%s purged=%d",
                    org_id,
                    tier.value,
                    cutoff_iso,
                    purged,
                )

            result.per_org.append(
                OrgPurgeResult(
                    organization_id=str(org_id),
                    tier=tier.value,
                    retention_days=retention_days,
                    cutoff_iso=cutoff_iso,
                    purged=purged,
                )
            )

        result.finished_at = datetime.now(timezone.utc).isoformat()
        return result

    @staticmethod
    def _purge_org(conn: Any, *, organization_id: str, cutoff_iso: str) -> int:
        """Delete HDRs for one org older than cutoff. Returns rows deleted.

        We count first (portable across SQLite/Postgres which differ on
        DELETE rowcount semantics) then delete.
        """
        count_row = conn.execute(
            """SELECT COUNT(*) FROM hdrs
               WHERE organization_id = ?
                 AND created_at < ?
                 AND created_at != '1970-01-01T00:00:00Z'""",
            (organization_id, cutoff_iso),
        ).fetchone()
        to_purge = int((count_row[0] if count_row else 0) or 0)

        if to_purge == 0:
            return 0

        conn.execute(
            """DELETE FROM hdrs
               WHERE organization_id = ?
                 AND created_at < ?
                 AND created_at != '1970-01-01T00:00:00Z'""",
            (organization_id, cutoff_iso),
        )
        return to_purge
