"""Admin metrics surface — auth via shared secret HMAC-compared token.

Designed for operator dashboards (Grafana / spreadsheet / cron jobs) during
beta and beyond. Returns ONLY aggregate counts; never returns prompts,
responses, or any PII.
"""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core import config as runtime_config
from app.dependencies import database_dependency
from app.domain.admin.models import BetaFeed, BetaMetrics
from app.domain.admin.services import AdminMetricsService

router = APIRouter(prefix="/admin", tags=["admin"])

# stateless service singleton — safe to share across requests
_metrics_svc = AdminMetricsService()


def _verify_admin_token(provided: str | None) -> None:
    """Constant-time comparison vs HEILLON_ADMIN_TOKEN env var."""
    settings = runtime_config.get_settings()
    expected = (settings.HEILLON_ADMIN_TOKEN or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API disabled (no HEILLON_ADMIN_TOKEN configured)",
        )
    if not provided or not provided.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Heillon-Admin-Token header",
            headers={"WWW-Authenticate": "AdminToken"},
        )
    if not hmac.compare_digest(provided.strip(), expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "AdminToken"},
        )


def admin_auth(
    x_heillon_admin_token: Annotated[
        str | None, Header(alias="X-Heillon-Admin-Token")
    ] = None,
) -> None:
    """Dependency: validates admin token; raises 401 on failure."""
    _verify_admin_token(x_heillon_admin_token)


@router.get(
    "/beta-metrics",
    dependencies=[Depends(admin_auth)],
    response_model=BetaMetrics,
)
def beta_metrics(conn=Depends(database_dependency)) -> BetaMetrics:
    """Aggregate snapshot of beta adoption (orgs/users/api_keys/hdrs)."""
    return _metrics_svc.beta_metrics(conn)


@router.get(
    "/beta-feed",
    dependencies=[Depends(admin_auth)],
    response_model=BetaFeed,
)
def beta_feed(
    limit: int = 20,
    conn=Depends(database_dependency),
) -> BetaFeed:
    """Recent sanitized HDR activity feed (no prompt/response content)."""
    return _metrics_svc.beta_feed(conn, limit=limit)
