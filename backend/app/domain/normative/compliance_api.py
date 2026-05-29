"""Compliance & constitutional anchoring HTTP façade."""

from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.dependencies import database_dependency, get_current_user_record
from app.domain.mission.repository import MissionRepository
from app.domain.normative.anchoring_service import NormativeAnchoringService
from app.domain.normative.compliance_models import ComplianceReportSummary
from app.domain.normative.framework_models import NormativeFramework
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/compliance", tags=["compliance"])

_missions = MissionRepository()


def _anchoring(request: Request) -> NormativeAnchoringService:
    svc: NormativeAnchoringService | None = getattr(
        request.app.state, "anchoring_service", None
    )
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Anchoring service offline.",
        )
    return svc


@router.get("/frameworks", response_model=list[NormativeFramework])
def list_frameworks(
    anchoring: NormativeAnchoringService = Depends(_anchoring),
) -> list[NormativeFramework]:
    """List registered normative frameworks (LGPD, future GDPR, ISO, …)."""

    return anchoring.list_frameworks()


@router.get("/frameworks/{framework_id}", response_model=NormativeFramework)
def get_framework(
    framework_id: str,
    anchoring: NormativeAnchoringService = Depends(_anchoring),
) -> NormativeFramework:
    """Return a single framework definition."""

    framework = anchoring.get_framework(framework_id)
    if framework is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework not registered."
        )
    return framework


@router.post("/report/{mission_id}", response_model=ComplianceReportSummary)
def generate_compliance_report(
    mission_id: str,
    framework_id: str = Query(default="LGPD-BR"),
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
    anchoring: NormativeAnchoringService = Depends(_anchoring),
) -> ComplianceReportSummary:
    """Build a mission-level compliance report against the requested framework."""

    plan = _missions.fetch_plan(
        conn, mission_id, organization_id=current_user.organization_id
    )
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found."
        )

    try:
        return anchoring.generate_compliance_report(conn, mission_id, framework_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("/report/{mission_id}/download")
def download_compliance_report(
    mission_id: str,
    framework_id: str = Query(default="LGPD-BR"),
    conn=Depends(database_dependency),
    current_user: UserRecord = Depends(get_current_user_record),
    anchoring: NormativeAnchoringService = Depends(_anchoring),
) -> Response:
    """Download a minimal PDF summary (MVP) derived from the structured compliance report."""

    plan = _missions.fetch_plan(
        conn, mission_id, organization_id=current_user.organization_id
    )
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found."
        )

    try:
        summary = anchoring.generate_compliance_report(conn, mission_id, framework_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"compliance-{framework_id}-{mission_id}")
    height = A4[1]
    y = height - 72
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, y, "Heillon Legal — Relatório de conformidade")
    y -= 24
    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        72, y, f"Framework: {summary.framework_name} ({summary.framework_id})"
    )
    y -= 16
    pdf.drawString(72, y, f"Missão: {mission_id}")
    y -= 16
    pdf.drawString(72, y, f"Organização: {current_user.organization_id}")
    y -= 16
    pdf.drawString(72, y, f"HDRs analisados: {summary.total_hdrs}")
    y -= 16
    pdf.drawString(
        72, y, f"HDRs em conformidade (heurística): {summary.compliant_hdrs}"
    )
    y -= 24
    pdf.drawString(
        72,
        y,
        "Este relatório é um sumário técnico MVP — integrar selos PDF/A-3 na Fase 9.1.",
    )
    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    filename = f"compliance-{framework_id}-{mission_id}.pdf"
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
