"""UAE regulatory compliance services — Fase 19."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.uae.models import (
    UAE_AI_ETHICS_PRINCIPLES,
    DIFC_DP_REQUIREMENTS,
    UAEJurisdiction,
)
from app.domain.uae.repository import (
    UAEAIGovernanceRepository,
    UAEPDPLConsentRepository,
    UAEPassSignatureRepository,
)


# ── UAE PDPL Consent ──────────────────────────────────────────────────────────


class UAEPDPLConsentService:
    def __init__(self, repo: UAEPDPLConsentRepository | None = None) -> None:
        self._repo = repo or UAEPDPLConsentRepository()

    def record_consent(
        self,
        conn: Any,
        *,
        organization_id: str,
        data_subject_id: str,
        data_subject_name: str,
        data_subject_email: str = "",
        data_subject_nationality: str = "",
        data_categories: list[str] | None = None,
        processing_purposes: list[str] | None = None,
        legal_basis: str = "consent",
        sensitive_data_processing: bool = False,
        biometric_data: bool = False,
        health_data: bool = False,
        children_data: bool = False,
        guardian_consent_obtained: bool = False,
        cross_border_transfer: bool = False,
        transfer_destination_country: str | None = None,
        transfer_safeguards: str = "",
        difc_jurisdiction: bool = False,
        adgm_jurisdiction: bool = False,
        consent_text: str = "",
        ip_address: str | None = None,
        language: str = "en",
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        # PDPL guardrails
        warnings: list[str] = []
        if children_data and not guardian_consent_obtained:
            warnings.append(
                "PDPL Art. 11: Guardian consent required for processing children's data."
            )
        if cross_border_transfer and not transfer_safeguards:
            warnings.append(
                "PDPL Art. 26: Transfer safeguards required for cross-border data transfer."
            )
        if sensitive_data_processing and legal_basis != "consent":
            warnings.append(
                "PDPL Art. 9: Sensitive data processing generally requires explicit consent."
            )

        consent_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            consent_id=consent_id,
            organization_id=organization_id,
            data_subject_id=data_subject_id,
            data_subject_name=data_subject_name,
            data_subject_email=data_subject_email,
            data_subject_nationality=data_subject_nationality,
            data_categories=data_categories,
            processing_purposes=processing_purposes,
            legal_basis=legal_basis,
            sensitive_data_processing=sensitive_data_processing,
            biometric_data=biometric_data,
            health_data=health_data,
            children_data=children_data,
            guardian_consent_obtained=guardian_consent_obtained,
            cross_border_transfer=cross_border_transfer,
            transfer_destination_country=transfer_destination_country,
            transfer_safeguards=transfer_safeguards,
            difc_jurisdiction=difc_jurisdiction,
            adgm_jurisdiction=adgm_jurisdiction,
            consent_text=consent_text,
            ip_address=ip_address,
            language=language,
            expires_at=expires_at,
        )
        return {"consent_id": consent_id, "warnings": warnings}

    def get(self, conn: Any, consent_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, consent_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)

    def withdraw(self, conn: Any, consent_id: str, *, reason: str = "") -> None:
        self._repo.withdraw(conn, consent_id, reason=reason)


# ── UAE AI Governance ──────────────────────────────────────────────────────────


class UAEAIGovernanceService:
    def __init__(self, repo: UAEAIGovernanceRepository | None = None) -> None:
        self._repo = repo or UAEAIGovernanceRepository()

    def register(
        self,
        conn: Any,
        *,
        organization_id: str,
        ai_system_name: str,
        ai_system_version: str = "1.0",
        ai_system_purpose: str = "",
        ethics_human_centered: bool = False,
        ethics_fairness: bool = False,
        ethics_transparency: bool = False,
        ethics_safety_reliability: bool = False,
        ethics_privacy_security: bool = False,
        ethics_accountability: bool = False,
        ethics_sustainability: bool = False,
        sector: str = "legal",
        difc_compliant: bool = False,
        difc_registration_ref: str | None = None,
        adgm_compliant: bool = False,
        adgm_registration_ref: str | None = None,
        jurisdiction_ae: str = "federal",
        risk_level: str = "medium",
        risk_assessment_notes: str = "",
        created_by: str,
    ) -> dict[str, Any]:
        valid_jurisdictions = {j.value for j in UAEJurisdiction}
        if jurisdiction_ae not in valid_jurisdictions:
            raise ValueError(
                f"jurisdiction_ae must be one of {sorted(valid_jurisdictions)}"
            )

        gov_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            gov_id=gov_id,
            organization_id=organization_id,
            ai_system_name=ai_system_name,
            ai_system_version=ai_system_version,
            ai_system_purpose=ai_system_purpose,
            ethics_human_centered=ethics_human_centered,
            ethics_fairness=ethics_fairness,
            ethics_transparency=ethics_transparency,
            ethics_safety_reliability=ethics_safety_reliability,
            ethics_privacy_security=ethics_privacy_security,
            ethics_accountability=ethics_accountability,
            ethics_sustainability=ethics_sustainability,
            sector=sector,
            difc_compliant=difc_compliant,
            difc_registration_ref=difc_registration_ref,
            adgm_compliant=adgm_compliant,
            adgm_registration_ref=adgm_registration_ref,
            jurisdiction_ae=jurisdiction_ae,
            risk_level=risk_level,
            risk_assessment_notes=risk_assessment_notes,
            created_by=created_by,
        )

        # Ethics score
        ethics_flags = [
            ethics_human_centered,
            ethics_fairness,
            ethics_transparency,
            ethics_safety_reliability,
            ethics_privacy_security,
            ethics_accountability,
            ethics_sustainability,
        ]
        ethics_score = round(sum(1 for f in ethics_flags if f) / 7 * 100)

        return {
            "gov_id": gov_id,
            "jurisdiction_ae": jurisdiction_ae,
            "ethics_score": ethics_score,
            "seal_eligible": ethics_score
            >= 86,  # 6/7 principles → eligible for UAE AI Seal
        }

    def get(self, conn: Any, gov_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, gov_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)

    def apply_seal(
        self,
        conn: Any,
        gov_id: str,
        *,
        seal_reference: str,
        seal_category: str,
        seal_expires_at: str | None = None,
    ) -> None:
        self._repo.apply_seal(
            conn,
            gov_id,
            seal_reference=seal_reference,
            seal_category=seal_category,
            seal_expires_at=seal_expires_at,
        )

    @staticmethod
    def ethics_principles() -> dict[str, str]:
        return UAE_AI_ETHICS_PRINCIPLES

    @staticmethod
    def difc_requirements() -> dict[str, str]:
        return DIFC_DP_REQUIREMENTS


# ── UAE PASS Signatures ────────────────────────────────────────────────────────


class UAEPassSignatureService:
    def __init__(self, repo: UAEPassSignatureRepository | None = None) -> None:
        self._repo = repo or UAEPassSignatureRepository()

    def record_signature(
        self,
        conn: Any,
        *,
        organization_id: str,
        document_ref: str,
        document_hash: str,
        document_title: str = "",
        signatory_name: str,
        signatory_email: str,
        signatory_emirates_id: str | None = None,
        signatory_mobile: str | None = None,
        uae_pass_verified: bool = False,
        uae_pass_identity_level: str = "verified",
        uae_pass_session_ref: str | None = None,
        trust_service_provider: str = "",
        trust_service_level: str = "qualified",
        qtsp_country: str = "AE",
        signature_format: str = "PAdES-LTA",
        signature_level: str = "QES",
        signed_at: str | None = None,
        tsa_timestamp: str | None = None,
        tsa_provider: str | None = None,
        hdr_id: str | None = None,
    ) -> dict[str, str]:
        if len(document_hash) != 64:
            raise ValueError("document_hash must be a 64-character SHA-256 hex string.")
        sig_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            sig_id=sig_id,
            organization_id=organization_id,
            document_ref=document_ref,
            document_hash=document_hash,
            document_title=document_title,
            signatory_name=signatory_name,
            signatory_email=signatory_email,
            signatory_emirates_id=signatory_emirates_id,
            signatory_mobile=signatory_mobile,
            uae_pass_verified=uae_pass_verified,
            uae_pass_identity_level=uae_pass_identity_level,
            uae_pass_session_ref=uae_pass_session_ref,
            trust_service_provider=trust_service_provider,
            trust_service_level=trust_service_level,
            qtsp_country=qtsp_country,
            signature_format=signature_format,
            signature_level=signature_level,
            signed_at=signed_at,
            tsa_timestamp=tsa_timestamp,
            tsa_provider=tsa_provider,
            hdr_id=hdr_id,
        )
        return {"sig_id": sig_id, "signature_level": signature_level}

    def get(self, conn: Any, sig_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, sig_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)
