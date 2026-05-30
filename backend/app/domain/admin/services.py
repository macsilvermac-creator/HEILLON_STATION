"""Domain service for the admin metrics bounded context.

Assembles aggregate snapshots from AdminMetricsRepository and returns typed
models. Keeps the router thin (auth + delegation only) and free of SQL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.admin.models import (
    ApiKeyMetrics,
    BetaFeed,
    BetaMetrics,
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

        by_tier = self._repo.organizations_by_tier(conn)
        api_total, api_active = self._repo.count_api_keys(conn)

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
        )

    def beta_feed(self, conn: Any, *, limit: int) -> BetaFeed:
        limit = max(1, min(limit, 100))
        events = [FeedEvent(**row) for row in self._repo.recent_hdrs(conn, limit=limit)]
        return BetaFeed(events=events, count=len(events))
