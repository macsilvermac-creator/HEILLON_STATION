"""Universal document signature lifecycle service."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.signatures.models import (
    STANDARD_DEFAULT_FORMAT,
    SIGNATURE_LEGAL_VALUE,
    SignatureStandard,
)
from app.domain.signatures.repository import DocumentSignatureRepository


class DocumentSignatureService:
    """Manage document send / deliver / receive / sign lifecycle across jurisdictions."""

    def __init__(self, repo: DocumentSignatureRepository | None = None) -> None:
        self._repo = repo or DocumentSignatureRepository()

    def record_signature(
        self,
        conn: Any,
        *,
        organization_id: str,
        document_ref: str,
        document_hash: str,
        document_title: str = "",
        document_type: str = "legal_document",
        signatory_id: str,
        signatory_name: str,
        signatory_email: str,
        signatory_role: str = "",
        jurisdiction: str = "BR",
        signature_standard: str = "ICP-Brasil",
        signature_level: str = "QES",
        certificate_issuer: str = "",
        certificate_serial: str = "",
        certificate_subject: str = "",
        certificate_valid_from: str | None = None,
        certificate_valid_until: str | None = None,
        signature_b64: str = "",
        signature_format: str = "",
        signed_at: str | None = None,
        tsa_timestamp: str | None = None,
        tsa_provider: str | None = None,
        action: str = "signed",
        hdr_id: str | None = None,
        ip_address: str | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        """Record a document signature event. Returns sig_id + legal_value."""
        if len(document_hash) != 64:
            raise ValueError("document_hash must be a 64-character SHA-256 hex string.")

        # Derive default format from standard if not supplied
        resolved_format = signature_format or STANDARD_DEFAULT_FORMAT.get(
            signature_standard, "PAdES-LTA"
        )

        sig_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            sig_id=sig_id,
            organization_id=organization_id,
            document_ref=document_ref,
            document_hash=document_hash,
            document_title=document_title,
            document_type=document_type,
            signatory_id=signatory_id,
            signatory_name=signatory_name,
            signatory_email=signatory_email,
            signatory_role=signatory_role,
            jurisdiction=jurisdiction,
            signature_standard=signature_standard,
            signature_level=signature_level,
            certificate_issuer=certificate_issuer,
            certificate_serial=certificate_serial,
            certificate_subject=certificate_subject,
            certificate_valid_from=certificate_valid_from,
            certificate_valid_until=certificate_valid_until,
            signature_b64=signature_b64,
            signature_format=resolved_format,
            signed_at=signed_at,
            tsa_timestamp=tsa_timestamp,
            tsa_provider=tsa_provider,
            action=action,
            hdr_id=hdr_id,
            ip_address=ip_address,
            notes=notes,
        )

        # Informative legal value
        jur_values = SIGNATURE_LEGAL_VALUE.get(jurisdiction, {})
        legal_value = jur_values.get(signature_level, "")

        return {
            "sig_id": sig_id,
            "action": action,
            "jurisdiction": jurisdiction,
            "signature_standard": signature_standard,
            "signature_level": signature_level,
            "signature_format": resolved_format,
            "legal_value": legal_value,
        }

    def acknowledge(
        self,
        conn: Any,
        *,
        sig_id: str,
        acknowledged_by: str,
        acknowledged_name: str,
        acknowledged_email: str = "",
        action: str = "received",
        ip_address: str | None = None,
        notes: str = "",
    ) -> dict[str, str]:
        """Record a delivery/receipt acknowledgment. Returns ack_id + ack_hash."""
        ack_id = str(uuid.uuid4())
        ack_hash = self._repo.create_ack(
            conn,
            ack_id=ack_id,
            sig_id=sig_id,
            acknowledged_by=acknowledged_by,
            acknowledged_name=acknowledged_name,
            acknowledged_email=acknowledged_email,
            action=action,
            ip_address=ip_address,
            notes=notes,
        )
        return {"ack_id": ack_id, "ack_hash": ack_hash, "action": action}

    def get(self, conn: Any, sig_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, sig_id)

    def list_by_org(
        self,
        conn: Any,
        organization_id: str,
        *,
        jurisdiction: str | None = None,
        action: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(
            conn, organization_id,
            jurisdiction=jurisdiction, action=action, status=status,
            skip=skip, limit=limit,
        )

    def list_by_document(
        self, conn: Any, document_hash: str
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_document_hash(conn, document_hash)

    def list_acks(self, conn: Any, sig_id: str) -> list[dict[str, Any]]:
        return self._repo.list_acks(conn, sig_id)

    def revoke(self, conn: Any, sig_id: str) -> None:
        self._repo.update_status(conn, sig_id, "revoked")

    @staticmethod
    def supported_standards() -> list[dict[str, str]]:
        """Return all supported signature standards with jurisdiction info."""
        return [
            {
                "standard": "ICP-Brasil",
                "jurisdiction": "BR",
                "levels": "QES (A3), AES (A1)",
                "formats": "PAdES-LTA, CAdES-LTA",
                "regulation": "MP 2.200-2/2001 + ITI",
            },
            {
                "standard": "eIDAS-QES",
                "jurisdiction": "EU",
                "levels": "QES, AES, SES",
                "formats": "PAdES-LTA, CAdES-LTA, XAdES-LTA",
                "regulation": "Reg. (EU) 2024/1183 (eIDAS 2.0)",
            },
            {
                "standard": "ESIGN",
                "jurisdiction": "US",
                "levels": "advanced, basic",
                "formats": "PAdES-LTA, PKCS7",
                "regulation": "ESIGN Act 2000 + UETA 1999",
            },
            {
                "standard": "UAE-PASS",
                "jurisdiction": "UAE",
                "levels": "QES (qualified), AES",
                "formats": "PAdES-LTA, CAdES-LTA",
                "regulation": "UAE Cabinet Resolution 22/2017 + TDRA",
            },
        ]
