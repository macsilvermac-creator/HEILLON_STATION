"""Universal document signature repository."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class DocumentSignatureRepository:
    """CRUD for ``document_signatures`` + ``signature_acknowledgments``."""

    # ── Signatures ────────────────────────────────────────────────────────────

    def create(
        self,
        conn: Any,
        *,
        sig_id: str,
        organization_id: str = "org_default",
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
        tsa_serial: str | None = None,
        action: str = "signed",
        status: str = "valid",
        hdr_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        notes: str = "",
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO document_signatures (
                sig_id, organization_id, document_ref, document_hash,
                document_title, document_type,
                signatory_id, signatory_name, signatory_email, signatory_role,
                jurisdiction, signature_standard, signature_level,
                certificate_issuer, certificate_serial, certificate_subject,
                certificate_valid_from, certificate_valid_until,
                signature_b64, signature_format,
                signed_at, tsa_timestamp, tsa_provider, tsa_serial,
                action, status, hdr_id, ip_address, user_agent, notes,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sig_id, organization_id, document_ref, document_hash,
                document_title, document_type,
                signatory_id, signatory_name, signatory_email, signatory_role,
                jurisdiction, signature_standard, signature_level,
                certificate_issuer, certificate_serial, certificate_subject,
                certificate_valid_from, certificate_valid_until,
                signature_b64, signature_format,
                signed_at or now, tsa_timestamp, tsa_provider, tsa_serial,
                action, status, hdr_id, ip_address, user_agent, notes,
                now, now,
            ),
        )

    def get(self, conn: Any, sig_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM document_signatures WHERE sig_id=?", (sig_id,)
        ).fetchone()
        return dict(row) if row else None

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
        conditions = ["organization_id=?"]
        params: list[Any] = [organization_id]
        if jurisdiction:
            conditions.append("jurisdiction=?")
            params.append(jurisdiction)
        if action:
            conditions.append("action=?")
            params.append(action)
        if status:
            conditions.append("status=?")
            params.append(status)
        where = " AND ".join(conditions)
        params.extend([limit, skip])
        rows = conn.execute(
            f"SELECT * FROM document_signatures WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_document_hash(
        self, conn: Any, document_hash: str
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM document_signatures WHERE document_hash=? ORDER BY created_at ASC",
            (document_hash,),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, conn: Any, sig_id: str, status: str) -> None:
        now = _now()
        conn.execute(
            "UPDATE document_signatures SET status=?, updated_at=? WHERE sig_id=?",
            (status, now, sig_id),
        )

    # ── Acknowledgments ────────────────────────────────────────────────────────

    def create_ack(
        self,
        conn: Any,
        *,
        ack_id: str,
        sig_id: str,
        acknowledged_by: str,
        acknowledged_name: str,
        acknowledged_email: str = "",
        action: str = "received",
        tsa_timestamp: str | None = None,
        ip_address: str | None = None,
        notes: str = "",
    ) -> str:
        """Create an acknowledgment and return its integrity hash."""
        now = _now()
        ack_hash = hashlib.sha256(
            f"{sig_id}:{acknowledged_by}:{action}:{now}".encode()
        ).hexdigest()
        conn.execute(
            """INSERT INTO signature_acknowledgments (
                ack_id, sig_id, acknowledged_by, acknowledged_name,
                acknowledged_email, action, ack_hash,
                tsa_timestamp, ip_address, notes, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ack_id, sig_id, acknowledged_by, acknowledged_name,
                acknowledged_email, action, ack_hash,
                tsa_timestamp, ip_address, notes, now,
            ),
        )
        return ack_hash

    def list_acks(self, conn: Any, sig_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM signature_acknowledgments WHERE sig_id=? ORDER BY created_at ASC",
            (sig_id,),
        ).fetchall()
        return [dict(r) for r in rows]
