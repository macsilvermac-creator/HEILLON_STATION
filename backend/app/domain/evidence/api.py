"""Evidence ingestion surface producing immutable HDR artefacts."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.dependencies import (
    database_dependency,
    get_current_user_record,
    hdr_service_dependency,
)
from app.core import config as runtime_config
from app.core.security import generate_hash
from app.domain.hdr.repository import HDRRepository
from app.domain.hdr.services import HDRService
from app.domain.tier.dependencies import enforce_hdr_quota
from app.domain.tier.models import QuotaSnapshot
from app.domain.user.models import UserRecord
from app.domain.evidence.extractor import extract_text
from app.domain.evidence.models import IngestionResponse
from app.domain.evidence.repository import EvidenceRepository
from app.domain.evidence.services import build_ingestion_hdr

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

_hdr_repository = HDRRepository()
_evidence_filesystem = EvidenceRepository()

# DoS protection: cap upload at 50 MB and gate by MIME allowlist
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # .doc legacy
        "text/plain",
        "text/csv",
        "image/png",
        "image/jpeg",
        "image/webp",
        "application/json",
        "application/zip",
        "application/octet-stream",  # fallback for forensic raw artefacts
    }
)


@router.post("", response_model=IngestionResponse)
async def ingest_evidence_file(
    file: UploadFile = File(description="Evidence binary submitted for hashing."),
    mission_id: str | None = Form(
        default=None,
        description="Optional mission discriminator; synthesized when omitted.",
    ),
    previous_hdr: str | None = Form(
        default=None,
        description="Optional predecessor hdr_id to extend append-only custody.",
    ),
    conn=Depends(database_dependency),
    hdr_service: HDRService = Depends(hdr_service_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
    quota: QuotaSnapshot = Depends(enforce_hdr_quota),  # 402 if exceeded
) -> IngestionResponse:
    """Hash evidence bytes, persist WORM artefacts, mint HDR ingestion record.

    Quota: each successful ingestion counts as 1 HDR against the org's monthly
    limit. Returns HTTP 402 Payment Required if the org has exhausted its tier.
    """

    settings = runtime_config.get_settings()

    # SECURITY: validate MIME type before reading bytes (defense against DoS)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Content-Type '{file.content_type}' não permitido. "
                f"Tipos aceites: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            ),
        )

    inferred_mission_id = mission_id or f"mission_{uuid4()}"
    # SECURITY: bounded read to prevent memory-exhaustion DoS
    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    checksum = generate_hash(file_bytes)
    extracted_text = await run_in_threadpool(
        extract_text, file.filename or "", file_bytes
    )

    if previous_hdr:
        predecessor = _hdr_repository.fetch_hdr(conn, previous_hdr)
        if predecessor is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="previous_hdr not found.",
            )

        prev_org = _hdr_repository.fetch_hdr_organization_id(conn, previous_hdr)
        if prev_org is None or prev_org != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="previous_hdr belongs to another organization.",
            )
        if mission_id and predecessor.mission_id != inferred_mission_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="previous_hdr does not belong to the specified mission.",
            )

    _evidence_id, canonical_path = _evidence_filesystem.reserve_target(
        settings.EVIDENCE_DIR,
        file.filename or "evidence.bin",
    )

    await run_in_threadpool(canonical_path.write_bytes, file_bytes)

    hdr = build_ingestion_hdr(
        hdr_service,
        sanitized_name=canonical_path.name,
        inferred_mission_id=inferred_mission_id,
        checksum=checksum,
        previous_hdr=previous_hdr,
        extracted_text=extracted_text,
    )

    _hdr_repository.insert(conn, hdr, organization_id=current_user.organization_id)

    return IngestionResponse(
        hdr=hdr, evidence_storage_path=str(canonical_path.resolve())
    )
