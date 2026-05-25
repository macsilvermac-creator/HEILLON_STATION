"""ISO 42001 AIMS + FRIA API — Fase 20.

Endpoints:
  GET    /iso42001/annex-controls           — ISO 42001 Annex A reference (no auth)
  GET    /iso42001/eu-charter-rights        — EU Charter rights reference (no auth)
  POST   /iso42001/aims                     — register AIMS record
  GET    /iso42001/aims                     — list AIMS records
  GET    /iso42001/aims/{aims_id}           — get AIMS record
  POST   /iso42001/aims/{aims_id}/cert      — update certification status (admin)
  POST   /iso42001/aims/{aims_id}/control   — add control evidence
  GET    /iso42001/aims/{aims_id}/controls  — list control evidence
  POST   /iso42001/fria                     — create FRIA assessment
  GET    /iso42001/fria                     — list FRIA assessments
  GET    /iso42001/fria/{fria_id}           — get FRIA assessment
  POST   /iso42001/fria/{fria_id}/approve   — approve FRIA (admin)
  POST   /iso42001/fria/{fria_id}/reject    — reject FRIA (admin)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.iso42001.models import (
    CertificationStatus, ControlStatus, FRIAStatus,
    ImpactLikelihood, ImpactSeverity, ResidualRiskLevel,
)
from app.domain.iso42001.services import FRIAService, ISO42001Service
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/iso42001", tags=["iso42001"])

_aims_svc = ISO42001Service()
_fria_svc = FRIAService()


def _require_admin(current_user: UserRecord = Depends(get_current_user_record)) -> UserRecord:
    from app.domain.user.models import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only.")
    return current_user


# ── Schemas ────────────────────────────────────────────────────────────────────


class AIMSCreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    ai_system_version: str = Field(default="1.0", max_length=50)
    # Clause 4
    c4_internal_issues: str = Field(default="", max_length=2000)
    c4_external_issues: str = Field(default="", max_length=2000)
    c4_aims_scope: str = Field(default="", max_length=2000)
    c4_ai_policy_defined: bool = False
    # Clause 5
    c5_top_mgmt_commitment: bool = False
    c5_ai_policy_text: str = Field(default="", max_length=4000)
    c5_roles_defined: bool = False
    c5_dpo_appointed: bool = False
    # Clause 6
    c6_risks_assessed: bool = False
    c6_opportunities_noted: bool = False
    # Clause 7
    c7_resources_allocated: bool = False
    c7_competence_verified: bool = False
    c7_awareness_training: bool = False
    c7_documentation_maintained: bool = False
    # Clause 8
    c8_operational_controls: bool = False
    c8_ai_system_lifecycle: str = Field(default="", max_length=2000)
    c8_data_quality_assured: bool = False
    c8_human_oversight_active: bool = False
    c8_incident_response_plan: str = Field(default="", max_length=2000)
    # Clause 9
    c9_internal_audit_done: bool = False
    c9_mgmt_review_done: bool = False
    # Clause 10
    c10_continual_improvement_plan: str = Field(default="", max_length=2000)
    # Annex A
    annex_a2: bool = False
    annex_a3: bool = False
    annex_a4: bool = False
    annex_a5: bool = False
    annex_a6: bool = False
    annex_a7: bool = False
    annex_a8: bool = False
    annex_a9: bool = False
    # Certification
    certification_body: str | None = None
    certification_status: CertificationStatus = CertificationStatus.NOT_STARTED


class AIMSCertUpdateRequest(BaseModel):
    certification_status: CertificationStatus
    conformity_score: int | None = Field(default=None, ge=0, le=100)
    certification_body: str | None = None
    certificate_number: str | None = None
    certificate_expires_at: str | None = None


class ControlEvidenceRequest(BaseModel):
    control_ref: str = Field(..., pattern="^A\\.[2-9]$")
    evidence: str = Field(..., min_length=1, max_length=4000)
    status: ControlStatus = ControlStatus.IMPLEMENTED
    verified_by: str | None = None


class FRIACreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    intended_purpose: str = Field(default="", max_length=4000)
    foreseeable_misuse: str = Field(default="", max_length=4000)
    geographic_scope: str = Field(default="", max_length=500)
    population_affected: str = Field(default="", max_length=1000)
    # EU Charter rights
    right_dignity: bool = False
    right_privacy: bool = False
    right_nondiscrimination: bool = False
    right_fair_trial: bool = False
    right_presumption: bool = False
    right_labour: bool = False
    right_education: bool = False
    right_property: bool = False
    other_rights: str = Field(default="", max_length=1000)
    # Impact assessment
    impact_severity: ImpactSeverity = ImpactSeverity.LOW
    impact_likelihood: ImpactLikelihood = ImpactLikelihood.LOW
    impact_description: str = Field(default="", max_length=4000)
    vulnerable_groups_affected: bool = False
    vulnerable_groups_desc: str = Field(default="", max_length=2000)
    # Mitigation
    technical_measures: list[str] = Field(default_factory=list)
    organisational_measures: list[str] = Field(default_factory=list)
    transparency_measures: list[str] = Field(default_factory=list)
    human_oversight_measures: list[str] = Field(default_factory=list)
    residual_risk_level: ResidualRiskLevel = ResidualRiskLevel.LOW
    # Conclusion
    deployment_approved: bool = False
    deployment_conditions: str = Field(default="", max_length=2000)
    review_frequency: str = Field(
        default="annual",
        pattern="^(monthly|quarterly|semi_annual|annual)$",
    )
    assessor_name: str = Field(default="", max_length=200)
    dpo_consulted: bool = False
    legal_reviewed: bool = False


class FRIADecisionRequest(BaseModel):
    decision_notes: str = Field(default="", max_length=2000)


# ── Reference Endpoints (no auth) ─────────────────────────────────────────────


@router.get("/annex-controls")
def get_annex_controls() -> dict[str, str]:
    """ISO 42001 Annex A controls reference — no auth required."""
    return ISO42001Service.annex_controls()


@router.get("/eu-charter-rights")
def get_eu_charter_rights() -> dict[str, str]:
    """EU Charter of Fundamental Rights relevant to AI — no auth required."""
    return FRIAService.eu_charter_rights()


# ── AIMS Records ──────────────────────────────────────────────────────────────


@router.post("/aims", status_code=status.HTTP_201_CREATED)
def create_aims(
    body: AIMSCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _aims_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        ai_system_version=body.ai_system_version,
        c4_internal_issues=body.c4_internal_issues,
        c4_external_issues=body.c4_external_issues,
        c4_aims_scope=body.c4_aims_scope,
        c4_ai_policy_defined=body.c4_ai_policy_defined,
        c5_top_mgmt_commitment=body.c5_top_mgmt_commitment,
        c5_ai_policy_text=body.c5_ai_policy_text,
        c5_roles_defined=body.c5_roles_defined,
        c5_dpo_appointed=body.c5_dpo_appointed,
        c6_risks_assessed=body.c6_risks_assessed,
        c6_opportunities_noted=body.c6_opportunities_noted,
        c7_resources_allocated=body.c7_resources_allocated,
        c7_competence_verified=body.c7_competence_verified,
        c7_awareness_training=body.c7_awareness_training,
        c7_documentation_maintained=body.c7_documentation_maintained,
        c8_operational_controls=body.c8_operational_controls,
        c8_ai_system_lifecycle=body.c8_ai_system_lifecycle,
        c8_data_quality_assured=body.c8_data_quality_assured,
        c8_human_oversight_active=body.c8_human_oversight_active,
        c8_incident_response_plan=body.c8_incident_response_plan,
        c9_internal_audit_done=body.c9_internal_audit_done,
        c9_mgmt_review_done=body.c9_mgmt_review_done,
        c10_continual_improvement_plan=body.c10_continual_improvement_plan,
        annex_a2=body.annex_a2, annex_a3=body.annex_a3,
        annex_a4=body.annex_a4, annex_a5=body.annex_a5,
        annex_a6=body.annex_a6, annex_a7=body.annex_a7,
        annex_a8=body.annex_a8, annex_a9=body.annex_a9,
        certification_body=body.certification_body,
        certification_status=body.certification_status.value,
        created_by=current_user.user_id,
    )


@router.get("/aims")
def list_aims(
    skip: int = 0, limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _aims_svc.list_by_org(
        conn, current_user.organization_id or "org_default",
        skip=skip, limit=min(limit, 100),
    )


@router.get("/aims/{aims_id}")
def get_aims(
    aims_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _aims_svc.get(conn, aims_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="AIMS record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.post("/aims/{aims_id}/cert")
def update_aims_certification(
    aims_id: str,
    body: AIMSCertUpdateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, Any]:
    rec = _aims_svc.get(conn, aims_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="AIMS record not found.")
    return _aims_svc.update_certification(
        conn, aims_id,
        certification_status=body.certification_status.value,
        conformity_score=body.conformity_score,
        certification_body=body.certification_body,
        certificate_number=body.certificate_number,
        certificate_expires_at=body.certificate_expires_at,
    )


@router.post("/aims/{aims_id}/control", status_code=status.HTTP_201_CREATED)
def add_control_evidence(
    aims_id: str,
    body: ControlEvidenceRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _aims_svc.get(conn, aims_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="AIMS record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return _aims_svc.add_control_evidence(
        conn, aims_id,
        control_ref=body.control_ref,
        evidence=body.evidence,
        status=body.status.value,
        verified_by=body.verified_by,
    )


@router.get("/aims/{aims_id}/controls")
def list_control_evidence(
    aims_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    rec = _aims_svc.get(conn, aims_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="AIMS record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return _aims_svc.list_controls(conn, aims_id)


# ── FRIA ──────────────────────────────────────────────────────────────────────


@router.post("/fria", status_code=status.HTTP_201_CREATED)
def create_fria(
    body: FRIACreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _fria_svc.create(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        intended_purpose=body.intended_purpose,
        foreseeable_misuse=body.foreseeable_misuse,
        geographic_scope=body.geographic_scope,
        population_affected=body.population_affected,
        right_dignity=body.right_dignity, right_privacy=body.right_privacy,
        right_nondiscrimination=body.right_nondiscrimination,
        right_fair_trial=body.right_fair_trial, right_presumption=body.right_presumption,
        right_labour=body.right_labour, right_education=body.right_education,
        right_property=body.right_property, other_rights=body.other_rights,
        impact_severity=body.impact_severity.value,
        impact_likelihood=body.impact_likelihood.value,
        impact_description=body.impact_description,
        vulnerable_groups_affected=body.vulnerable_groups_affected,
        vulnerable_groups_desc=body.vulnerable_groups_desc,
        technical_measures=body.technical_measures,
        organisational_measures=body.organisational_measures,
        transparency_measures=body.transparency_measures,
        human_oversight_measures=body.human_oversight_measures,
        residual_risk_level=body.residual_risk_level.value,
        deployment_approved=body.deployment_approved,
        deployment_conditions=body.deployment_conditions,
        review_frequency=body.review_frequency,
        assessor_id=current_user.user_id,
        assessor_name=body.assessor_name,
        dpo_consulted=body.dpo_consulted,
        legal_reviewed=body.legal_reviewed,
        status="draft",
    )


@router.get("/fria")
def list_fria(
    skip: int = 0, limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _fria_svc.list_by_org(
        conn, current_user.organization_id or "org_default",
        skip=skip, limit=min(limit, 100),
    )


@router.get("/fria/{fria_id}")
def get_fria(
    fria_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _fria_svc.get(conn, fria_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="FRIA assessment not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.post("/fria/{fria_id}/approve")
def approve_fria(
    fria_id: str,
    body: FRIADecisionRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, Any]:
    rec = _fria_svc.get(conn, fria_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="FRIA assessment not found.")
    return _fria_svc.approve(
        conn, fria_id,
        approved_by=current_user.user_id,
        deployment_conditions=body.decision_notes,
    )


@router.post("/fria/{fria_id}/reject")
def reject_fria(
    fria_id: str,
    body: FRIADecisionRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, Any]:
    rec = _fria_svc.get(conn, fria_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="FRIA assessment not found.")
    return _fria_svc.reject(
        conn, fria_id,
        rejected_by=current_user.user_id,
        rejection_reason=body.decision_notes,
    )
