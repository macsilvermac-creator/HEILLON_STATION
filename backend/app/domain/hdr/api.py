"""Public verification endpoints for HDR artefacts."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import database_dependency, hdr_service_dependency
from app.domain.hdr.repository import HDRRepository
from app.domain.hdr.schemas import ChainVerificationResponse, VerificationDetailReport, VerificationResponse
from app.domain.hdr.services import HDRService

router = APIRouter(prefix="/verify", tags=["verification"])

_hdr_repository = HDRRepository()


@router.get("/chain/{mission_id}", response_model=ChainVerificationResponse)
def verify_chain(
    mission_id: str,
    conn=Depends(database_dependency),
    svc: HDRService = Depends(hdr_service_dependency),
) -> ChainVerificationResponse:
    """Expose mission-level cryptographic lineage diagnostics."""

    chain = _hdr_repository.fetch_mission_chain(conn, mission_id)
    if not chain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not archived.")

    report = svc.verify_chain(chain)

    integrity = "validated" if report.valid else "compromised"
    timestamp_gate = integrity
    chain_gate = "linear" if report.valid else "fractured"

    return ChainVerificationResponse(
        valid=report.valid,
        mission_id=mission_id,
        integrity_status=integrity,
        timestamp_status=timestamp_gate,
        chain_status=chain_gate,
        chained_hdr_count=len(chain),
        verification=report.details,
    )


@router.get("/{hdr_id}", response_model=VerificationResponse)
def verify_hdr(
    hdr_id: str,
    conn=Depends(database_dependency),
    svc: HDRService = Depends(hdr_service_dependency),
) -> VerificationResponse:
    """Verify solitary HDR artefacts without authentication hurdles."""

    record = _hdr_repository.fetch_hdr(conn, hdr_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HDR unknown.")

    valid = svc.verify_single_hdr(record)

    steps = [
        f"Canonical digest {'validated' if valid else 'tampered'} against custody manifest.",
        f"RFC3161 imprint binding {'trusted' if valid else 'broken'}.",
    ]

    detail = VerificationDetailReport(steps=steps)

    return VerificationResponse(
        valid=valid,
        hdr_id=hdr_id,
        integrity_status="validated" if valid else "compromised",
        timestamp_status="trusted" if valid else "invalid",
        chain_status="singular",
        details=detail,
    )
