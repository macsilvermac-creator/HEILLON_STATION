"""FastAPI router for the privacy bounded context (LGPD Fase 14).

Endpoints:
  GET  /privacy/dpo-contact          — public DPO contact (no auth)
  POST /privacy/dpo-request          — submit data subject request (no auth)
  GET  /privacy/dpo-requests         — list requests (admin)
  PUT  /privacy/dpo-requests/{id}    — update request (admin)
  GET  /privacy/consent              — get my consent bundle
  POST /privacy/consent              — set / update consent
  DELETE /privacy/consent            — revoke all consent
  GET  /privacy/export               — portability export (ZIP)
  POST /privacy/ripd                 — create RIPD report
  GET  /privacy/ripd                 — list RIPD reports
  GET  /privacy/ripd/{id}            — get RIPD report
  GET  /privacy/ripd/{id}/download   — download RIPD PDF
  POST /security/incident            — register security incident
  GET  /security/incidents           — list incidents (admin)
  PUT  /security/incidents/{id}      — update incident (admin)
  GET  /security/incidents/{id}/notification — ANPD notification draft
  POST /privacy/purge-logs           — run Marco Civil log purge (admin)
"""

from __future__ import annotations

import io
import json
import zipfile
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse

from app.dependencies import (
    database_dependency,
    get_current_user_record,
    resolve_mission_actor,
    settings_dependency,
    MissionActor,
)
from app.core.config import Settings
from app.db.compat import CompatConnection
from app.domain.privacy.models import (
    ConsentBundle,
    ConsentRecord,
    ConsentUpdate,
    DPOContact,
    DPORequest,
    DPORequestCreate,
    DPORequestStatus,
    DPORequestUpdate,
    IncidentCreate,
    IncidentStatus,
    IncidentUpdate,
    PurgeStats,
    RIPDCreate,
    RIPDReport,
    SecurityIncident,
)
from app.domain.privacy.services import (
    AccessLogService,
    ConsentService,
    DPOService,
    IncidentService,
    RIPDService,
)
from app.domain.user.models import UserRecord

router = APIRouter(tags=["privacy"])

# ── service singletons (stateless — safe) ─────────────────────────────────────

_ripd_svc = RIPDService()
_incident_svc = IncidentService()
_consent_svc = ConsentService()
_access_log_svc = AccessLogService()


def _get_dpo_service(settings: Settings) -> DPOService:
    """Build DPO service from environment settings."""
    return DPOService(
        dpo_name=getattr(settings, "DPO_NAME", "Encarregado de Dados"),
        dpo_email=getattr(settings, "DPO_EMAIL", "dpo@heillon.com"),
        organization_name="Heillon Legal",
        public_base_url=settings.VERIFICATION_PUBLIC_BASE,
    )


def _require_admin(user: UserRecord) -> UserRecord:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a administradores.")
    return user


# ─────────────────────────────────────────────────────────────────────────────
# DPO Contact (PUBLIC — no auth)
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/privacy/dpo-contact",
    response_model=DPOContact,
    summary="Contacto público do DPO (LGPD art. 41)",
)
def dpo_contact(settings: Annotated[Settings, Depends(settings_dependency)]) -> DPOContact:
    """Return public DPO contact information — no authentication required."""
    return _get_dpo_service(settings).contact


# ─────────────────────────────────────────────────────────────────────────────
# DPO Requests (titulares — no auth for submission)
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/privacy/dpo-request",
    response_model=DPORequest,
    status_code=status.HTTP_201_CREATED,
    summary="Submeter solicitação de direitos do titular (LGPD art. 18)",
)
def submit_dpo_request(
    body: DPORequestCreate,
    request: Request,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    settings: Annotated[Settings, Depends(settings_dependency)],
) -> DPORequest:
    dpo_svc = _get_dpo_service(settings)
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else None)
    ua = request.headers.get("user-agent")
    return dpo_svc.submit_request(
        conn,
        organization_id=settings.DEFAULT_ORGANIZATION_ID,
        payload=body,
        ip_address=ip,
        user_agent=ua,
    )


@router.get(
    "/privacy/dpo-requests",
    response_model=list[DPORequest],
    summary="Listar solicitações DPO (admin)",
)
def list_dpo_requests(
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
    settings: Annotated[Settings, Depends(settings_dependency)],
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[DPORequest]:
    _require_admin(user)
    dpo_svc = _get_dpo_service(settings)
    return dpo_svc.list_requests(
        conn,
        organization_id=user.organization_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/privacy/dpo-requests/{request_id}",
    response_model=DPORequest,
    summary="Atualizar solicitação DPO (admin)",
)
def update_dpo_request(
    request_id: str,
    body: DPORequestUpdate,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
    settings: Annotated[Settings, Depends(settings_dependency)],
) -> DPORequest:
    _require_admin(user)
    dpo_svc = _get_dpo_service(settings)
    req = dpo_svc.update_request(
        conn,
        request_id=request_id,
        organization_id=user.organization_id,
        update=body,
    )
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada.")
    return req


# ─────────────────────────────────────────────────────────────────────────────
# Consent (authenticated user)
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/privacy/consent",
    response_model=ConsentBundle,
    summary="Obter bundle de consentimentos do utilizador",
)
def get_consent(
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> ConsentBundle:
    return _consent_svc.get_bundle(conn, user_id=user.user_id, organization_id=user.organization_id)


@router.post(
    "/privacy/consent",
    response_model=ConsentRecord,
    summary="Atualizar consentimento para uma finalidade",
)
def set_consent(
    body: ConsentUpdate,
    request: Request,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> ConsentRecord:
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else None)
    ua = request.headers.get("user-agent")
    return _consent_svc.set_consent(
        conn,
        user_id=user.user_id,
        organization_id=user.organization_id,
        update=body,
        ip_address=ip,
        user_agent=ua,
    )


@router.delete(
    "/privacy/consent",
    response_model=list[ConsentRecord],
    summary="Revogar todo o consentimento (LGPD art. 8 §5)",
)
def revoke_all_consent(
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> list[ConsentRecord]:
    return _consent_svc.revoke_all(conn, user_id=user.user_id, organization_id=user.organization_id)


# ─────────────────────────────────────────────────────────────────────────────
# Data portability export (LGPD art. 18 V)
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/privacy/export",
    summary="Exportar todos os dados do titular (portabilidade LGPD art. 18 V)",
)
def export_user_data(
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> Response:
    """Return ZIP with all personal data for the authenticated user."""
    bundle = _consent_svc.get_bundle(conn, user_id=user.user_id, organization_id=user.organization_id)

    user_data = {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "organization_id": user.organization_id,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
    consent_data = [r.model_dump(mode="json") for r in bundle.records]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("profile.json", json.dumps(user_data, indent=2, ensure_ascii=False))
        zf.writestr("consent.json", json.dumps(consent_data, indent=2, ensure_ascii=False))
        zf.writestr(
            "README.txt",
            "Exportação de dados pessoais — Heillon Legal (LGPD art. 18 V)\n"
            f"Gerado em: {__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}\n"
            "Este arquivo contém todos os dados pessoais associados à sua conta.\n",
        )
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="heillon_export_{user.user_id[:8]}.zip"'},
    )


# ─────────────────────────────────────────────────────────────────────────────
# RIPD (authenticated — any role can create; admin can list all)
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/privacy/ripd",
    response_model=RIPDReport,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Relatório de Impacto à Proteção de Dados (LGPD art. 38)",
)
def create_ripd(
    body: RIPDCreate,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
    settings: Annotated[Settings, Depends(settings_dependency)],
) -> RIPDReport:
    dpo_svc = _get_dpo_service(settings)
    return _ripd_svc.create(
        conn,
        organization_id=user.organization_id,
        created_by=user.user_id,
        payload=body,
        dpo_name=dpo_svc.dpo_name,
        dpo_email=dpo_svc.dpo_email,
    )


@router.get(
    "/privacy/ripd",
    response_model=list[RIPDReport],
    summary="Listar RIPDs da organização",
)
def list_ripd(
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[RIPDReport]:
    return _ripd_svc.list_by_org(conn, organization_id=user.organization_id, limit=limit, offset=offset)


@router.get(
    "/privacy/ripd/{ripd_id}",
    response_model=RIPDReport,
    summary="Obter RIPD por ID",
)
def get_ripd(
    ripd_id: str,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> RIPDReport:
    report = _ripd_svc.get(conn, ripd_id=ripd_id, organization_id=user.organization_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RIPD não encontrado.")
    return report


@router.get(
    "/privacy/ripd/{ripd_id}/download",
    summary="Descarregar RIPD em PDF",
)
def download_ripd(
    ripd_id: str,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
    settings: Annotated[Settings, Depends(settings_dependency)],
) -> Response:
    report = _ripd_svc.get(conn, ripd_id=ripd_id, organization_id=user.organization_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RIPD não encontrado.")
    pdf_bytes = _ripd_svc.generate_pdf(report)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ripd_{ripd_id[:14]}.pdf"'},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Security Incidents (ANPD Res. 15/2024)
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/security/incident",
    response_model=SecurityIncident,
    status_code=status.HTTP_201_CREATED,
    summary="Registar incidente de segurança (ANPD Res. 15/2024)",
)
def register_incident(
    body: IncidentCreate,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> SecurityIncident:
    return _incident_svc.register(
        conn,
        organization_id=user.organization_id,
        detected_by=user.user_id,
        payload=body,
    )


@router.get(
    "/security/incidents",
    response_model=list[SecurityIncident],
    summary="Listar incidentes de segurança (admin)",
)
def list_incidents(
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[SecurityIncident]:
    _require_admin(user)
    return _incident_svc.list_by_org(conn, organization_id=user.organization_id, limit=limit, offset=offset)


@router.put(
    "/security/incidents/{incident_id}",
    response_model=SecurityIncident,
    summary="Avançar workflow do incidente (admin)",
)
def update_incident(
    incident_id: str,
    body: IncidentUpdate,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> SecurityIncident:
    _require_admin(user)
    incident = _incident_svc.update(
        conn,
        incident_id=incident_id,
        organization_id=user.organization_id,
        update=body,
        closed_by=user.user_id if body.status == IncidentStatus.CLOSED else None,
    )
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente não encontrado.")
    return incident


@router.get(
    "/security/incidents/{incident_id}/notification",
    summary="Gerar rascunho de notificação ANPD (Res. 15/2024)",
)
def get_anpd_notification(
    incident_id: str,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> dict[str, str]:
    _require_admin(user)
    incident = _incident_svc.get(conn, incident_id=incident_id, organization_id=user.organization_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidente não encontrado.")
    notification_text = _incident_svc.generate_anpd_notification_text(incident)
    return {
        "incident_id": incident_id,
        "anpd_notification_draft": notification_text,
        "is_overdue": str(incident.is_overdue_anpd),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Access Log Purge (Marco Civil — admin only)
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/privacy/purge-logs",
    response_model=PurgeStats,
    summary="Executar purga de logs expirados (Marco Civil arts. 13-15)",
)
def purge_logs(
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    user: Annotated[UserRecord, Depends(get_current_user_record)],
) -> PurgeStats:
    _require_admin(user)
    return _access_log_svc.purge_expired(conn)
