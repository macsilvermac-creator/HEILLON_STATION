"""Admin metrics surface — auth via shared secret HMAC-compared token.

Designed for operator dashboards (Grafana / spreadsheet / cron jobs) during
beta and beyond. Returns ONLY aggregate counts; never returns prompts,
responses, or any PII.
"""

from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core import config as runtime_config
from app.dependencies import database_dependency

router = APIRouter(prefix="/admin", tags=["admin"])


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


@router.get("/beta-metrics", dependencies=[Depends(admin_auth)])
def beta_metrics(conn=Depends(database_dependency)) -> dict[str, Any]:
    """Aggregate snapshot of beta adoption.

    Returns:
        organizations: total + by tier
        users: total + active in last 7d
        api_keys: total active + revoked
        hdrs: total + 24h + 7d + by hdr_type
        latest_hdr_at: ISO timestamp of most recent HDR (proxy for liveness)
    """
    now = datetime.now(timezone.utc)
    last_24h = (now - timedelta(hours=24)).isoformat()
    last_7d = (now - timedelta(days=7)).isoformat()

    # Organizations by tier
    rows = conn.execute(
        "SELECT tier, COUNT(*) FROM organizations GROUP BY tier ORDER BY tier"
    ).fetchall()
    by_tier: dict[str, int] = {}
    total_orgs = 0
    for r in rows:
        tier = r[0] if not hasattr(r, "keys") else r["tier"]
        count = int(r[1] if not hasattr(r, "keys") else r[1])
        by_tier[str(tier)] = count
        total_orgs += count

    # Users
    users_total = _scalar(conn, "SELECT COUNT(*) FROM users")
    users_active_7d = _scalar(
        conn,
        """SELECT COUNT(DISTINCT u.user_id)
           FROM users u
           JOIN api_keys k ON k.user_id = u.user_id
           WHERE k.last_used_at >= ?""",
        (last_7d,),
    )

    # API keys
    api_keys_total = _scalar(conn, "SELECT COUNT(*) FROM api_keys")
    api_keys_active = _scalar(
        conn, "SELECT COUNT(*) FROM api_keys WHERE revoked_at IS NULL"
    )
    api_keys_revoked = api_keys_total - api_keys_active

    # HDRs
    hdrs_total = _scalar(conn, "SELECT COUNT(*) FROM hdrs")
    hdrs_24h = _scalar(
        conn, "SELECT COUNT(*) FROM hdrs WHERE created_at >= ?", (last_24h,)
    )
    hdrs_7d = _scalar(
        conn, "SELECT COUNT(*) FROM hdrs WHERE created_at >= ?", (last_7d,)
    )

    rows = conn.execute(
        "SELECT hdr_type, COUNT(*) FROM hdrs GROUP BY hdr_type ORDER BY hdr_type"
    ).fetchall()
    by_hdr_type: dict[str, int] = {}
    for r in rows:
        t = r[0] if not hasattr(r, "keys") else r["hdr_type"]
        c = int(r[1] if not hasattr(r, "keys") else r[1])
        by_hdr_type[str(t)] = c

    latest_row = conn.execute(
        "SELECT created_at FROM hdrs ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    latest_hdr_at = None
    if latest_row is not None:
        latest_hdr_at = (
            latest_row[0] if not hasattr(latest_row, "keys") else latest_row["created_at"]
        )

    return {
        "snapshot_at": now.isoformat(),
        "organizations": {
            "total": total_orgs,
            "by_tier": by_tier,
        },
        "users": {
            "total": users_total,
            "active_last_7d": users_active_7d,
        },
        "api_keys": {
            "active": api_keys_active,
            "revoked": api_keys_revoked,
            "total": api_keys_total,
        },
        "hdrs": {
            "total": hdrs_total,
            "last_24h": hdrs_24h,
            "last_7d": hdrs_7d,
            "by_type": by_hdr_type,
            "latest_at": latest_hdr_at,
        },
    }


@router.get("/beta-feed", dependencies=[Depends(admin_auth)])
def beta_feed(
    limit: int = 20,
    conn=Depends(database_dependency),
) -> dict[str, Any]:
    """Recent activity feed (sanitized — no prompt/response content).

    Returns the last N HDRs with: created_at, mission_id, hdr_type,
    organization_id, agent.model — useful for "is the beta breathing?" view.
    """
    limit = max(1, min(limit, 100))

    rows = conn.execute(
        """SELECT hdr_id, created_at, mission_id, hdr_type, organization_id
           FROM hdrs
           ORDER BY created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

    events: list[dict[str, Any]] = []
    for r in rows:

        def get(field: str, idx: int) -> Any:
            return r[field] if hasattr(r, "keys") else r[idx]

        events.append(
            {
                "hdr_id": str(get("hdr_id", 0)),
                "created_at": str(get("created_at", 1)),
                "mission_id": str(get("mission_id", 2)),
                "hdr_type": str(get("hdr_type", 3)),
                "organization_id": str(get("organization_id", 4)),
            }
        )

    return {"events": events, "count": len(events)}


def _scalar(conn: Any, sql: str, params: tuple = ()) -> int:
    """Run a single-value SELECT and return int (0 if NULL/missing)."""
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return 0
    val = row[0] if not hasattr(row, "keys") else row[0]
    return int(val or 0)
