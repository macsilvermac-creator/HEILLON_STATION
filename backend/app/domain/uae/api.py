"""UAE regulatory compliance API — Fase 19.

Endpoints:
  POST   /uae/pdpl/consent                    — record UAE PDPL consent
  GET    /uae/pdpl/consent                    — list
  GET    /uae/pdpl/consent/{id}               — get
  POST   /uae/pdpl/consent/{id}/withdraw      — withdraw

  POST   /uae/governance                      — register AI system
  GET    /uae/governance                      — list
  GET    /uae/governance/{id}                 — get
  POST   /uae/governance/{id}/seal            — apply UAE AI Seal (admin)
  GET    /uae/governance/ethics-principles    — UAE AI Ethics (7 pillars)
  GET    /uae/governance/difc-requirements    — DIFC DP requirements

  POST   /uae/pass/sign                       — record UAE PASS signature
  GET    /uae/pass/sign                       — list
  GET    /uae/pass/sign/{sig_id}              — get
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.uae.services import (
    UAEAIGovernanceService,
    UAEPDPLConsentService,
    UAEPassSignatureService,
)
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/uae", tags=["uae"])

_pdpl_svc = UAEPDPLConsentService()
_gov_svc = UAEAIGovernanceService()
_pass_svc = UAEPassSignatureService()


def _require_admin(current_user: UserRecord = Depends(get_current_user_record)) -> UserRecord:
    from app.domain.user.models import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only.")
    return current_user


# ── Schemas ────────────────────────────────────────────────────────────────────


class PDPLConsentCreateRequest(BaseModel):
    data_subject_id: str = Field(..., min_length=1, max_length=200)
    data_subject_name: str = Field(..., min_length=1, max_length=200)
    data_subject_email: str = Field(default="", max_length=200)
    data_subject_nationality: str = Field(default="", max_length=100)
    data_categories: list[str] = Field(default_factory=list)
    processing_purposes: list[str] = Field(default_factory=list)
    legal_basis: str = Field(
        default="consent",
        pattern="^(consent|contract|legal_obligation|vital_interests|public_interest|legitimate_interest)$",
    )
    sensitive_data_processing: bool = False
    biometric_data: bool = False
    health_data: bool = False
    children_data: bool = False
    guardian_consent_obtained: bool = False
    cross_border_transfer: bool = False
    transfer_destination_country: str | None = None
    transfer_safeguards: str = Field(default="", max_length=1000)
    difc_jurisdiction: bool = False
    adgm_jurisdiction: bool = False
    consent_text: str = Field(default="", max_length=4000)
    language: str = Field(default="en", pattern="^(en|ar)$")
    expires_at: str | None = None


class PDPLWithdrawRequest(BaseModel):
    reason: str = Field(default="", max_length=1000)


class UAEGovernanceCreateRequest(BaseModel):
    ai_system_name: str = Field(..., min_length=1, max_length=200)
    ai_system_version: str = Field(default="1.0", max_length=50)
    ai_system_purpose: str = Field(default="", max_length=4000)
    # Ethics pillars
    ethics_human_centered: bool = False
    ethics_fairness: bool = False
    ethics_transparency: bool = False
    ethics_safety_reliability: bool = False
    ethics_privacy_security: bool = False
    ethics_accountability: bool = False
    ethics_sustainability: bool = False
    # Sector
    sector: str = Field(
        default="legal",
        pattern="^(legal|health|transport|space|renewable_energy|water|technology|education|economy|cybersecurity|telecommunications)$",
    )
    # DIFC / ADGM
    difc_compliant: bool = False
    difc_registration_ref: str | None = None
    adgm_compliant: bool = False
    adgm_registration_ref: str | None = None
    # Jurisdiction
    jurisdiction_ae: str = Field(
        default="federal",
        pattern="^(federal|dubai|abu_dhabi|sharjah|difc|adgm|dmcc)$",
    )
    risk_level: str = Field(
        default="medium", pattern="^(low|medium|high)$"
    )
    risk_assessment_notes: str = Field(default="", max_length=4000)


class UAESealRequest(BaseModel):
    seal_reference: str = Field(..., min_length=1, max_length=200)
    seal_category: str = Field(
        ...,
        pattern="^(government|commercial|research|critical_infrastructure)$",
    )
    seal_expires_at: str | None = None


class UAEPassSignRequest(BaseModel):
    document_ref: str = Field(..., min_length=1, max_length=300)
    document_hash: str = Field(..., min_length=64, max_length=64)
    document_title: str = Field(default="", max_length=500)
    signatory_name: str = Field(..., min_length=1, max_length=200)
    signatory_email: str = Field(..., max_length=200)
    signatory_emirates_id: str | None = None
    signatory_mobile: str | None = None
    uae_pass_verified: bool = False
    uae_pass_identity_level: str = Field(
        default="verified", pattern="^(basic|verified|qualified)$"
    )
    uae_pass_session_ref: str | None = None
    trust_service_provider: str = Field(default="", max_length=200)
    trust_service_level: str = Field(
        default="qualified", pattern="^(qualified|advanced|basic)$"
    )
    signature_format: str = Field(
        default="PAdES-LTA", pattern="^(PAdES-LTA|CAdES-LTA|XAdES-LTA)$"
    )
    signature_level: str = Field(
        default="QES", pattern="^(QES|AES|SES)$"
    )
    tsa_provider: str | None = None
    hdr_id: str | None = None


# ── UAE PDPL ──────────────────────────────────────────────────────────────────


@router.post("/pdpl/consent", status_code=status.HTTP_201_CREATED)
def create_pdpl_consent(
    body: PDPLConsentCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _pdpl_svc.record_consent(
        conn,
        organization_id=current_user.organization_id or "org_default",
        data_subject_id=body.data_subject_id,
        data_subject_name=body.data_subject_name,
        data_subject_email=body.data_subject_email,
        data_subject_nationality=body.data_subject_nationality,
        data_categories=body.data_categories,
        processing_purposes=body.processing_purposes,
        legal_basis=body.legal_basis,
        sensitive_data_processing=body.sensitive_data_processing,
        biometric_data=body.biometric_data,
        health_data=body.health_data,
        children_data=body.children_data,
        guardian_consent_obtained=body.guardian_consent_obtained,
        cross_border_transfer=body.cross_border_transfer,
        transfer_destination_country=body.transfer_destination_country,
        transfer_safeguards=body.transfer_safeguards,
        difc_jurisdiction=body.difc_jurisdiction,
        adgm_jurisdiction=body.adgm_jurisdiction,
        consent_text=body.consent_text,
        language=body.language,
        expires_at=body.expires_at,
    )


@router.get("/pdpl/consent")
def list_pdpl_consent(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _pdpl_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/pdpl/consent/{consent_id}")
def get_pdpl_consent(
    consent_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _pdpl_svc.get(conn, consent_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Consent record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.post("/pdpl/consent/{consent_id}/withdraw")
def withdraw_pdpl_consent(
    consent_id: str,
    body: PDPLWithdrawRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    rec = _pdpl_svc.get(conn, consent_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Consent record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    _pdpl_svc.withdraw(conn, consent_id, reason=body.reason)
    return {"consent_id": consent_id, "status": "withdrawn"}


# ── UAE AI Governance ──────────────────────────────────────────────────────────


@router.get("/governance/ethics-principles")
def get_ethics_principles() -> dict[str, str]:
    """UAE AI Ethics 7 pillars — no auth required."""
    return UAEAIGovernanceService.ethics_principles()


@router.get("/governance/difc-requirements")
def get_difc_requirements() -> dict[str, str]:
    """DIFC Data Protection requirements — no auth required."""
    return UAEAIGovernanceService.difc_requirements()


@router.post("/governance", status_code=status.HTTP_201_CREATED)
def register_uae_governance(
    body: UAEGovernanceCreateRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    return _gov_svc.register(
        conn,
        organization_id=current_user.organization_id or "org_default",
        ai_system_name=body.ai_system_name,
        ai_system_version=body.ai_system_version,
        ai_system_purpose=body.ai_system_purpose,
        ethics_human_centered=body.ethics_human_centered,
        ethics_fairness=body.ethics_fairness,
        ethics_transparency=body.ethics_transparency,
        ethics_safety_reliability=body.ethics_safety_reliability,
        ethics_privacy_security=body.ethics_privacy_security,
        ethics_accountability=body.ethics_accountability,
        ethics_sustainability=body.ethics_sustainability,
        sector=body.sector,
        difc_compliant=body.difc_compliant,
        difc_registration_ref=body.difc_registration_ref,
        adgm_compliant=body.adgm_compliant,
        adgm_registration_ref=body.adgm_registration_ref,
        jurisdiction_ae=body.jurisdiction_ae,
        risk_level=body.risk_level,
        risk_assessment_notes=body.risk_assessment_notes,
        created_by=current_user.user_id,
    )


@router.get("/governance")
def list_uae_governance(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _gov_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/governance/{gov_id}")
def get_uae_governance(
    gov_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _gov_svc.get(conn, gov_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Governance record not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec


@router.post("/governance/{gov_id}/seal")
def apply_uae_seal(
    gov_id: str,
    body: UAESealRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, str]:
    rec = _gov_svc.get(conn, gov_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Governance record not found.")
    _gov_svc.apply_seal(
        conn,
        gov_id,
        seal_reference=body.seal_reference,
        seal_category=body.seal_category,
        seal_expires_at=body.seal_expires_at,
    )
    return {"gov_id": gov_id, "ai_seal_applied": "true", "seal_reference": body.seal_reference}


# ── UAE PASS Signatures ────────────────────────────────────────────────────────


@router.post("/pass/sign", status_code=status.HTTP_201_CREATED)
def record_uae_pass_signature(
    body: UAEPassSignRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    return _pass_svc.record_signature(
        conn,
        organization_id=current_user.organization_id or "org_default",
        document_ref=body.document_ref,
        document_hash=body.document_hash,
        document_title=body.document_title,
        signatory_name=body.signatory_name,
        signatory_email=body.signatory_email,
        signatory_emirates_id=body.signatory_emirates_id,
        signatory_mobile=body.signatory_mobile,
        uae_pass_verified=body.uae_pass_verified,
        uae_pass_identity_level=body.uae_pass_identity_level,
        uae_pass_session_ref=body.uae_pass_session_ref,
        trust_service_provider=body.trust_service_provider,
        trust_service_level=body.trust_service_level,
        signature_format=body.signature_format,
        signature_level=body.signature_level,
        tsa_provider=body.tsa_provider,
        hdr_id=body.hdr_id,
    )


@router.get("/pass/sign")
def list_uae_pass_signatures(
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _pass_svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/pass/sign/{sig_id}")
def get_uae_pass_signature(
    sig_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    rec = _pass_svc.get(conn, sig_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="UAE PASS signature not found.")
    if rec.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return rec
