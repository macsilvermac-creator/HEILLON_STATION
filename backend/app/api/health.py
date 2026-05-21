"""Health probes for orchestration and admin dashboard."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.db.compat import open_connection, resolve_dialect
from app.dependencies import get_current_user_record
from app.domain.mission.agent_registry_setup import build_agent_registry
from app.domain.user.models import UserRecord, UserRole

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness probe."""

    return {
        "status": "ok",
        "version": "12.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health(
    current_user: UserRecord = Depends(get_current_user_record),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Component health for administrators."""

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores.")

    checks = {
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
