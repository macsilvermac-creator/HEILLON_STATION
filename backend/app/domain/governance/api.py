"""Governance domain HTTP API — CNJ 615/2025 + OAB Rec. 001/2024.

Endpoints:
  POST   /governance/risk                           — create risk classification
  GET    /governance/risk                           — list risk classifications (auth)
  GET    /governance/risk/{classification_id}       — get classification
  DELETE /governance/risk/{classification_id}       — retire classification (admin)

  POST   /governance/decisions                      — log AI decision
  GET    /governance/decisions                      — list decisions (auth)
  GET    /governance/decisions/{decision_id}        — get decision
  POST   /governance/decisions/{decision_id}/review — human review (auth)

  GET    /governance/gates                          — list pending gates (auth)
  GET    /governance/gates/{gate_id}                — get gate detail
  POST   /governance/gates/{gate_id}/resolve        — resolve gate (auth, required role)

  POST   /governance/disclosures                    — create OAB disclosure (auth)
  GET    /governance/disclosures                    — list disclosures (auth)
  GET    /governance/disclosures/{disclosure_id}    — get disclosure
  POST   /governance/disclosures/{disclosure_id}/ack — client acknowledgement
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.governance.models import GateStatus
from app.domain.governance.services import (
    AIDecisionService,
    AIDisclosureService,
    AIRiskService,
    HumanGateService,
)
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/governance", tags=["governance"])

_risk_svc = AIRiskService()
_decision_svc = AIDecisionService()
_gate_svc = HumanGateService()
_disclosure_svc = AIDisclosureService()


# ── Helpers ────────────────────────────────────────────────────────────────────


def _require_admin(
    current_user: UserRecord = Depends(get_current_user_record),
) -> UserRecord:
    from app.domain.user.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only.")
    return current_user


def _org_id(user: UserRecord) -> str:
    return user.organization_id or "org_default"


# ── Schemas ────────────────────────────────────────────────────────────────────


class ClassifyRequest(BaseModel):
    system_name: str = Field(..., min_length=1, max_length=200)
    system_version: str = Field(default="1.0", max_length=50)
    system_description: str = Field(default="", max_length=2000)
    risk_level: str = Field(
        ...,
        description="low | medium | high | prohibited",
        pattern="^(low|medium|high|prohibited)$",
    )
    risk_justification: str = Field(default="", max_length=4000)
    impact_areas: list[str] = Field(default_factory=list)
    regulatory_refs: list[str] = Field(default_factory=list)


class LogDecisionRequest(BaseModel):
    decision_type: str = Field(
        ..., description="analysis | recommendation | classification | generation"
    )
    decision_summary: str = Field(default="", max_length=4000)
    ai_model: str = Field(default="", max_length=200)
    ai_provider: str = Field(default="", max_length=200)
    hdr_id: str | None = None
    mission_id: str | None = None
    classification_id: str | None = None
    risk_level: str = Field(
        default="low",
        description="low | medium | high | prohibited",
        pattern="^(low|medium|high|prohibited)$",
    )


class ReviewDecisionRequest(BaseModel):
    human_decision: str = Field(..., description="approved | rejected | modified")
    notes: str = Field(default="", max_length=4000)


class ResolveGateRequest(BaseModel):
    status: str = Field(..., description="approved | rejected")
    notes: str = Field(default="", max_length=4000)


class CreateDisclosureRequest(BaseModel):
    client_identifier: str = Field(..., min_length=1, max_length=500)
    ai_systems_used: list[str] = Field(default_factory=list)
    mission_ids: list[str] = Field(default_factory=list)
    disclosure_text: str | None = Field(default=None, max_length=8000)
    method: str = Field(default="written", description="written | verbal | automated")
    channel: str = Field(default="email", description="email | portal | document")


# ── Risk classification routes ─────────────────────────────────────────────────


@router.post("/risk", status_code=status.HTTP_201_CREATED)
def create_risk_classification(
    body: ClassifyRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    cid = _risk_svc.classify(
        conn,
        organization_id=current_user.organization_id or "org_default",
        system_name=body.system_name,
        system_version=body.system_version,
        system_description=body.system_description,
        risk_level=body.risk_level,
        risk_justification=body.risk_justification,
        impact_areas=body.impact_areas,
        regulatory_refs=body.regulatory_refs,
        classified_by=current_user.user_id,
    )
    return {"classification_id": cid, "risk_level": body.risk_level}


@router.get("/risk")
def list_risk_classifications(
    status_filter: str = "active",
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _risk_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        status=status_filter or None,
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/risk/{classification_id}")
def get_risk_classification(
    classification_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    record = _risk_svc.get(conn, classification_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Classification not found.")
    if record.get("organization_id") != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    return record


@router.delete("/risk/{classification_id}")
def retire_risk_classification(
    classification_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, str]:
    record = _risk_svc.get(conn, classification_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Classification not found.")
    _risk_svc.retire(conn, classification_id)
    return {"classification_id": classification_id, "status": "retired"}


# ── Decision log routes ────────────────────────────────────────────────────────


@router.post("/decisions", status_code=status.HTTP_201_CREATED)
def log_ai_decision(
    body: LogDecisionRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    result = _decision_svc.log_decision(
        conn,
        organization_id=current_user.organization_id or "org_default",
        decision_type=body.decision_type,
        decision_summary=body.decision_summary,
        ai_model=body.ai_model,
        ai_provider=body.ai_provider,
        hdr_id=body.hdr_id,
        mission_id=body.mission_id,
        classification_id=body.classification_id,
        risk_level=body.risk_level,
    )
    return result


@router.get("/decisions")
def list_ai_decisions(
    pending_review: bool = False,
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _decision_svc.list_decisions(
        conn,
        current_user.organization_id or "org_default",
        human_reviewed=False if pending_review else None,
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/decisions/{decision_id}")
def get_ai_decision(
    decision_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    record = _decision_svc.get_decision(conn, decision_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Decision not found.")
    if record.get("organization_id") != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    return record


@router.post("/decisions/{decision_id}/review", status_code=status.HTTP_200_OK)
def review_ai_decision(
    decision_id: str,
    body: ReviewDecisionRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    record = _decision_svc.get_decision(conn, decision_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Decision not found.")
    if record.get("organization_id") != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    _decision_svc.review_decision(
        conn,
        decision_id,
        reviewer_id=current_user.user_id,
        human_decision=body.human_decision,
        notes=body.notes,
    )
    return {"status": "reviewed", "decision_id": decision_id}


# ── Human gate routes ──────────────────────────────────────────────────────────


@router.get("/gates")
def list_pending_gates(
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _gate_svc.list_pending(
        conn, current_user.organization_id or "org_default", limit=min(limit, 100)
    )


@router.get("/gates/{gate_id}")
def get_gate(
    gate_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    gate = _gate_svc.get_gate(conn, gate_id)
    if gate is None:
        raise HTTPException(status_code=404, detail="Gate not found.")
    if gate.get("organization_id") != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    return gate


@router.post("/gates/{gate_id}/resolve", status_code=status.HTTP_200_OK)
def resolve_gate(
    gate_id: str,
    body: ResolveGateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    gate = _gate_svc.get_gate(conn, gate_id)
    if gate is None:
        raise HTTPException(status_code=404, detail="Gate not found.")
    if gate.get("organization_id") != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    if gate.get("status") != GateStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Gate is already {gate.get('status')} — cannot re-resolve.",
        )
    _gate_svc.resolve(
        conn,
        gate_id,
        status=body.status,
        resolved_by=current_user.user_id,
        notes=body.notes,
    )
    return {"gate_id": gate_id, "status": body.status}


# ── Disclosure routes ──────────────────────────────────────────────────────────


@router.post("/disclosures", status_code=status.HTTP_201_CREATED)
def create_disclosure(
    body: CreateDisclosureRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    did = _disclosure_svc.create_disclosure(
        conn,
        organization_id=current_user.organization_id or "org_default",
        lawyer_id=current_user.user_id,
        client_identifier=body.client_identifier,
        ai_systems_used=body.ai_systems_used,
        mission_ids=body.mission_ids,
        disclosure_text=body.disclosure_text,
        method=body.method,
        channel=body.channel,
    )
    return {"disclosure_id": did}


@router.get("/disclosures")
def list_disclosures(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _disclosure_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/disclosures/{disclosure_id}")
def get_disclosure(
    disclosure_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    record = _disclosure_svc.get(conn, disclosure_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Disclosure not found.")
    if record.get("organization_id") != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    return record


@router.post("/disclosures/{disclosure_id}/ack", status_code=status.HTTP_200_OK)
def acknowledge_disclosure(
    disclosure_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    """Mark disclosure as acknowledged by client (no auth required — public endpoint)."""
    record = _disclosure_svc.get(conn, disclosure_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Disclosure not found.")
    _disclosure_svc.acknowledge(conn, disclosure_id)
    return {"disclosure_id": disclosure_id, "status": "acknowledged"}
