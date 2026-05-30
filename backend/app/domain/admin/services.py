"""Domain service for the admin metrics bounded context.

Assembles aggregate snapshots from AdminMetricsRepository and returns typed
models. Keeps the router thin (auth + delegation only) and free of SQL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.admin.models import (
    ActivationFunnel,
    ApiKeyMetrics,
    BetaFeed,
    BetaMetrics,
    DailyCount,
    FeedEvent,
    HdrMetrics,
    OrganizationMetrics,
    UserMetrics,
)
from app.domain.admin.repository import AdminMetricsRepository


class AdminMetricsService:
    """Builds beta adoption snapshots and activity feeds."""

    def __init__(self, repository: AdminMetricsRepository | None = None) -> None:
        self._repo = repository or AdminMetricsRepository()

    def beta_metrics(self, conn: Any) -> BetaMetrics:
        now = datetime.now(timezone.utc)
        last_24h = (now - timedelta(hours=24)).isoformat()
        last_7d = (now - timedelta(days=7)).isoformat()
        last_14d = (now - timedelta(days=14)).isoformat()

        by_tier = self._repo.organizations_by_tier(conn)
        api_total, api_active = self._repo.count_api_keys(conn)
        org_total = sum(by_tier.values())

        return BetaMetrics(
            snapshot_at=now.isoformat(),
            organizations=OrganizationMetrics(
                total=sum(by_tier.values()),
                by_tier=by_tier,
            ),
            users=UserMetrics(
                total=self._repo.count_users(conn),
                active_last_7d=self._repo.count_active_users_since(conn, last_7d),
            ),
            api_keys=ApiKeyMetrics(
                active=api_active,
                revoked=api_total - api_active,
                total=api_total,
            ),
            hdrs=HdrMetrics(
                total=self._repo.count_hdrs(conn),
                last_24h=self._repo.count_hdrs_since(conn, last_24h),
                last_7d=self._repo.count_hdrs_since(conn, last_7d),
                by_type=self._repo.hdrs_by_type(conn),
                latest_at=self._repo.latest_hdr_at(conn),
            ),
            daily_hdrs=[
                DailyCount(**row)
                for row in self._repo.hdrs_daily_since(conn, last_14d)
            ],
            funnel=ActivationFunnel(
                organizations=org_total,
                with_api_key=self._repo.organizations_with_api_key(conn),
                with_hdr=self._repo.organizations_with_hdr(conn),
                active_7d=self._repo.active_orgs_since(conn, last_7d),
            ),
        )

    def beta_feed(self, conn: Any, *, limit: int) -> BetaFeed:
        limit = max(1, min(limit, 100))
        events = [FeedEvent(**row) for row in self._repo.recent_hdrs(conn, limit=limit)]
        return BetaFeed(events=events, count=len(events))
