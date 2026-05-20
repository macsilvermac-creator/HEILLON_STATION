"""Handset-oriented judiciary rails (approval queues, KPI tiles, push bridge)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core import config as runtime_config
from app.dependencies import database_dependency
from app.domain.mission.agent_config_api import resolve_registered_operator
from app.domain.mission.models import MissionStatus
from app.domain.mission.repository import MissionRepository
from app.domain.mobile.models import (
    MobileQuickStats,
    PendingApprovalsEnvelope,
    PushTokenRegisterRequest,
    PushTokenRegisterResponse,
)
from app.domain.mobile.repository import MobileBridgeRepository
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/mobile", tags=["mobile"])

_missions = MissionRepository()
_bridge = MobileBridgeRepository()


def _tenant_org(user: UserRecord) -> str | None:
    cfg = runtime_config.get_settings()
    return user.organization_id if cfg.MISSION_ROUTES_REQUIRE_AUTH else None


@router.get("/pending-approvals", response_model=PendingApprovalsEnvelope)
def mobile_pending_approvals(
    actor: Annotated[UserRecord, Depends(resolve_registered_operator)],
    conn=Depends(database_dependency),
) -> PendingApprovalsEnvelope:
    """Mission dossiers still awaiting EASY human affirmation."""

    oid = _tenant_org(actor)

    total, missions = _missions.diary_query(
        conn,
        skip=0,
        limit=100,
        status_filter=MissionStatus.PENDING.value,
        organization_id=oid,
    )
    return PendingApprovalsEnvelope(total=total, missions=missions)


@router.get("/quick-stats", response_model=MobileQuickStats)
def mobile_quick_stats(
    actor: Annotated[UserRecord, Depends(resolve_registered_operator)],
    conn=Depends(database_dependency),
) -> MobileQuickStats:
    """Ultra-compact tiles for handset dashboards."""

    oid = _tenant_org(actor)

    totals = _missions.aggregate_stats(conn, organization_id=oid)
    pend_total, _ = _missions.diary_query(
        conn,
        skip=0,
        limit=1,
        status_filter=MissionStatus.PENDING.value,
        organization_id=oid,
    )

    return MobileQuickStats(
        total_missions=int(totals["total_missions"]),
        pending_approvals=int(pend_total),
        completed=int(totals["completed"]),
        failed=int(totals["failed"]),
    )


@router.post("/push-token", response_model=PushTokenRegisterResponse)
def register_push_subscription(
    body: PushTokenRegisterRequest,
    actor: Annotated[UserRecord, Depends(resolve_registered_operator)],
    conn=Depends(database_dependency),
) -> PushTokenRegisterResponse:
    """Accept Web Push subscriptions until dedicated notification dispatcher exists."""

    try:
        _bridge.upsert_push_token(conn, user_id=actor.user_id, subscription_json=body.subscription_json)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON inválido.") from exc
    except Exception as exc:  # noqa: BLE001 — defensive guardrail for SQLite oddities.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao persistir subscrição push.",
        ) from exc

    return PushTokenRegisterResponse()
