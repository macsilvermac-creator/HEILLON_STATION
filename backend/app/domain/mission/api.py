"""EASY mission planning, diary, approval, and execution endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core import config as runtime_config
from app.dependencies import MissionActor, database_dependency, resolve_mission_actor
from app.domain.hdr.repository import HDRRepository

from app.domain.mission.models import (
    MissionDiaryResponse,
    MissionExecutionResult,
    MissionPlan,
    MissionStats,
    MissionStatus,
    PlanMissionRequest,
    AgentFrequency,
)
from app.domain.mission.repository import MissionRepository
from app.domain.mission.services import OrchestrationEngine

router = APIRouter(prefix="/mission", tags=["mission"])

_hdr_repository_singleton = HDRRepository()

_mission_repository_singleton = MissionRepository()


def tenant_organization_scope(actor: MissionActor) -> str | None:
    """Honor multi-tenancy gates only when mission authentication is mandated."""

    return actor.organization_id if runtime_config.get_settings().MISSION_ROUTES_REQUIRE_AUTH else None



def mission_repository_dependency() -> MissionRepository:
    """Singleton repository for Depends wiring."""

    return _mission_repository_singleton


def get_orchestration(request: Request) -> OrchestrationEngine:
    """Resolve orchestrator bound during application lifespan."""

    engine = getattr(request.app.state, "orchestration_engine", None)
    if engine is None:
        msg = "Orchestration engine not initialized."
        raise RuntimeError(msg)
    return engine


@router.post("/plan", response_model=MissionPlan)
def plan_mission_endpoint(
    body: PlanMissionRequest,
    actor: MissionActor = Depends(resolve_mission_actor),
    conn=Depends(database_dependency),
    orchestrator: OrchestrationEngine = Depends(get_orchestration),
    mission_repo: MissionRepository = Depends(mission_repository_dependency),
) -> MissionPlan:
    """Materialize EASY mission dossier sans execution."""

    plan = orchestrator.plan_mission(
        body.description,
        body.authorized_agents,
        organization_id=actor.organization_id,
    )
    mission_repo.persist_plan(conn, plan)
    return plan


@router.get("/diary/stats", response_model=MissionStats)
def diary_stats_endpoint(
    actor: MissionActor = Depends(resolve_mission_actor),
    conn=Depends(database_dependency),
    mission_repo: MissionRepository = Depends(mission_repository_dependency),
) -> MissionStats:
    """Aggregate judiciary dashboard metrics."""

    raw = mission_repo.aggregate_stats(conn, organization_id=tenant_organization_scope(actor))

    freq = [
        AgentFrequency(agent_id=item["agent_id"], count=item["count"])
        for item in raw.get("most_used_agents", [])
    ]

    return MissionStats(
        total_missions=raw["total_missions"],
        completed=raw["completed"],
        failed=raw["failed"],
        blocked_by_normative=raw["blocked_by_normative"],
        total_hdrs_generated=raw["total_hdrs_generated"],
        avg_execution_time_ms=raw["avg_execution_time_ms"],
        most_used_agents=freq,
    )


@router.get("/diary", response_model=MissionDiaryResponse)
def diary_endpoint(
    actor: MissionActor = Depends(resolve_mission_actor),
    conn=Depends(database_dependency),
    mission_repo: MissionRepository = Depends(mission_repository_dependency),
    skip: int = 0,
    limit: int = 20,
    status: MissionStatus | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
) -> MissionDiaryResponse:
    """Diário de bordo — filtros plus pagination."""

    if skip < 0 or limit <= 0 or limit > 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pagination window.")

    stat_value = status.value if status else None
    total, missions = mission_repo.diary_query(
        conn,
        skip=skip,
        limit=limit,
        status_filter=stat_value,
        date_from=date_from,
        date_to=date_to,
        search=search,
        organization_id=tenant_organization_scope(actor),
    )
    return MissionDiaryResponse(total=total, skip=skip, limit=limit, missions=missions)


@router.post("/{mission_id}/approve", response_model=MissionPlan)
def approve_mission_endpoint(
    mission_id: str,
    actor: MissionActor = Depends(resolve_mission_actor),
    conn=Depends(database_dependency),
    mission_repo: MissionRepository = Depends(mission_repository_dependency),
) -> MissionPlan:
    """Promote dossier awaiting human EASY approval gates."""

    plan = mission_repo.fetch_plan(conn, mission_id, organization_id=tenant_organization_scope(actor))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not archived.")

    if not plan.normative_result or not plan.normative_result.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Corpus Normativo blockage.")

    if plan.status != MissionStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mission not awaiting approval.")

    plan.status = MissionStatus.APPROVED
    plan.approved_at = datetime.now(timezone.utc)
    mission_repo.persist_plan(conn, plan)
    return plan


@router.post("/{mission_id}/reject", response_model=MissionPlan)
def reject_mission_endpoint(
    mission_id: str,
    actor: MissionActor = Depends(resolve_mission_actor),
    conn=Depends(database_dependency),
    mission_repo: MissionRepository = Depends(mission_repository_dependency),
) -> MissionPlan:
    """Mark dossiers as judiciary-rejected prior to EASY execution."""

    plan = mission_repo.fetch_plan(conn, mission_id, organization_id=tenant_organization_scope(actor))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not archived.")

    if plan.status != MissionStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mission not awaiting approval.")

    plan.status = MissionStatus.REJECTED
    mission_repo.persist_plan(conn, plan)
    return plan


@router.post("/{mission_id}/execute", response_model=MissionExecutionResult)
async def execute_mission_endpoint(
    mission_id: str,
    actor: MissionActor = Depends(resolve_mission_actor),
    conn=Depends(database_dependency),
    orchestrator: OrchestrationEngine = Depends(get_orchestration),
    mission_repo: MissionRepository = Depends(mission_repository_dependency),
) -> MissionExecutionResult:
    """Execute approved EASY DAG minting cryptographic HDR artefacts."""

    plan = mission_repo.fetch_plan(conn, mission_id, organization_id=tenant_organization_scope(actor))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not archived.")

    if plan.status != MissionStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mission not approved.")

    if not plan.normative_result or not plan.normative_result.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mission normatively barred.")

    try:
        hdrs = await orchestrator.execute_mission(plan, mission_id=mission_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    for hdr in hdrs:
        _hdr_repository_singleton.insert(conn, hdr, organization_id=plan.organization_id)

    plan.status = MissionStatus.COMPLETED
    now = datetime.now(timezone.utc)
    plan.executed_at = now
    plan.completed_at = now
    mission_repo.persist_plan(conn, plan)

    chain_root = hdrs[0].hdr_id if hdrs else None
    chain_tail = hdrs[-1].hdr_id if hdrs else None

    return MissionExecutionResult(
        mission_id=mission_id,
        status=plan.status,
        hdrs=hdrs,
        chain_root=chain_root,
        chain_tail=chain_tail,
        total_hdrs=len(hdrs),
    )


@router.get("/", response_model=list[MissionPlan])
def list_missions_endpoint(
    actor: MissionActor = Depends(resolve_mission_actor),
    conn=Depends(database_dependency),
    mission_repo: MissionRepository = Depends(mission_repository_dependency),
    skip: int = 0,
    limit: int = 20,
) -> list[MissionPlan]:
    """Enumerate missions with cursored pagination safeguards."""

    if skip < 0 or limit <= 0 or limit > 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pagination window.")
    return mission_repo.list_plans(
        conn,
        skip=skip,
        limit=limit,
        organization_id=tenant_organization_scope(actor),
    )


@router.get("/{mission_id}", response_model=MissionPlan)
def get_mission_endpoint(
    mission_id: str,
    actor: MissionActor = Depends(resolve_mission_actor),
    conn=Depends(database_dependency),
    mission_repo: MissionRepository = Depends(mission_repository_dependency),
) -> MissionPlan:
    """Return immutable archival snapshot for judiciary review."""

    plan = mission_repo.fetch_plan(conn, mission_id, organization_id=tenant_organization_scope(actor))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not archived.")
    return plan
