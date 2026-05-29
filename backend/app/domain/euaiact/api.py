"""EU AI Act + eIDAS 2.0 + ISO 27001 HTTP API — Fase 17.

Endpoints:
  POST   /euaiact/tech-docs                         — create Annex IV doc
  GET    /euaiact/tech-docs                         — list tech docs
  GET    /euaiact/tech-docs/{doc_id}                — get doc
  POST   /euaiact/tech-docs/{doc_id}/activate       — activate doc
  POST   /euaiact/tech-docs/{doc_id}/conformity     — mark conformity assessed

  POST   /euaiact/dpia                              — create DPIA
  GET    /euaiact/dpia                              — list DPIAs
  GET    /euaiact/dpia/{dpia_id}                    — get DPIA
  POST   /euaiact/dpia/{dpia_id}/approve            — approve DPIA (admin)

  POST   /euaiact/qes                               — record QES signature
  GET    /euaiact/qes                               — list QES records
  GET    /euaiact/qes/{qes_id}                      — get QES record

  POST   /euaiact/isms/risks                        — register ISMS risk
  GET    /euaiact/isms/risks                        — list ISMS risks
  GET    /euaiact/isms/risks/{risk_id}              — get risk
  POST   /euaiact/isms/risks/{risk_id}/close        — close risk (admin)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.euaiact.services import (
    DPIAService,
    EIDASQESService,
    EUAITechDocService,
    ISMSRiskService,
)
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/euaiact", tags=["euaiact"])

_techdoc_svc = EUAITechDocService()
_dpia_svc = DPIAService()
_qes_svc = EIDASQESService()
_isms_svc = ISMSRiskService()


# ── Auth helpers ──────────────────────────────────────────────────────────────


def _require_admin(
    current_user: UserRecord = Depends(get_current_user_record),
) -> UserRecord:
    from app.domain.user.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only.")
    return current_user


# ── Schemas ────────────────────────────────────────────────────────────────────


class CreateTechDocRequest(BaseModel):
    system_name: str = Field(..., min_length=1, max_length=200)
    system_version: str = Field(default="1.0", max_length=50)
    system_description: str = Field(default="", max_length=4000)
    risk_category: str = Field(
        default="high", pattern="^(unacceptable|high|limited|minimal)$"
    )
    annex_iii_category: str | None = None
    intended_purpose: str = Field(default="", max_length=4000)
    general_description: dict | None = None
    training_data: dict | None = None
    testing_validation: dict | None = None
    performance_metrics: dict | None = None
    human_oversight: dict | None = None
    cybersecurity: dict | None = None


class ConformityRequest(BaseModel):
    notified_body: str | None = Field(default=None, max_length=200)


class CreateDPIARequest(BaseModel):
    processing_name: str = Field(..., min_length=1, max_length=300)
    processing_purpose: str = Field(default="", max_length=4000)
    legal_basis: str = Field(
        default="legitimate_interest",
        pattern="^(consent|contract|legal_obligation|vital_interests|public_task|legitimate_interest)$",
    )
    data_categories: list[str] = Field(default_factory=list)
    data_subjects: list[str] = Field(default_factory=list)
    necessity_assessment: str = Field(default="", max_length=8000)
    proportionality_check: str = Field(default="", max_length=8000)
    risks_identified: list[dict] = Field(default_factory=list)
    mitigations: list[dict] = Field(default_factory=list)


class RecordQESRequest(BaseModel):
    document_type: str = Field(..., min_length=1, max_length=100)
    document_ref: str = Field(..., min_length=1, max_length=200)
    document_hash: str = Field(..., min_length=64, max_length=64)
    signatory_name: str = Field(..., min_length=1, max_length=200)
    signatory_email: str = Field(..., max_length=200)
    qtsp_provider: str = Field(default="", max_length=200)
    qtsp_country: str = Field(default="EU", max_length=10)
    signature_format: str = Field(
        default="PAdES-LTA", pattern="^(PAdES-LTA|CAdES-LTA|XAdES-LTA)$"
    )
    signature_level: str = Field(default="QES", pattern="^(QES|AES|SES)$")
    eudi_wallet_used: bool = False
    eudi_pid_verified: bool = False
    tsa_provider: str | None = None


class RegisterISMSRiskRequest(BaseModel):
    asset: str = Field(..., min_length=1, max_length=300)
    threat: str = Field(..., min_length=1, max_length=1000)
    vulnerability: str = Field(default="", max_length=1000)
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)
    control_ref: str | None = Field(default=None, max_length=50)
    control_description: str = Field(default="", max_length=2000)
    treatment_option: str = Field(
        default="mitigate", pattern="^(mitigate|accept|transfer|avoid)$"
    )
    residual_risk: str | None = Field(default=None, max_length=1000)


# ── EU AI Act Tech Docs ────────────────────────────────────────────────────────


@router.post("/tech-docs", status_code=status.HTTP_201_CREATED)
def create_tech_doc(
    body: CreateTechDocRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    doc_id = _techdoc_svc.create_doc(
        conn,
        organization_id=current_user.organization_id or "org_default",
        system_name=body.system_name,
        system_version=body.system_version,
        system_description=body.system_description,
        risk_category=body.risk_category,
        annex_iii_category=body.annex_iii_category,
        intended_purpose=body.intended_purpose,
        general_description=body.general_description,
        training_data=body.training_data,
        testing_validation=body.testing_validation,
        performance_metrics=body.performance_metrics,
        human_oversight=body.human_oversight,
        cybersecurity=body.cybersecurity,
        created_by=current_user.user_id,
    )
    return {"doc_id": doc_id, "status": "draft"}


@router.get("/tech-docs")
def list_tech_docs(
    status_filter: str | None = None,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _techdoc_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        status=status_filter,
    )


@router.get("/tech-docs/{doc_id}")
def get_tech_doc(
    doc_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    doc = _techdoc_svc.get(conn, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Technical document not found.")
    if doc.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    doc["_summary"] = _techdoc_svc.generate_summary_text(doc)
    return doc


@router.post("/tech-docs/{doc_id}/activate")
def activate_tech_doc(
    doc_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    doc = _techdoc_svc.get(conn, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Technical document not found.")
    _techdoc_svc.activate(conn, doc_id)
    return {"doc_id": doc_id, "status": "active"}


@router.post("/tech-docs/{doc_id}/conformity")
def mark_tech_doc_conformity(
    doc_id: str,
    body: ConformityRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    doc = _techdoc_svc.get(conn, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Technical document not found.")
    _techdoc_svc.mark_conformity(conn, doc_id, notified_body=body.notified_body)
    return {"doc_id": doc_id, "conformity_assessed": "true"}


# ── DPIA ──────────────────────────────────────────────────────────────────────


@router.post("/dpia", status_code=status.HTTP_201_CREATED)
def create_dpia(
    body: CreateDPIARequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    dpia_id = _dpia_svc.create_dpia(
        conn,
        organization_id=current_user.organization_id or "org_default",
        processing_name=body.processing_name,
        processing_purpose=body.processing_purpose,
        legal_basis=body.legal_basis,
        data_categories=body.data_categories,
        data_subjects=body.data_subjects,
        necessity_assessment=body.necessity_assessment,
        proportionality_check=body.proportionality_check,
        risks_identified=body.risks_identified,
        mitigations=body.mitigations,
        created_by=current_user.user_id,
    )
    return {"dpia_id": dpia_id}


@router.get("/dpia")
def list_dpias(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _dpia_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/dpia/{dpia_id}")
def get_dpia(
    dpia_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    record = _dpia_svc.get(conn, dpia_id)
    if record is None:
        raise HTTPException(status_code=404, detail="DPIA not found.")
    if record.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return record


@router.post("/dpia/{dpia_id}/approve")
def approve_dpia(
    dpia_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, str]:
    record = _dpia_svc.get(conn, dpia_id)
    if record is None:
        raise HTTPException(status_code=404, detail="DPIA not found.")
    _dpia_svc.approve(conn, dpia_id, approved_by=current_user.user_id)
    return {"dpia_id": dpia_id, "status": "approved"}


# ── eIDAS QES ─────────────────────────────────────────────────────────────────


@router.post("/qes", status_code=status.HTTP_201_CREATED)
def record_qes(
    body: RecordQESRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    qes_id = _qes_svc.record_qes(
        conn,
        organization_id=current_user.organization_id or "org_default",
        document_type=body.document_type,
        document_ref=body.document_ref,
        document_hash=body.document_hash,
        signatory_name=body.signatory_name,
        signatory_email=body.signatory_email,
        qtsp_provider=body.qtsp_provider,
        qtsp_country=body.qtsp_country,
        signature_format=body.signature_format,
        signature_level=body.signature_level,
        eudi_wallet_used=body.eudi_wallet_used,
        eudi_pid_verified=body.eudi_pid_verified,
        tsa_provider=body.tsa_provider,
    )
    return {"qes_id": qes_id}


@router.get("/qes")
def list_qes(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _qes_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/qes/{qes_id}")
def get_qes(
    qes_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    record = _qes_svc.get(conn, qes_id)
    if record is None:
        raise HTTPException(status_code=404, detail="QES record not found.")
    if record.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return record


# ── ISO 27001 ISMS Risk ───────────────────────────────────────────────────────


@router.post("/isms/risks", status_code=status.HTTP_201_CREATED)
def register_isms_risk(
    body: RegisterISMSRiskRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    result = _isms_svc.register_risk(
        conn,
        organization_id=current_user.organization_id or "org_default",
        asset=body.asset,
        threat=body.threat,
        vulnerability=body.vulnerability,
        likelihood=body.likelihood,
        impact=body.impact,
        control_ref=body.control_ref,
        control_description=body.control_description,
        treatment_option=body.treatment_option,
        residual_risk=body.residual_risk,
        risk_owner=current_user.user_id,
    )
    return result


@router.get("/isms/risks")
def list_isms_risks(
    risk_level: str | None = None,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _isms_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        risk_level=risk_level,
        status=status_filter,
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/isms/risks/{risk_id}")
def get_isms_risk(
    risk_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    record = _isms_svc.get(conn, risk_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Risk not found.")
    if record.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return record


@router.post("/isms/risks/{risk_id}/close")
def close_isms_risk(
    risk_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, str]:
    record = _isms_svc.get(conn, risk_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Risk not found.")
    _isms_svc.close_risk(conn, risk_id)
    return {"risk_id": risk_id, "status": "closed"}
