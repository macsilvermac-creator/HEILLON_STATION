"""Legal evidence AI API — FRE 707, citations, hallucination, competence.

Endpoints:
  GET    /legal-evidence/aba-rules            — ABA rules (no auth)
  GET    /legal-evidence/state-cle            — State CLE requirements (no auth)
  POST   /legal-evidence/fre707              — register FRE 707 evidence record
  GET    /legal-evidence/fre707              — list
  GET    /legal-evidence/fre707/{id}         — get
  POST   /legal-evidence/fre707/{id}/ruling  — update admissibility ruling
  POST   /legal-evidence/citations           — record citation verification
  GET    /legal-evidence/citations/doc/{ref} — citations for a document
  GET    /legal-evidence/citations/hallucinations — hallucinated citations
  GET    /legal-evidence/citations/{id}      — get
  POST   /legal-evidence/hallucinations      — report hallucination incident
  GET    /legal-evidence/hallucinations      — list incidents
  GET    /legal-evidence/hallucinations/{id} — get
  POST   /legal-evidence/hallucinations/{id}/resolve — resolve
  POST   /legal-evidence/competence          — issue competence certificate
  GET    /legal-evidence/competence          — list
  GET    /legal-evidence/competence/{id}     — get
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.legal_evidence.models import (
    AdmissibilityOpinion,
    CitationType,
    HallucinationSeverity,
    HallucinationType,
    IncidentSeverity,
    VerificationMethod,
)
from app.domain.legal_evidence.services import (
    AICompetenceService,
    CitationVerificationService,
    FRE707Service,
    HallucinationService,
)
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/legal-evidence", tags=["legal-evidence"])

_fre_svc = FRE707Service()
_cit_svc = CitationVerificationService()
_hal_svc = HallucinationService()
_comp_svc = AICompetenceService()


# ── Schemas ───────────────────────────────────────────────────────────────────


class FRE707CreateRequest(BaseModel):
    case_ref: str = Field(..., min_length=1, max_length=200)
    court: str = Field(default="", max_length=200)
    jurisdiction: str = Field(
        default="federal",
        pattern="^(federal|state|arbitration|international)$",
    )
    document_ref: str = Field(..., min_length=1, max_length=300)
    document_type: str = Field(default="", max_length=100)
    ai_system_name: str = Field(default="", max_length=200)
    ai_system_version: str = Field(default="", max_length=50)
    ai_provider: str = Field(default="", max_length=200)
    ai_model_id: str = Field(default="", max_length=200)
    training_data_description: str = Field(default="", max_length=2000)
    methodology_disclosed: bool = False
    reliable_principles: bool = False
    principles_applied: bool = False
    opinion_not_speculative: bool = False
    validation_method: str = Field(default="", max_length=500)
    error_rate_known: bool = False
    error_rate_value: float | None = None
    peer_reviewed: bool = False
    human_attorney_reviewed: bool = False
    daubert_analysis: str = Field(default="", max_length=4000)
    admissibility_opinion: AdmissibilityOpinion = AdmissibilityOpinion.PENDING
    opposing_counsel_notified: bool = False
    hdr_id: str | None = None
    hash_sha256: str = Field(default="", max_length=64)


class AdmissibilityRulingRequest(BaseModel):
    admissibility_opinion: AdmissibilityOpinion
    court_ruling: str | None = None
    conditions: str = Field(default="", max_length=2000)


class CitationVerifyRequest(BaseModel):
    document_ref: str = Field(..., min_length=1, max_length=300)
    case_ref: str = Field(default="", max_length=200)
    citation_text: str = Field(default="", max_length=2000)
    citation_type: CitationType = CitationType.CASE
    cited_court: str = Field(default="", max_length=200)
    cited_year: str = Field(default="", max_length=10)
    reporter: str = Field(default="", max_length=100)
    volume: str = Field(default="", max_length=20)
    page_start: str = Field(default="", max_length=20)
    url: str = Field(default="", max_length=500)
    verification_method: VerificationMethod = VerificationMethod.MANUAL
    verification_db: str = Field(default="", max_length=100)
    citation_exists: bool = False
    proposition_accurate: bool = False
    quote_accurate: bool = False
    case_still_good_law: bool = True
    is_hallucination: bool = False
    hallucination_type: HallucinationType | None = None
    hallucination_severity: HallucinationSeverity = HallucinationSeverity.NONE
    hallucination_notes: str = Field(default="", max_length=2000)
    filed_with_court: bool = False
    corrective_action_taken: bool = False
    corrective_action_desc: str = Field(default="", max_length=2000)
    bar_complaint_risk: str = Field(default="none", pattern="^(none|low|medium|high)$")


class HallucinationReportRequest(BaseModel):
    citation_id: str | None = None
    document_ref: str = Field(default="", max_length=300)
    case_ref: str = Field(default="", max_length=200)
    incident_type: str = Field(
        default="citation",
        pattern="^(citation|fact|statute|ruling|date|party_name|other)$",
    )
    ai_system: str = Field(default="", max_length=200)
    ai_model: str = Field(default="", max_length=200)
    original_output: str = Field(default="", max_length=4000)
    correct_info: str = Field(default="", max_length=4000)
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    filed_with_court: bool = False
    court_sanction: str | None = None
    financial_impact: float | None = None
    client_notified: bool = False
    bar_reported: bool = False
    root_cause: str = Field(default="", max_length=2000)
    prevention_measure: str = Field(default="", max_length=2000)
    workflow_updated: bool = False


class CompetenceCertRequest(BaseModel):
    attorney_id: str = Field(..., min_length=1, max_length=200)
    attorney_name: str = Field(default="", max_length=200)
    bar_number: str = Field(default="", max_length=100)
    jurisdiction: str = Field(default="", max_length=50)
    training_provider: str = Field(default="", max_length=200)
    training_course: str = Field(default="", max_length=200)
    cle_credits_earned: float = Field(default=0, ge=0)
    training_date: str = Field(default="", max_length=30)
    training_topics: list[str] = Field(default_factory=list)
    ai_systems_covered: list[str] = Field(default_factory=list)
    competence_areas: list[str] = Field(default_factory=list)
    aba_rule_1_1_compliant: bool = False
    state_bar_compliant: bool = False
    renewal_due_date: str | None = None
    expires_at: str | None = None


# ── Reference Endpoints (no auth) ─────────────────────────────────────────────


@router.get("/aba-rules")
def get_aba_rules() -> dict[str, str]:
    """ABA Formal Opinion 512 rules for AI use — no auth."""
    return AICompetenceService.aba_rules()


@router.get("/state-cle")
def get_state_cle() -> dict[str, str]:
    """State bar AI CLE requirements — no auth."""
    return AICompetenceService.state_cle_requirements()


# ── FRE 707 ───────────────────────────────────────────────────────────────────


@router.post("/fre707", status_code=status.HTTP_201_CREATED)
def create_fre707(
    body: FRE707CreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _fre_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        case_ref=body.case_ref,
        court=body.court,
        jurisdiction=body.jurisdiction,
        document_ref=body.document_ref,
        document_type=body.document_type,
        ai_system_name=body.ai_system_name,
        ai_system_version=body.ai_system_version,
        ai_provider=body.ai_provider,
        ai_model_id=body.ai_model_id,
        training_data_description=body.training_data_description,
        methodology_disclosed=body.methodology_disclosed,
        reliable_principles=body.reliable_principles,
        principles_applied=body.principles_applied,
        opinion_not_speculative=body.opinion_not_speculative,
        validation_method=body.validation_method,
        error_rate_known=body.error_rate_known,
        error_rate_value=body.error_rate_value,
        peer_reviewed=body.peer_reviewed,
        human_attorney_reviewed=body.human_attorney_reviewed,
        daubert_analysis=body.daubert_analysis,
        admissibility_opinion=body.admissibility_opinion.value,
        opposing_counsel_notified=body.opposing_counsel_notified,
        hdr_id=body.hdr_id,
        hash_sha256=body.hash_sha256,
        created_by=current_user.user_id,
    )


@router.get("/fre707")
def list_fre707(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _fre_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/fre707/{evidence_id}")
def get_fre707(
    evidence_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _fre_svc.get(conn, evidence_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Evidence record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.post("/fre707/{evidence_id}/ruling")
def update_admissibility(
    evidence_id: str,
    body: AdmissibilityRulingRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _fre_svc.get(conn, evidence_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Evidence record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return _fre_svc.update_admissibility(
        conn,
        evidence_id,
        admissibility_opinion=body.admissibility_opinion.value,
        court_ruling=body.court_ruling,
        conditions=body.conditions,
    )


# ── Citation Verification ─────────────────────────────────────────────────────


@router.post("/citations", status_code=status.HTTP_201_CREATED)
def verify_citation(
    body: CitationVerifyRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _cit_svc.verify(
        conn,
        organization_id=current_user.organization_id or "org_default",
        document_ref=body.document_ref,
        case_ref=body.case_ref,
        citation_text=body.citation_text,
        citation_type=body.citation_type.value,
        cited_court=body.cited_court,
        cited_year=body.cited_year,
        reporter=body.reporter,
        volume=body.volume,
        page_start=body.page_start,
        url=body.url,
        verified_by=current_user.user_id,
        verification_method=body.verification_method.value,
        verification_db=body.verification_db,
        citation_exists=body.citation_exists,
        proposition_accurate=body.proposition_accurate,
        quote_accurate=body.quote_accurate,
        case_still_good_law=body.case_still_good_law,
        is_hallucination=body.is_hallucination,
        hallucination_type=body.hallucination_type.value
        if body.hallucination_type
        else None,
        hallucination_severity=body.hallucination_severity.value,
        hallucination_notes=body.hallucination_notes,
        filed_with_court=body.filed_with_court,
        corrective_action_taken=body.corrective_action_taken,
        corrective_action_desc=body.corrective_action_desc,
        bar_complaint_risk=body.bar_complaint_risk,
    )


@router.get("/citations/hallucinations")
def list_hallucinated_citations(
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _cit_svc.list_hallucinations(
        conn, current_user.organization_id or "org_default"
    )


@router.get("/citations/doc/{document_ref:path}")
def list_citations_by_doc(
    document_ref: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _cit_svc.list_by_doc(
        conn, current_user.organization_id or "org_default", document_ref
    )


@router.get("/citations/{citation_id}")
def get_citation(
    citation_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _cit_svc.get(conn, citation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Citation record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


# ── Hallucination Incidents ───────────────────────────────────────────────────


@router.post("/hallucinations", status_code=status.HTTP_201_CREATED)
def report_hallucination(
    body: HallucinationReportRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _hal_svc.report(
        conn,
        organization_id=current_user.organization_id or "org_default",
        citation_id=body.citation_id,
        document_ref=body.document_ref,
        case_ref=body.case_ref,
        incident_type=body.incident_type,
        ai_system=body.ai_system,
        ai_model=body.ai_model,
        original_output=body.original_output,
        correct_info=body.correct_info,
        severity=body.severity.value,
        filed_with_court=body.filed_with_court,
        court_sanction=body.court_sanction,
        financial_impact=body.financial_impact,
        client_notified=body.client_notified,
        bar_reported=body.bar_reported,
        root_cause=body.root_cause,
        prevention_measure=body.prevention_measure,
        workflow_updated=body.workflow_updated,
        created_by=current_user.user_id,
    )


@router.get("/hallucinations")
def list_hallucinations(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _hal_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/hallucinations/{incident_id}")
def get_hallucination(
    incident_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _hal_svc.get(conn, incident_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.post("/hallucinations/{incident_id}/resolve")
def resolve_hallucination(
    incident_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _hal_svc.get(conn, incident_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return _hal_svc.resolve(conn, incident_id, resolved_by=current_user.user_id)


# ── AI Competence Certificates ────────────────────────────────────────────────


@router.post("/competence", status_code=status.HTTP_201_CREATED)
def issue_competence_cert(
    body: CompetenceCertRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _comp_svc.issue_certificate(
        conn,
        organization_id=current_user.organization_id or "org_default",
        attorney_id=body.attorney_id,
        attorney_name=body.attorney_name,
        bar_number=body.bar_number,
        jurisdiction=body.jurisdiction,
        training_provider=body.training_provider,
        training_course=body.training_course,
        cle_credits_earned=body.cle_credits_earned,
        training_date=body.training_date,
        training_topics=body.training_topics,
        ai_systems_covered=body.ai_systems_covered,
        competence_areas=body.competence_areas,
        aba_rule_1_1_compliant=body.aba_rule_1_1_compliant,
        state_bar_compliant=body.state_bar_compliant,
        renewal_due_date=body.renewal_due_date,
        issued_by="Heillon Legal",
        expires_at=body.expires_at,
    )


@router.get("/competence")
def list_competence_certs(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _comp_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/competence/{cert_id}")
def get_competence_cert(
    cert_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _comp_svc.get(conn, cert_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec
