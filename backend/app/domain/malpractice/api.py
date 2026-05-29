"""Malpractice insurance + compliance scoring API — Fase 20.

Endpoints:
  GET    /malpractice/colorado/rights         — SB 26-189 consumer rights (no auth)
  POST   /malpractice/colorado                — register Colorado SB 26-189 record
  GET    /malpractice/colorado                — list
  GET    /malpractice/colorado/{id}           — get
  GET    /malpractice/ccpa-admt/rights        — CCPA ADMT rights (no auth)
  POST   /malpractice/ccpa-admt              — register CCPA ADMT record
  GET    /malpractice/ccpa-admt              — list
  GET    /malpractice/ccpa-admt/{id}         — get
  POST   /malpractice/insurance               — register malpractice insurance record
  GET    /malpractice/insurance               — list
  GET    /malpractice/insurance/{id}          — get
  GET    /malpractice/score/weights           — score weights (no auth)
  POST   /malpractice/score                   — compute global compliance score
  GET    /malpractice/score                   — list scores
  GET    /malpractice/score/latest/{ref}      — latest score for AI system
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.malpractice.models import ADMTPurpose, ConsequentialDecisionType
from app.domain.malpractice.services import (
    CCPAADMTService,
    ColoradoSB26189Service,
    HeilonComplianceScoreService,
    MalpracticeInsuranceService,
)
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/malpractice", tags=["malpractice"])

_co_svc = ColoradoSB26189Service()
_admt_svc = CCPAADMTService()
_ins_svc = MalpracticeInsuranceService()
_score_svc = HeilonComplianceScoreService()


# ── Schemas ───────────────────────────────────────────────────────────────────


class ColoradoSB26189CreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    ai_system_version: str = Field(default="1.0", max_length=50)
    consequential_decision_type: ConsequentialDecisionType = (
        ConsequentialDecisionType.OTHER
    )
    consumers_affected_count: int = Field(default=0, ge=0)
    disclosure_provided: bool = False
    disclosure_timing: str = Field(default="", max_length=200)
    disclosure_method: str = Field(default="", max_length=200)
    explanation_available: bool = False
    explanation_process: str = Field(default="", max_length=2000)
    explanation_response_days: int = Field(default=30, ge=1, le=365)
    data_correction_available: bool = False
    data_correction_process: str = Field(default="", max_length=2000)
    human_review_available: bool = False
    human_review_process: str = Field(default="", max_length=2000)
    human_review_response_days: int = Field(default=30, ge=1, le=365)
    opt_out_available: bool = False
    opt_out_categories: list[str] = Field(default_factory=list)
    small_business_exempt: bool = False
    open_source_exempt: bool = False
    national_security_exempt: bool = False


class CCPAADMTCreateRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    admt_purpose: ADMTPurpose = ADMTPurpose.OTHER
    significant_decisions: bool = False
    personal_data_used: bool = False
    california_consumers: bool = False
    pre_use_notice_provided: bool = False
    pre_use_notice_content: str = Field(default="", max_length=4000)
    notice_delivery_method: str = Field(default="", max_length=200)
    opt_out_available: bool = False
    opt_out_mechanism: str = Field(default="", max_length=1000)
    opt_out_response_days: int = Field(default=15, ge=1, le=45)
    global_opt_out_honored: bool = False
    access_to_admt_logic: bool = False
    access_process: str = Field(default="", max_length=2000)
    human_review_available: bool = False
    human_review_process: str = Field(default="", max_length=2000)
    human_review_timing: str = Field(default="", max_length=200)
    risk_assessment_required: bool = False
    risk_assessment_done: bool = False
    risk_assessment_ref: str | None = None
    cppa_submission_required: bool = False
    admt_vendor_agreements: list[str] = Field(default_factory=list)


class InsuranceCreateRequest(BaseModel):
    law_firm_name: str = Field(default="", max_length=200)
    bar_jurisdiction: str = Field(default="", max_length=50)
    insurer_name: str = Field(default="", max_length=200)
    policy_number: str = Field(default="", max_length=100)
    policy_start: str | None = None
    policy_end: str | None = None
    coverage_limit_usd: float | None = None
    current_premium_usd: float | None = None
    ai_tools_used: bool = False
    ai_tools_list: list[str] = Field(default_factory=list)
    ai_outputs_filed_in_court: bool = False
    citation_verification_process: bool = False
    hallucination_incidents_12mo: int = Field(default=0, ge=0)
    ai_competence_certified: bool = False
    heillon_compliance_score: int | None = Field(default=None, ge=0, le=100)
    score_breakdown: dict | None = None
    ai_related_claims_count: int = Field(default=0, ge=0)
    ai_related_claims_usd: float = Field(default=0, ge=0)


class ComplianceScoreRequest(BaseModel):
    ai_system_ref: str = Field(..., min_length=1, max_length=200)
    ai_system_name: str = Field(default="", max_length=200)
    score_hdr_coverage: int = Field(default=0, ge=0, le=100)
    score_citation_accuracy: int = Field(default=0, ge=0, le=100)
    score_hallucination: int = Field(default=0, ge=0, le=100)
    score_lgpd: int = Field(default=0, ge=0, le=100)
    score_gdpr_eu: int = Field(default=0, ge=0, le=100)
    score_gdpr_uk: int = Field(default=0, ge=0, le=100)
    score_ccpa: int = Field(default=0, ge=0, le=100)
    score_colorado: int = Field(default=0, ge=0, le=100)
    score_pdpl_uae: int = Field(default=0, ge=0, le=100)
    score_pdpa_sg: int = Field(default=0, ge=0, le=100)
    score_privacy_au: int = Field(default=0, ge=0, le=100)
    score_pipeda_ca: int = Field(default=0, ge=0, le=100)
    score_iso42001: int = Field(default=0, ge=0, le=100)
    score_iso27001: int = Field(default=0, ge=0, le=100)
    score_nist_rmf: int = Field(default=0, ge=0, le=100)
    score_euai_act: int = Field(default=0, ge=0, le=100)
    score_attorney_competence: int = Field(default=0, ge=0, le=100)
    evidence_bundle: dict | None = None


# ── Reference Endpoints (no auth) ─────────────────────────────────────────────


@router.get("/colorado/rights")
def get_colorado_rights() -> dict[str, str]:
    """Colorado SB 26-189 consumer rights — no auth."""
    return ColoradoSB26189Service.consumer_rights()


@router.get("/ccpa-admt/rights")
def get_admt_rights() -> dict[str, str]:
    """CCPA ADMT Regulations consumer rights — no auth."""
    return CCPAADMTService.admt_rights()


@router.get("/score/weights")
def get_score_weights() -> dict[str, int]:
    """Heillon compliance score component weights — no auth."""
    return HeilonComplianceScoreService.score_weights()


# ── Colorado SB 26-189 ────────────────────────────────────────────────────────


@router.post("/colorado", status_code=status.HTTP_201_CREATED)
def create_colorado(
    body: ColoradoSB26189CreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _co_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        ai_system_version=body.ai_system_version,
        consequential_decision_type=body.consequential_decision_type.value,
        consumers_affected_count=body.consumers_affected_count,
        disclosure_provided=body.disclosure_provided,
        disclosure_timing=body.disclosure_timing,
        disclosure_method=body.disclosure_method,
        explanation_available=body.explanation_available,
        explanation_process=body.explanation_process,
        explanation_response_days=body.explanation_response_days,
        data_correction_available=body.data_correction_available,
        data_correction_process=body.data_correction_process,
        human_review_available=body.human_review_available,
        human_review_process=body.human_review_process,
        human_review_response_days=body.human_review_response_days,
        opt_out_available=body.opt_out_available,
        opt_out_categories=body.opt_out_categories,
        small_business_exempt=body.small_business_exempt,
        open_source_exempt=body.open_source_exempt,
        national_security_exempt=body.national_security_exempt,
        created_by=current_user.user_id,
    )


@router.get("/colorado")
def list_colorado(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _co_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/colorado/{record_id}")
def get_colorado(
    record_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _co_svc.get(conn, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Colorado record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


# ── CCPA ADMT ─────────────────────────────────────────────────────────────────


@router.post("/ccpa-admt", status_code=status.HTTP_201_CREATED)
def create_ccpa_admt(
    body: CCPAADMTCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _admt_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        admt_purpose=body.admt_purpose.value,
        significant_decisions=body.significant_decisions,
        personal_data_used=body.personal_data_used,
        california_consumers=body.california_consumers,
        pre_use_notice_provided=body.pre_use_notice_provided,
        pre_use_notice_content=body.pre_use_notice_content,
        notice_delivery_method=body.notice_delivery_method,
        opt_out_available=body.opt_out_available,
        opt_out_mechanism=body.opt_out_mechanism,
        opt_out_response_days=body.opt_out_response_days,
        global_opt_out_honored=body.global_opt_out_honored,
        access_to_admt_logic=body.access_to_admt_logic,
        access_process=body.access_process,
        human_review_available=body.human_review_available,
        human_review_process=body.human_review_process,
        human_review_timing=body.human_review_timing,
        risk_assessment_required=body.risk_assessment_required,
        risk_assessment_done=body.risk_assessment_done,
        risk_assessment_ref=body.risk_assessment_ref,
        cppa_submission_required=body.cppa_submission_required,
        admt_vendor_agreements=body.admt_vendor_agreements,
        created_by=current_user.user_id,
    )


@router.get("/ccpa-admt")
def list_ccpa_admt(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _admt_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/ccpa-admt/{admt_id}")
def get_ccpa_admt(
    admt_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _admt_svc.get(conn, admt_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="CCPA ADMT record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


# ── Malpractice Insurance ─────────────────────────────────────────────────────


@router.post("/insurance", status_code=status.HTTP_201_CREATED)
def create_insurance(
    body: InsuranceCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _ins_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        law_firm_name=body.law_firm_name,
        bar_jurisdiction=body.bar_jurisdiction,
        insurer_name=body.insurer_name,
        policy_number=body.policy_number,
        policy_start=body.policy_start,
        policy_end=body.policy_end,
        coverage_limit_usd=body.coverage_limit_usd,
        current_premium_usd=body.current_premium_usd,
        ai_tools_used=body.ai_tools_used,
        ai_tools_list=body.ai_tools_list,
        ai_outputs_filed_in_court=body.ai_outputs_filed_in_court,
        citation_verification_process=body.citation_verification_process,
        hallucination_incidents_12mo=body.hallucination_incidents_12mo,
        ai_competence_certified=body.ai_competence_certified,
        heillon_compliance_score=body.heillon_compliance_score,
        score_breakdown=body.score_breakdown,
        ai_related_claims_count=body.ai_related_claims_count,
        ai_related_claims_usd=body.ai_related_claims_usd,
        created_by=current_user.user_id,
    )


@router.get("/insurance")
def list_insurance(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _ins_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/insurance/{insurance_id}")
def get_insurance(
    insurance_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _ins_svc.get(conn, insurance_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Insurance record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


# ── Heillon Global Compliance Score ──────────────────────────────────────────


@router.post("/score", status_code=status.HTTP_201_CREATED)
def compute_compliance_score(
    body: ComplianceScoreRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    component_scores = {
        "score_hdr_coverage": body.score_hdr_coverage,
        "score_citation_accuracy": body.score_citation_accuracy,
        "score_hallucination": body.score_hallucination,
        "score_lgpd": body.score_lgpd,
        "score_gdpr_eu": body.score_gdpr_eu,
        "score_gdpr_uk": body.score_gdpr_uk,
        "score_ccpa": body.score_ccpa,
        "score_colorado": body.score_colorado,
        "score_pdpl_uae": body.score_pdpl_uae,
        "score_pdpa_sg": body.score_pdpa_sg,
        "score_privacy_au": body.score_privacy_au,
        "score_pipeda_ca": body.score_pipeda_ca,
        "score_iso42001": body.score_iso42001,
        "score_iso27001": body.score_iso27001,
        "score_nist_rmf": body.score_nist_rmf,
        "score_euai_act": body.score_euai_act,
        "score_attorney_competence": body.score_attorney_competence,
    }
    return _score_svc.compute(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_ref=body.ai_system_ref,
        ai_system_name=body.ai_system_name,
        component_scores=component_scores,
        evidence_bundle=body.evidence_bundle,
        computed_by=current_user.user_id,
    )


@router.get("/score")
def list_compliance_scores(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _score_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/score/latest/{ai_system_ref:path}")
def get_latest_score(
    ai_system_ref: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _score_svc.get_latest(
        conn, current_user.organization_id or "org_default", ai_system_ref
    )
    if rec is None:
        raise HTTPException(
            status_code=404, detail="No compliance score found for this system."
        )
    return rec
