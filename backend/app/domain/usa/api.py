"""USA regulatory compliance API — Fase 18.

Endpoints:
  POST   /usa/colorado/ai-records              — register AI system (Colorado AI Act)
  GET    /usa/colorado/ai-records              — list
  GET    /usa/colorado/ai-records/{id}         — get
  POST   /usa/colorado/ai-records/{id}/retire  — retire

  POST   /usa/ccpa/consent                     — record CCPA/CPRA consent
  GET    /usa/ccpa/consent                     — list
  GET    /usa/ccpa/consent/{id}                — get
  POST   /usa/ccpa/consent/{id}/withdraw       — withdraw

  POST   /usa/aba/compliance                   — log ABA Model Rules check
  GET    /usa/aba/compliance                   — list
  GET    /usa/aba/compliance/{id}              — get
  GET    /usa/aba/rules                        — ABA rules reference

  POST   /usa/nist/rmf                         — create NIST AI RMF record
  GET    /usa/nist/rmf                         — list
  GET    /usa/nist/rmf/{id}                    — get

  POST   /usa/esign/audit                      — log ESIGN event
  GET    /usa/esign/audit                      — list events (org)
  GET    /usa/esign/audit/document/{ref}       — events for a document
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.usa.services import (
    ABAComplianceService,
    CCPAConsentService,
    ColoradoAIService,
    ESIGNAuditService,
    NISTRMFService,
)
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/usa", tags=["usa"])

_colorado_svc = ColoradoAIService()
_ccpa_svc = CCPAConsentService()
_aba_svc = ABAComplianceService()
_nist_svc = NISTRMFService()
_esign_svc = ESIGNAuditService()


def _require_admin(
    current_user: UserRecord = Depends(get_current_user_record),
) -> UserRecord:
    from app.domain.user.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only.")
    return current_user


# ── Schemas ────────────────────────────────────────────────────────────────────


class ColoradoCreateRequest(BaseModel):
    ai_system_name: str = Field(..., min_length=1, max_length=200)
    ai_system_version: str = Field(default="1.0", max_length=50)
    developer_name: str = Field(default="", max_length=200)
    deployer_name: str = Field(default="", max_length=200)
    risk_tier: str = Field(default="limited", pattern="^(high|limited)$")
    high_risk_category: str | None = Field(
        default=None,
        pattern="^(employment|education|financial_services|housing|insurance|healthcare|criminal_justice|legal_services|other)$",
    )
    consequential_decision_desc: str = Field(default="", max_length=4000)
    impact_assessment_done: bool = False
    impact_assessment_date: str | None = None
    impact_assessment_ref: str = Field(default="", max_length=300)
    bias_audit_done: bool = False
    bias_audit_date: str | None = None
    bias_audit_provider: str = Field(default="", max_length=200)
    consumer_notification_text: str = Field(default="", max_length=4000)
    opt_out_mechanism: str = Field(default="", max_length=1000)
    appeal_process_available: bool = False
    monitoring_plan: str = Field(default="", max_length=4000)


class CCPACreateRequest(BaseModel):
    consumer_id: str = Field(..., min_length=1, max_length=200)
    consumer_email: str = Field(..., max_length=200)
    consumer_state: str = Field(default="CA", max_length=2)
    data_categories: list[str] = Field(default_factory=list)
    processing_purposes: list[str] = Field(default_factory=list)
    consent_type: str = Field(
        default="opt_in",
        pattern="^(opt_in|opt_out|do_not_sell|do_not_share|limit_sensitive)$",
    )
    sensitive_data_consent: bool = False
    automated_decision_consent: bool = False
    sale_of_personal_info_consent: bool = False
    sharing_for_cross_context: bool = False
    consent_text: str = Field(default="", max_length=4000)
    expires_at: str | None = None


class CCPAWithdrawRequest(BaseModel):
    reason: str = Field(default="", max_length=1000)


class ABALogRequest(BaseModel):
    matter_ref: str = Field(..., min_length=1, max_length=200)
    attorney_name: str = Field(default="", max_length=200)
    ai_tool_name: str = Field(default="", max_length=200)
    ai_tool_version: str = Field(default="", max_length=50)
    ai_tool_provider: str = Field(default="", max_length=200)
    rule_11_competence: bool = False
    rule_16_confidentiality: bool = False
    rule_34_fairness: bool = False
    rule_53_supervision: bool = False
    client_disclosure_made: bool = False
    state_bar: str = Field(default="CA", max_length=2)
    state_specific_rule_ref: str = Field(default="", max_length=100)
    state_specific_notes: str = Field(default="", max_length=2000)
    output_reviewed: bool = False
    review_notes: str = Field(default="", max_length=4000)


class NISTRMFCreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    ai_system_version: str = Field(default="1.0", max_length=50)
    govern_policies_defined: bool = False
    govern_roles_assigned: bool = False
    govern_risk_tolerance_set: bool = False
    govern_training_completed: bool = False
    govern_notes: str = Field(default="", max_length=2000)
    map_intended_use: str = Field(default="", max_length=2000)
    map_context_established: bool = False
    map_risks_identified: list[dict] = Field(default_factory=list)
    map_stakeholders_consulted: bool = False
    map_notes: str = Field(default="", max_length=2000)
    measure_metrics_defined: bool = False
    measure_testing_completed: bool = False
    measure_bias_evaluated: bool = False
    measure_performance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    measure_trustworthiness: int | None = Field(default=None, ge=1, le=5)
    measure_notes: str = Field(default="", max_length=2000)
    manage_risk_responses: list[dict] = Field(default_factory=list)
    manage_residual_risks: list[dict] = Field(default_factory=list)
    manage_monitoring_plan: str = Field(default="", max_length=4000)
    manage_incident_plan: str = Field(default="", max_length=4000)
    manage_notes: str = Field(default="", max_length=2000)
    profile_tier: str = Field(
        default="tier-2",
        pattern="^(tier-1|tier-2|tier-3|tier-4)$",
    )


class ESIGNEventRequest(BaseModel):
    event_type: str = Field(
        ...,
        pattern="^(document_created|invitation_sent|document_viewed|signed|declined|delegated|voided|completed)$",
    )
    actor_name: str = Field(default="", max_length=200)
    actor_email: str = Field(..., max_length=200)
    document_ref: str = Field(default="", max_length=300)
    document_hash: str | None = Field(default=None, min_length=64, max_length=64)
    sig_id: str | None = None
    event_sequence: int = Field(default=1, ge=1)
    event_data: dict = Field(default_factory=dict)


# ── Colorado AI Act ────────────────────────────────────────────────────────────


@router.post("/colorado/ai-records", status_code=status.HTTP_201_CREATED)
def create_colorado_record(
    body: ColoradoCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _colorado_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_name=body.ai_system_name,
        ai_system_version=body.ai_system_version,
        developer_name=body.developer_name,
        deployer_name=body.deployer_name,
        risk_tier=body.risk_tier,
        high_risk_category=body.high_risk_category,
        consequential_decision_desc=body.consequential_decision_desc,
        impact_assessment_done=body.impact_assessment_done,
        impact_assessment_date=body.impact_assessment_date,
        impact_assessment_ref=body.impact_assessment_ref,
        bias_audit_done=body.bias_audit_done,
        bias_audit_date=body.bias_audit_date,
        bias_audit_provider=body.bias_audit_provider,
        consumer_notification_text=body.consumer_notification_text,
        opt_out_mechanism=body.opt_out_mechanism,
        appeal_process_available=body.appeal_process_available,
        monitoring_plan=body.monitoring_plan,
        created_by=current_user.user_id,
    )


@router.get("/colorado/ai-records")
def list_colorado_records(
    risk_tier: str | None = None,
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _colorado_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        risk_tier=risk_tier,
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/colorado/ai-records/{record_id}")
def get_colorado_record(
    record_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _colorado_svc.get(conn, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.post("/colorado/ai-records/{record_id}/retire")
def retire_colorado_record(
    record_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, str]:
    rec = _colorado_svc.get(conn, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    _colorado_svc.retire(conn, record_id)
    return {"record_id": record_id, "status": "retired"}


# ── CCPA / CPRA ───────────────────────────────────────────────────────────────


@router.post("/ccpa/consent", status_code=status.HTTP_201_CREATED)
def create_ccpa_consent(
    body: CCPACreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    consent_id = _ccpa_svc.record_consent(
        conn,
        organization_id=current_user.organization_id or "org_default",
        consumer_id=body.consumer_id,
        consumer_email=body.consumer_email,
        consumer_state=body.consumer_state,
        data_categories=body.data_categories,
        processing_purposes=body.processing_purposes,
        consent_type=body.consent_type,
        sensitive_data_consent=body.sensitive_data_consent,
        automated_decision_consent=body.automated_decision_consent,
        sale_of_personal_info_consent=body.sale_of_personal_info_consent,
        sharing_for_cross_context=body.sharing_for_cross_context,
        consent_text=body.consent_text,
        expires_at=body.expires_at,
    )
    return {"consent_id": consent_id}


@router.get("/ccpa/consent")
def list_ccpa_consent(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _ccpa_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/ccpa/consent/{consent_id}")
def get_ccpa_consent(
    consent_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _ccpa_svc.get(conn, consent_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Consent record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.post("/ccpa/consent/{consent_id}/withdraw")
def withdraw_ccpa_consent(
    consent_id: str,
    body: CCPAWithdrawRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    rec = _ccpa_svc.get(conn, consent_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Consent record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    _ccpa_svc.withdraw(conn, consent_id, reason=body.reason)
    return {"consent_id": consent_id, "status": "withdrawn"}


# ── ABA Compliance ────────────────────────────────────────────────────────────


@router.post("/aba/compliance", status_code=status.HTTP_201_CREATED)
def log_aba_compliance(
    body: ABALogRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _aba_svc.log(
        conn,
        organization_id=current_user.organization_id or "org_default",
        matter_ref=body.matter_ref,
        attorney_id=current_user.user_id,
        attorney_name=body.attorney_name,
        ai_tool_name=body.ai_tool_name,
        ai_tool_version=body.ai_tool_version,
        ai_tool_provider=body.ai_tool_provider,
        rule_11_competence=body.rule_11_competence,
        rule_16_confidentiality=body.rule_16_confidentiality,
        rule_34_fairness=body.rule_34_fairness,
        rule_53_supervision=body.rule_53_supervision,
        client_disclosure_made=body.client_disclosure_made,
        state_bar=body.state_bar,
        state_specific_rule_ref=body.state_specific_rule_ref,
        state_specific_notes=body.state_specific_notes,
        output_reviewed=body.output_reviewed,
        review_notes=body.review_notes,
    )


@router.get("/aba/compliance")
def list_aba_compliance(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _aba_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/aba/compliance/{log_id}")
def get_aba_compliance(
    log_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _aba_svc.get(conn, log_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Compliance log not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.get("/aba/rules")
def get_aba_rules() -> dict[str, str]:
    """ABA Model Rules reference — no auth required."""
    return ABAComplianceService.aba_rules_reference()


# ── NIST AI RMF ───────────────────────────────────────────────────────────────


@router.post("/nist/rmf", status_code=status.HTTP_201_CREATED)
def create_nist_rmf(
    body: NISTRMFCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _nist_svc.create(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        ai_system_version=body.ai_system_version,
        govern_policies_defined=body.govern_policies_defined,
        govern_roles_assigned=body.govern_roles_assigned,
        govern_risk_tolerance_set=body.govern_risk_tolerance_set,
        govern_training_completed=body.govern_training_completed,
        govern_notes=body.govern_notes,
        map_intended_use=body.map_intended_use,
        map_context_established=body.map_context_established,
        map_risks_identified=body.map_risks_identified,
        map_stakeholders_consulted=body.map_stakeholders_consulted,
        map_notes=body.map_notes,
        measure_metrics_defined=body.measure_metrics_defined,
        measure_testing_completed=body.measure_testing_completed,
        measure_bias_evaluated=body.measure_bias_evaluated,
        measure_performance_score=body.measure_performance_score,
        measure_trustworthiness=body.measure_trustworthiness,
        measure_notes=body.measure_notes,
        manage_risk_responses=body.manage_risk_responses,
        manage_residual_risks=body.manage_residual_risks,
        manage_monitoring_plan=body.manage_monitoring_plan,
        manage_incident_plan=body.manage_incident_plan,
        manage_notes=body.manage_notes,
        profile_tier=body.profile_tier,
        created_by=current_user.user_id,
    )


@router.get("/nist/rmf")
def list_nist_rmf(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _nist_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/nist/rmf/{rmf_id}")
def get_nist_rmf(
    rmf_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _nist_svc.get(conn, rmf_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="NIST RMF record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


# ── ESIGN Audit ───────────────────────────────────────────────────────────────


@router.post("/esign/audit", status_code=status.HTTP_201_CREATED)
def log_esign_event(
    body: ESIGNEventRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    return _esign_svc.log_event(
        conn,
        organization_id=current_user.organization_id or "org_default",
        event_type=body.event_type,
        actor_id=current_user.user_id,
        actor_name=body.actor_name,
        actor_email=body.actor_email,
        document_ref=body.document_ref,
        document_hash=body.document_hash,
        sig_id=body.sig_id,
        event_sequence=body.event_sequence,
        event_data=body.event_data,
    )


@router.get("/esign/audit")
def list_esign_events(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _esign_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/esign/audit/document/{document_ref}")
def list_esign_events_by_doc(
    document_ref: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _esign_svc.list_by_doc(
        conn,
        current_user.organization_id or "org_default",
        document_ref,
    )
