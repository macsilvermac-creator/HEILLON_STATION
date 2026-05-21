"""HTTP surface for EASY agent cognition sovereignty (per-tenant model routing)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import get_current_user_record
from app.domain.mission.agent_config_models import AgentConfig, AgentConfigTestResponse, AgentConfigUpdate
from app.domain.mission.agent_config_service import AgentConfigService
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/agent-config", tags=["agent-config"])


def get_agent_config_runtime(request: Request) -> AgentConfigService:
    svc = getattr(request.app.state, "agent_config_service", None)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Serviço de configuração de agentes indisponível.",
        )
    return svc


@router.get("/", response_model=list[AgentConfig])
def list_agent_configs(
    actor: Annotated[UserRecord, Depends(get_current_user_record)],
    config_service: Annotated[AgentConfigService, Depends(get_agent_config_runtime)],
) -> list[AgentConfig]:
    """Enumerate configured cognition backends for the operator organization."""

    return config_service.list_configs(actor.organization_id)


@router.get("/{agent_id}", response_model=AgentConfig)
def get_agent_config_route(
    agent_id: str,
    actor: Annotated[UserRecord, Depends(get_current_user_record)],
    config_service: Annotated[AgentConfigService, Depends(get_agent_config_runtime)],
) -> AgentConfig:
    """Hydrate sanitized configuration projections (secrets never egress)."""

    return config_service.get_config(agent_id, actor.organization_id)


@router.put("/{agent_id}", response_model=AgentConfig)
def put_agent_config_route(
    agent_id: str,
    body: AgentConfigUpdate,
    actor: Annotated[UserRecord, Depends(get_current_user_record)],
    config_service: Annotated[AgentConfigService, Depends(get_agent_config_runtime)],
) -> AgentConfig:
    """Upsert cognition routing artefacts for EASY workers."""

    try:
        return config_service.update_config(agent_id, actor.organization_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{agent_id}/test", response_model=AgentConfigTestResponse)
def probe_agent_configuration(
    agent_id: str,
    actor: Annotated[UserRecord, Depends(get_current_user_record)],
    config_service: Annotated[AgentConfigService, Depends(get_agent_config_runtime)],
) -> AgentConfigTestResponse:
    """Lightweight inference ping using the persisted routing profile."""

    raw = config_service.run_smoke_probe(agent_id, actor.organization_id)
    okay = raw.get("status") == "ok"
    return AgentConfigTestResponse(
        status=str(raw.get("status") or "error"),
        execution_status=str(raw.get("execution_status") or "") if okay else None,
        cognitive_excerpt=str(raw.get("cognitive_excerpt") or "") if okay else None,
        detail=str(raw.get("detail") or "") if not okay else None,
    )
