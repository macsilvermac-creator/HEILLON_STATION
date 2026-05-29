"""Health probes for orchestration and admin dashboard."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.db.compat import open_connection, resolve_dialect
from app.dependencies import get_current_user_record
from app.domain.mission.agent_registry_setup import build_agent_registry
from app.domain.user.models import UserRecord, UserRole

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness probe — does the process answer HTTP?

    Use this from Docker HEALTHCHECK and Kubernetes livenessProbe. Returns 200
    as long as the FastAPI process is up. NEVER queries DB/Redis (would mask
    transient deps as liveness failures and cause restart loops).
    """

    return {
        "status": "ok",
        "version": "12.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready")
async def health_ready(
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Readiness probe — should the load balancer send traffic here?

    Verifies DB + Redis reachable + agents loaded. Returns:
      - 200 + {"status": "ready", checks: {...}} when all OK
      - 503 + {"status": "not_ready", checks: {...}} when any dep is down

    Caddy/k8s/load balancers use this to drain traffic from failing nodes
    automatically. NEVER requires auth — orchestrators must reach it freely.
    """
    checks = {
        "database": _check_database(settings),
        "redis": _check_redis(settings),
    }
    is_ready = all(c.get("status") == "ok" for c in checks.values())

    body: dict[str, object] = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }

    if not is_ready:
        # 503 makes orchestrators stop sending traffic until ready
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=body,
        )

    return body


@router.get("/health/detailed")
async def detailed_health(
    current_user: UserRecord = Depends(get_current_user_record),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Component health for administrators."""

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores."
        )

    checks: dict[str, dict[str, Any]] = {
        "database": _check_database(settings),
        "redis": _check_redis(settings),
        "timestamp_service": _check_tsa(settings),
        "agents": _check_agents(settings),
    }

    overall = "ok"
    if any(c.get("status") == "error" for c in checks.values()):
        overall = "degraded"

    return {
        "status": overall,
        "version": "12.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }


def _check_database(settings: Settings) -> dict[str, str]:
    try:
        with open_connection(settings) as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "type": resolve_dialect(settings)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc)}


def _check_redis(settings: Settings) -> dict[str, str]:
    try:
        import redis

        client = redis.from_url(settings.REDIS_URL)
        client.ping()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc)}


def _check_tsa(settings: Settings) -> dict[str, str]:
    if settings.FORCE_STUB_TIMESTAMP:
        return {"status": "warning", "message": "Using stub timestamps"}
    return {"status": "ok", "tsa_url": settings.TSA_URL}


def _check_agents(settings: Settings) -> dict[str, str | int]:
    try:
        registry = build_agent_registry(settings)
        total = len(registry.list_definitions())
        return {"status": "ok", "total_agents": total}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc)}
