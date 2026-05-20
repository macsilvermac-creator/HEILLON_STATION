"""Forensic package generation and artefact dissemination."""

from __future__ import annotations

import json

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse

from app.dependencies import database_dependency
from app.domain.forensic.models import AuditManifest, ForensicPackage, ForensicPackageStatus
from app.domain.forensic.repository import ForensicRepository
from app.domain.forensic.services import ForensicPackageService

router = APIRouter(prefix="/forensic", tags=["forensic"])

_repository_singleton = ForensicRepository()


def get_forensic_package_service(request: Request) -> ForensicPackageService:
    """Resolve singleton forensic assembler registered during lifespan."""

    svc = getattr(request.app.state, "forensic_service", None)
    if svc is None:
        msg = "Forensic package engine not initialized."
        raise RuntimeError(msg)
    return svc


@router.post("/package/{mission_id}", response_model=ForensicPackage)
def generate_forensic_package(
    mission_id: str,
    generated_by: str = "perito_default",
    conn=Depends(database_dependency),
    service: ForensicPackageService = Depends(get_forensic_package_service),
) -> ForensicPackage:
    """Mint a courtroom-ready dossier anchored to deterministic HDR lineage."""

    try:
        dossier = service.generate_package(conn, mission_id, generated_by=generated_by)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return dossier


@router.get("/package/{package_id}", response_model=ForensicPackage)
def get_package_metadata(
    package_id: str,
    conn=Depends(database_dependency),
) -> ForensicPackage:
    """Return persisted forensic dossier metadata with manifest envelope."""

    row = _repository_singleton.fetch_row(conn, package_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forensic dossier unavailable.")

    manifest = AuditManifest.model_validate_json(row["manifest_json"])

    pkg = ForensicPackage(
        package_id=package_id,
        mission_id=row["mission_id"],
        status=ForensicPackageStatus(row["status"]),
        manifest=manifest,
        pdf_checksum=row["pdf_checksum"],
        json_chain_checksum=row["json_chain_checksum"],
        created_at=manifest.generated_at,
        download_url=f"/api/v1/forensic/package/{package_id}/download/manifest",
    )
    return pkg


@router.get("/package/{package_id}/download/pdf")
def download_pdf(
    package_id: str,
    conn=Depends(database_dependency),
) -> FileResponse:
    """Download executive summary stub slated for eventual PDF/A hardening."""

    row = _repository_singleton.fetch_row(conn, package_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forensic dossier unavailable.")

    path_pdf = Path(row["pdf_path"])
    media_type = "application/pdf" if path_pdf.suffix.lower() == ".pdf" else "text/plain; charset=utf-8"
    download_name = f"{package_id}{path_pdf.suffix}"

    return FileResponse(
        path_pdf.as_posix(),
        media_type=media_type,
        filename=download_name,
    )


@router.get("/package/{package_id}/download/json")
def download_json_chain(
    package_id: str,
    conn=Depends(database_dependency),
) -> FileResponse:
    """Download cryptographic HDR lineage attachments."""

    row = _repository_singleton.fetch_row(conn, package_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forensic dossier unavailable.")

    return FileResponse(
        row["json_chain_path"],
        media_type="application/json",
        filename=f"{package_id}_chain.json",
    )


@router.get("/package/{package_id}/download/manifest")
def download_manifest(
    package_id: str,
    conn=Depends(database_dependency),
) -> JSONResponse:
    """Expose integrity manifest for independent verification."""

    row = _repository_singleton.fetch_row(conn, package_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forensic dossier unavailable.")

    manifest_payload = json.loads(row["manifest_json"])
    return JSONResponse(content=manifest_payload)
