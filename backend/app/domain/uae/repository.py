"""UAE regulatory compliance repository layer."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── UAE PDPL Consent ──────────────────────────────────────────────────────────


class UAEPDPLConsentRepository:
    def create(
        self,
        conn: Any,
        *,
        consent_id: str,
        organization_id: str = "org_default",
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
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO uae_pdpl_consent (
                consent_id, organization_id,
                data_subject_id, data_subject_name, data_subject_email,
                data_subject_nationality, data_categories, processing_purposes,
                legal_basis, sensitive_data_processing, biometric_data,
                health_data, children_data, guardian_consent_obtained,
                cross_border_transfer, transfer_destination_country, transfer_safeguards,
                difc_jurisdiction, adgm_jurisdiction,
                consent_text, ip_address, language,
                status, expires_at, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                consent_id,
                organization_id,
                data_subject_id,
                data_subject_name,
                data_subject_email,
                data_subject_nationality,
                json.dumps(data_categories or []),
                json.dumps(processing_purposes or []),
                legal_basis,
                int(sensitive_data_processing),
                int(biometric_data),
                int(health_data),
                int(children_data),
                int(guardian_consent_obtained),
                int(cross_border_transfer),
                transfer_destination_country,
                transfer_safeguards,
                int(difc_jurisdiction),
                int(adgm_jurisdiction),
                consent_text,
                ip_address,
                language,
                "active",
                expires_at,
                now,
                now,
            ),
        )

    def get(self, conn: Any, consent_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM uae_pdpl_consent WHERE consent_id=?", (consent_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM uae_pdpl_consent
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def withdraw(self, conn: Any, consent_id: str, *, reason: str = "") -> None:
        now = _now()
        conn.execute(
            """UPDATE uae_pdpl_consent
               SET status='withdrawn', withdrawn_at=?, withdrawal_reason=?, updated_at=?
               WHERE consent_id=?""",
            (now, reason, now, consent_id),
        )


# ── UAE AI Governance ──────────────────────────────────────────────────────────


class UAEAIGovernanceRepository:
    def create(
        self,
        conn: Any,
        *,
        gov_id: str,
        organization_id: str = "org_default",
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
        ai_seal_applied: bool = False,
        ai_seal_reference: str | None = None,
        ai_seal_category: str | None = None,
        sector: str = "legal",
        difc_compliant: bool = False,
        difc_registration_ref: str | None = None,
        adgm_compliant: bool = False,
        adgm_registration_ref: str | None = None,
        jurisdiction_ae: str = "federal",
        risk_level: str = "medium",
        risk_assessment_notes: str = "",
        created_by: str,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO uae_ai_governance (
                gov_id, organization_id, ai_system_name, ai_system_version, ai_system_purpose,
                ethics_human_centered, ethics_fairness, ethics_transparency,
                ethics_safety_reliability, ethics_privacy_security,
                ethics_accountability, ethics_sustainability,
                ai_seal_applied, ai_seal_reference, ai_seal_category,
                sector, difc_compliant, difc_registration_ref, difc_dp_law_version,
                adgm_compliant, adgm_registration_ref,
                jurisdiction_ae, risk_level, risk_assessment_notes,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                gov_id,
                organization_id,
                ai_system_name,
                ai_system_version,
                ai_system_purpose,
                int(ethics_human_centered),
                int(ethics_fairness),
                int(ethics_transparency),
                int(ethics_safety_reliability),
                int(ethics_privacy_security),
                int(ethics_accountability),
                int(ethics_sustainability),
                int(ai_seal_applied),
                ai_seal_reference,
                ai_seal_category,
                sector,
                int(difc_compliant),
                difc_registration_ref,
                "2020",
                int(adgm_compliant),
                adgm_registration_ref,
                jurisdiction_ae,
                risk_level,
                risk_assessment_notes,
                "active",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, gov_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM uae_ai_governance WHERE gov_id=?", (gov_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM uae_ai_governance
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def apply_seal(
        self,
        conn: Any,
        gov_id: str,
        *,
        seal_reference: str,
        seal_category: str,
        seal_expires_at: str | None = None,
    ) -> None:
        now = _now()
        conn.execute(
            """UPDATE uae_ai_governance
               SET ai_seal_applied=1, ai_seal_reference=?, ai_seal_issued_at=?,
                   ai_seal_expires_at=?, ai_seal_category=?, updated_at=?
               WHERE gov_id=?""",
            (seal_reference, now, seal_expires_at, seal_category, now, gov_id),
        )


# ── UAE PASS Signatures ────────────────────────────────────────────────────────


class UAEPassSignatureRepository:
    def create(
        self,
        conn: Any,
        *,
        sig_id: str,
        organization_id: str = "org_default",
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
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO uae_pass_signatures (
                sig_id, organization_id, document_ref, document_hash, document_title,
                signatory_name, signatory_email, signatory_emirates_id, signatory_mobile,
                uae_pass_verified, uae_pass_identity_level, uae_pass_session_ref,
                trust_service_provider, trust_service_level, qtsp_country,
                signature_format, signature_level,
                signed_at, tsa_timestamp, tsa_provider, hdr_id,
                status, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sig_id,
                organization_id,
                document_ref,
                document_hash,
                document_title,
                signatory_name,
                signatory_email,
                signatory_emirates_id,
                signatory_mobile,
                int(uae_pass_verified),
                uae_pass_identity_level,
                uae_pass_session_ref,
                trust_service_provider,
                trust_service_level,
                qtsp_country,
                signature_format,
                signature_level,
                signed_at or now,
                tsa_timestamp,
                tsa_provider,
                hdr_id,
                "valid",
                now,
            ),
        )

    def get(self, conn: Any, sig_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM uae_pass_signatures WHERE sig_id=?", (sig_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM uae_pass_signatures
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]
