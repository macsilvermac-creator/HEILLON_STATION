"""Universal document signature lifecycle API — cross-jurisdiction.

Endpoints:
  POST   /signatures                          — record signature event
  GET    /signatures                          — list signatures (org)
  GET    /signatures/{sig_id}                 — get signature
  POST   /signatures/{sig_id}/acknowledge     — record delivery/receipt ack
  GET    /signatures/{sig_id}/acks            — list acknowledgments
  GET    /signatures/document/{document_hash} — all signatures for a document
  POST   /signatures/{sig_id}/revoke          — revoke signature (admin)
  GET    /signatures/standards                — list supported standards
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import database_dependency, get_current_user_record
from app.domain.signatures.services import DocumentSignatureService
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/signatures", tags=["signatures"])
_svc = DocumentSignatureService()


def _require_admin(current_user: UserRecord = Depends(get_current_user_record)) -> UserRecord:
    from app.domain.user.models import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only.")
    return current_user


# ── Schemas ────────────────────────────────────────────────────────────────────


class RecordSignatureRequest(BaseModel):
    document_ref: str = Field(..., min_length=1, max_length=300)
    document_hash: str = Field(..., min_length=64, max_length=64)
    document_title: str = Field(default="", max_length=500)
    document_type: str = Field(default="legal_document", max_length=100)
    signatory_name: str = Field(..., min_length=1, max_length=200)
    signatory_email: str = Field(..., max_length=200)
    signatory_role: str = Field(default="", max_length=100)
    jurisdiction: str = Field(
        default="BR", pattern="^(BR|EU|US|UAE|GLOBAL)$"
    )
    signature_standard: str = Field(
        default="ICP-Brasil",
        pattern="^(ICP-Brasil|eIDAS-QES|eIDAS-AES|ESIGN|UAE-PASS|Self-Signed)$",
    )
    signature_level: str = Field(
        default="QES", pattern="^(QES|AES|SES|advanced|basic)$"
    )
    certificate_issuer: str = Field(default="", max_length=500)
    certificate_serial: str = Field(default="", max_length=200)
    certificate_subject: str = Field(default="", max_length=500)
    certificate_valid_from: str | None = None
    certificate_valid_until: str | None = None
    signature_b64: str = Field(default="", max_length=65536)
    signature_format: str = Field(
        default="",
        pattern="^(PAdES-LTA|CAdES-LTA|XAdES-LTA|JAdES|PKCS7|raw|)$",
    )
    signed_at: str | None = None
    tsa_timestamp: str | None = None
    tsa_provider: str | None = None
    action: str = Field(
        default="signed",
        pattern="^(sent|delivered|received|signed|rejected|revoked)$",
    )
    hdr_id: str | None = None
    notes: str = Field(default="", max_length=2000)


class AcknowledgeRequest(BaseModel):
    acknowledged_name: str = Field(..., min_length=1, max_length=200)
    acknowledged_email: str = Field(default="", max_length=200)
    action: str = Field(
        default="received",
        pattern="^(received|reviewed|accepted|rejected|countersigned)$",
    )
    notes: str = Field(default="", max_length=2000)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
def record_signature(
    body: RecordSignatureRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    result = _svc.record_signature(
        conn,
        organization_id=current_user.organization_id or "org_default",
        document_ref=body.document_ref,
        document_hash=body.document_hash,
        document_title=body.document_title,
        document_type=body.document_type,
        signatory_id=current_user.user_id,
        signatory_name=body.signatory_name,
        signatory_email=body.signatory_email,
        signatory_role=body.signatory_role,
        jurisdiction=body.jurisdiction,
        signature_standard=body.signature_standard,
        signature_level=body.signature_level,
        certificate_issuer=body.certificate_issuer,
        certificate_serial=body.certificate_serial,
        certificate_subject=body.certificate_subject,
        certificate_valid_from=body.certificate_valid_from,
        certificate_valid_until=body.certificate_valid_until,
        signature_b64=body.signature_b64,
        signature_format=body.signature_format,
        signed_at=body.signed_at,
        tsa_timestamp=body.tsa_timestamp,
        tsa_provider=body.tsa_provider,
        action=body.action,
        hdr_id=body.hdr_id,
        notes=body.notes,
    )
    return result


@router.get("")
def list_signatures(
    jurisdiction: str | None = None,
    action: str | None = None,
    sig_status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    return _svc.list_by_org(
        conn,
        current_user.organization_id or "org_default",
        jurisdiction=jurisdiction,
        action=action,
        status=sig_status,
        skip=skip,
        limit=min(limit, 100),
    )


@router.get("/standards")
def list_standards() -> list[dict[str, str]]:
    """Return all supported signature standards — no auth required."""
    return DocumentSignatureService.supported_standards()


@router.get("/document/{document_hash}")
def list_by_document(
    document_hash: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    if len(document_hash) != 64:
        raise HTTPException(status_code=422, detail="document_hash must be 64 hex chars.")
    return _svc.list_by_document(conn, document_hash)


@router.get("/{sig_id}")
def get_signature(
    sig_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, Any]:
    record = _svc.get(conn, sig_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Signature not found.")
    if record.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return record


@router.post("/{sig_id}/acknowledge", status_code=status.HTTP_201_CREATED)
def acknowledge_signature(
    sig_id: str,
    body: AcknowledgeRequest,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> dict[str, str]:
    record = _svc.get(conn, sig_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Signature not found.")
    if record.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return _svc.acknowledge(
        conn,
        sig_id=sig_id,
        acknowledged_by=current_user.user_id,
        acknowledged_name=body.acknowledged_name,
        acknowledged_email=body.acknowledged_email,
        action=body.action,
        notes=body.notes,
    )


@router.get("/{sig_id}/acks")
def list_acks(
    sig_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
) -> list[dict[str, Any]]:
    record = _svc.get(conn, sig_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Signature not found.")
    if record.get("organization_id") != (current_user.organization_id or "org_default"):
        raise HTTPException(status_code=403, detail="Forbidden.")
    return _svc.list_acks(conn, sig_id)


@router.post("/{sig_id}/revoke")
def revoke_signature(
    sig_id: str,
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(_require_admin),
) -> dict[str, str]:
    record = _svc.get(conn, sig_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Signature not found.")
    _svc.revoke(conn, sig_id)
    return {"sig_id": sig_id, "status": "revoked"}
