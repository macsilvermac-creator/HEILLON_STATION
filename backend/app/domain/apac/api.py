"""APAC + Global privacy compliance API.

Endpoints:
  GET    /apac/uk/ico-exemptions             — UK ICO exemptions (no auth)
  POST   /apac/uk                            — register UK GDPR record
  GET    /apac/uk                            — list
  GET    /apac/uk/{id}                       — get
  POST   /apac/canada                        — register Canada PIPEDA/C-27 record
  GET    /apac/canada                        — list
  GET    /apac/canada/{id}                   — get
  GET    /apac/singapore/agentic-obligations — PDPC obligations (no auth)
  POST   /apac/singapore                     — register Singapore PDPA record
  GET    /apac/singapore                     — list
  GET    /apac/singapore/{id}                — get
  GET    /apac/australia/privacy-principles  — APPs reference (no auth)
  POST   /apac/australia                     — register Australia Privacy record
  GET    /apac/australia                     — list
  GET    /apac/australia/{id}                — get
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.apac.models import (
    CanadaProvincialLaw,
    EUTransferMechanism,
    UKLawfulBasis,
)
from app.domain.apac.services import (
    AustraliaPrivacyService,
    CanadaPrivacyService,
    SingaporePDPAService,
    UKGDPRService,
)
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/apac", tags=["apac"])

_uk_svc = UKGDPRService()
_ca_svc = CanadaPrivacyService()
_sg_svc = SingaporePDPAService()
_au_svc = AustraliaPrivacyService()


# ── Schemas ───────────────────────────────────────────────────────────────────


class UKGDPRCreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    ico_reference: str = Field(default="", max_length=100)
    ico_registered: bool = False
    data_protection_fee_paid: bool = False
    lawful_basis: UKLawfulBasis = UKLawfulBasis.LEGITIMATE_INTERESTS
    legitimate_interests_assessment: str = Field(default="", max_length=4000)
    ai_code_applicable: bool = False
    transparency_notice_published: bool = False
    human_review_available: bool = False
    profiling_used: bool = False
    profiling_basis: str = Field(default="", max_length=500)
    right_access_process: str = Field(default="", max_length=2000)
    right_erasure_process: str = Field(default="", max_length=2000)
    right_portability_process: str = Field(default="", max_length=2000)
    right_object_ai: str = Field(default="", max_length=2000)
    dpo_required: bool = False
    dpo_name: str = Field(default="", max_length=200)
    uk_rep_appointed: bool = False
    uk_rep_name: str = Field(default="", max_length=200)
    eu_transfer_mechanism: EUTransferMechanism = EUTransferMechanism.NONE
    dpia_conducted: bool = False
    dpia_ref: str | None = None


class CanadaPrivacyCreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    provincial_law: CanadaProvincialLaw = CanadaProvincialLaw.FEDERAL
    law_25_quebec: bool = False
    consent_obtained: bool = False
    consent_form: str = Field(default="", max_length=2000)
    aida_applicable: bool = False
    high_impact_system: bool = False
    high_impact_categories: list[str] = Field(default_factory=list)
    impact_assessment_done: bool = False
    mitigation_measures: list[str] = Field(default_factory=list)
    incident_reporting_process: str = Field(default="", max_length=2000)
    q25_privacy_officer: str = Field(default="", max_length=200)
    q25_privacy_policy_published: bool = False
    q25_pia_required: bool = False
    q25_pia_done: bool = False
    q25_72h_breach_report: bool = False
    q25_portability_enabled: bool = False


class SingaporePDPACreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    pdpa_dpo_designated: bool = False
    pdpa_dpo_name: str = Field(default="", max_length=200)
    pdpa_dpo_registered: bool = False
    data_protection_policy_published: bool = False
    do_not_call_compliant: bool = False
    consent_purpose_specific: bool = False
    notification_given: bool = False
    agentic_ai_applicable: bool = False
    agentic_human_oversight: bool = False
    agentic_oversight_desc: str = Field(default="", max_length=2000)
    agentic_disclosure: bool = False
    agentic_disclosure_text: str = Field(default="", max_length=2000)
    agentic_consent_scope: str = Field(default="", max_length=1000)
    agentic_data_minimised: bool = False
    agentic_incident_plan: str = Field(default="", max_length=2000)
    pdpc_model_governance_aligned: bool = False
    explainability_implemented: bool = False
    bias_testing_done: bool = False
    cbdt_countries: list[str] = Field(default_factory=list)
    cbdt_contractual_clauses: bool = False
    cbdt_binding_corporate_rules: bool = False
    cbdt_adequacy_applicable: bool = False


class AustraliaPrivacyCreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    annual_turnover_aud: float | None = None
    health_service_provider: bool = False
    acts_covered: bool = False
    app1_privacy_policy: bool = False
    app5_collection_notice: bool = False
    app6_primary_purpose_only: bool = False
    app11_security_measures: str = Field(default="", max_length=2000)
    app12_access_process: str = Field(default="", max_length=2000)
    app13_correction_process: str = Field(default="", max_length=2000)
    adm_used: bool = False
    adm_description: str = Field(default="", max_length=2000)
    adm_explanation_available: bool = False
    adm_human_review_available: bool = False
    adm_opt_out_available: bool = False
    adm_meaningful_impact: bool = False
    ndb_scheme_applicable: bool = True
    breach_assessment_process: str = Field(default="", max_length=2000)
    oaic_notification_process: str = Field(default="", max_length=2000)
    oaic_complaint_process: str = Field(default="", max_length=2000)
    privacy_impact_assessment_done: bool = False


# ── Reference Endpoints (no auth) ─────────────────────────────────────────────


@router.get("/uk/ico-exemptions")
def get_uk_ico_exemptions() -> dict[str, str]:
    """UK ICO registration exemptions — no auth."""
    return UKGDPRService.ico_exemptions()


@router.get("/singapore/agentic-obligations")
def get_agentic_obligations() -> dict[str, str]:
    """PDPC Agentic AI Framework 5 obligations — no auth."""
    return SingaporePDPAService.agentic_obligations()


@router.get("/australia/privacy-principles")
def get_australia_apps() -> dict[str, str]:
    """Australian Privacy Principles (APPs) — no auth."""
    return AustraliaPrivacyService.privacy_principles()


# ── UK GDPR ───────────────────────────────────────────────────────────────────


@router.post("/uk", status_code=status.HTTP_201_CREATED)
def create_uk_gdpr(
    body: UKGDPRCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _uk_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        ico_reference=body.ico_reference,
        ico_registered=body.ico_registered,
        data_protection_fee_paid=body.data_protection_fee_paid,
        lawful_basis=body.lawful_basis.value,
        legitimate_interests_assessment=body.legitimate_interests_assessment,
        ai_code_applicable=body.ai_code_applicable,
        transparency_notice_published=body.transparency_notice_published,
        human_review_available=body.human_review_available,
        profiling_used=body.profiling_used,
        profiling_basis=body.profiling_basis,
        right_access_process=body.right_access_process,
        right_erasure_process=body.right_erasure_process,
        right_portability_process=body.right_portability_process,
        right_object_ai=body.right_object_ai,
        dpo_required=body.dpo_required,
        dpo_name=body.dpo_name,
        uk_rep_appointed=body.uk_rep_appointed,
        uk_rep_name=body.uk_rep_name,
        eu_transfer_mechanism=body.eu_transfer_mechanism.value,
        dpia_conducted=body.dpia_conducted,
        dpia_ref=body.dpia_ref,
        created_by=current_user.user_id,
    )


@router.get("/uk")
def list_uk_gdpr(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _uk_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/uk/{record_id}")
def get_uk_gdpr(
    record_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _uk_svc.get(conn, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="UK GDPR record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


# ── Canada ────────────────────────────────────────────────────────────────────


@router.post("/canada", status_code=status.HTTP_201_CREATED)
def create_canada_privacy(
    body: CanadaPrivacyCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _ca_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        provincial_law=body.provincial_law.value,
        law_25_quebec=body.law_25_quebec,
        consent_obtained=body.consent_obtained,
        consent_form=body.consent_form,
        aida_applicable=body.aida_applicable,
        high_impact_system=body.high_impact_system,
        high_impact_categories=body.high_impact_categories,
        impact_assessment_done=body.impact_assessment_done,
        mitigation_measures=body.mitigation_measures,
        incident_reporting_process=body.incident_reporting_process,
        q25_privacy_officer=body.q25_privacy_officer,
        q25_privacy_policy_published=body.q25_privacy_policy_published,
        q25_pia_required=body.q25_pia_required,
        q25_pia_done=body.q25_pia_done,
        q25_72h_breach_report=body.q25_72h_breach_report,
        q25_portability_enabled=body.q25_portability_enabled,
        created_by=current_user.user_id,
    )


@router.get("/canada")
def list_canada_privacy(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _ca_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/canada/{record_id}")
def get_canada_privacy(
    record_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _ca_svc.get(conn, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Canada privacy record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


# ── Singapore ─────────────────────────────────────────────────────────────────


@router.post("/singapore", status_code=status.HTTP_201_CREATED)
def create_singapore_pdpa(
    body: SingaporePDPACreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _sg_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        pdpa_dpo_designated=body.pdpa_dpo_designated,
        pdpa_dpo_name=body.pdpa_dpo_name,
        pdpa_dpo_registered=body.pdpa_dpo_registered,
        data_protection_policy_published=body.data_protection_policy_published,
        do_not_call_compliant=body.do_not_call_compliant,
        consent_purpose_specific=body.consent_purpose_specific,
        notification_given=body.notification_given,
        agentic_ai_applicable=body.agentic_ai_applicable,
        agentic_human_oversight=body.agentic_human_oversight,
        agentic_oversight_desc=body.agentic_oversight_desc,
        agentic_disclosure=body.agentic_disclosure,
        agentic_disclosure_text=body.agentic_disclosure_text,
        agentic_consent_scope=body.agentic_consent_scope,
        agentic_data_minimised=body.agentic_data_minimised,
        agentic_incident_plan=body.agentic_incident_plan,
        pdpc_model_governance_aligned=body.pdpc_model_governance_aligned,
        explainability_implemented=body.explainability_implemented,
        bias_testing_done=body.bias_testing_done,
        cbdt_countries=body.cbdt_countries,
        cbdt_contractual_clauses=body.cbdt_contractual_clauses,
        cbdt_binding_corporate_rules=body.cbdt_binding_corporate_rules,
        cbdt_adequacy_applicable=body.cbdt_adequacy_applicable,
        created_by=current_user.user_id,
    )


@router.get("/singapore")
def list_singapore_pdpa(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _sg_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/singapore/{record_id}")
def get_singapore_pdpa(
    record_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _sg_svc.get(conn, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Singapore PDPA record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


# ── Australia ─────────────────────────────────────────────────────────────────


@router.post("/australia", status_code=status.HTTP_201_CREATED)
def create_australia_privacy(
    body: AustraliaPrivacyCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _au_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        annual_turnover_aud=body.annual_turnover_aud,
        health_service_provider=body.health_service_provider,
        acts_covered=body.acts_covered,
        app1_privacy_policy=body.app1_privacy_policy,
        app5_collection_notice=body.app5_collection_notice,
        app6_primary_purpose_only=body.app6_primary_purpose_only,
        app11_security_measures=body.app11_security_measures,
        app12_access_process=body.app12_access_process,
        app13_correction_process=body.app13_correction_process,
        adm_used=body.adm_used,
        adm_description=body.adm_description,
        adm_explanation_available=body.adm_explanation_available,
        adm_human_review_available=body.adm_human_review_available,
        adm_opt_out_available=body.adm_opt_out_available,
        adm_meaningful_impact=body.adm_meaningful_impact,
        ndb_scheme_applicable=body.ndb_scheme_applicable,
        breach_assessment_process=body.breach_assessment_process,
        oaic_notification_process=body.oaic_notification_process,
        oaic_complaint_process=body.oaic_complaint_process,
        privacy_impact_assessment_done=body.privacy_impact_assessment_done,
        created_by=current_user.user_id,
    )


@router.get("/australia")
def list_australia_privacy(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _au_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/australia/{record_id}")
def get_australia_privacy(
    record_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _au_svc.get(conn, record_id)
    if rec is None:
        raise HTTPException(
            status_code=404, detail="Australia privacy record not found."
        )
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec
