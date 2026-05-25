"""Domain services for the privacy bounded context (LGPD Fase 14)."""

from __future__ import annotations

import hashlib
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.domain.privacy.models import (
    AccessLogCreate,
    ConsentBundle,
    ConsentRecord,
    ConsentUpdate,
    DPOContact,
    DPORequest,
    DPORequestCreate,
    DPORequestUpdate,
    IncidentCreate,
    IncidentUpdate,
    LogType,
    PurgeStats,
    RIPDCreate,
    RIPDReport,
    SecurityIncident,
)
from app.domain.privacy.repository import (
    AccessLogRepository,
    ConsentRepository,
    DPORepository,
    IncidentRepository,
    RIPDRepository,
)

logger = logging.getLogger("heillon.privacy")

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False
    logger.warning("reportlab not available — RIPD PDFs will be plain text")


# ─── RIPD Service ──────────────────────────────────────────────────────────────


class RIPDService:
    """Generates RIPD reports (LGPD art. 38) and their PDF/A representations."""

    def __init__(self, repository: RIPDRepository | None = None) -> None:
        self._repo = repository or RIPDRepository()

    def create(
        self,
        conn: Any,
        *,
        organization_id: str,
        created_by: str,
        payload: RIPDCreate,
        dpo_name: str,
        dpo_email: str,
    ) -> RIPDReport:
        ripd_id = f"ripd_{uuid.uuid4().hex}"
        report = self._repo.create(
            conn,
            ripd_id=ripd_id,
            organization_id=organization_id,
            created_by=created_by,
            payload=payload,
            dpo_name=dpo_name,
            dpo_email=dpo_email,
        )
        logger.info("RIPD created: %s org=%s type=%s", ripd_id, organization_id, payload.processing_type)
        return report

    def get(self, conn: Any, *, ripd_id: str, organization_id: str) -> RIPDReport | None:
        return self._repo.get(conn, ripd_id=ripd_id, organization_id=organization_id)

    def list_by_org(
        self, conn: Any, *, organization_id: str, limit: int = 50, offset: int = 0
    ) -> list[RIPDReport]:
        return self._repo.list_by_org(conn, organization_id=organization_id, limit=limit, offset=offset)

    def generate_pdf(self, report: RIPDReport) -> bytes:
        """Render RIPD as PDF (reportlab) or plain-text fallback."""
        if _REPORTLAB:
            return self._render_reportlab(report)
        return self._render_plaintext(report)

    def generate_pdf_and_persist(self, conn: Any, *, report: RIPDReport, output_dir: str) -> tuple[str, str]:
        """Generate PDF bytes, write to disk, update DB, return (path, checksum)."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        pdf_bytes = self.generate_pdf(report)
        checksum = hashlib.sha256(pdf_bytes).hexdigest()
        path = f"{output_dir}/{report.ripd_id}.pdf"
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        self._repo.update_pdf(
            conn,
            ripd_id=report.ripd_id,
            organization_id=report.organization_id,
            pdf_path=path,
            pdf_checksum=checksum,
        )
        return path, checksum

    # ── private ──────────────────────────────────────────────────────────────

    def _render_reportlab(self, report: RIPDReport) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        def _h1(text: str) -> Paragraph:
            return Paragraph(f"<b>{text}</b>", styles["Heading1"])

        def _h2(text: str) -> Paragraph:
            return Paragraph(f"<b>{text}</b>", styles["Heading2"])

        def _p(text: str) -> Paragraph:
            return Paragraph(text, styles["Normal"])

        def _sp() -> Spacer:
            return Spacer(1, 0.3*cm)

        # Header
        story.append(_h1("RELATÓRIO DE IMPACTO À PROTEÇÃO DE DADOS PESSOAIS"))
        story.append(_p(f"RIPD — {report.title}"))
        story.append(_p(f"ID: {report.ripd_id}"))
        story.append(_p(f"Elaborado em: {report.created_at.strftime('%d/%m/%Y %H:%M UTC')}"))
        story.append(_p(f"Encarregado (DPO): {report.dpo_name} &lt;{report.dpo_email}&gt;"))
        story.append(_sp())

        # Table
        data = [
            ["Campo", "Valor"],
            ["Tipo de Tratamento", report.processing_type],
            ["Base Legal (LGPD art. 7)", report.legal_basis.value],
            ["Finalidade", report.purpose],
            ["Ciclo de Vida dos Dados", report.data_lifecycle],
        ]
        table = Table(data, colWidths=[5*cm, 11*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
        story.append(_sp())

        def _list_section(heading: str, items: list[str]) -> None:
            story.append(_h2(heading))
            if items:
                for item in items:
                    story.append(_p(f"• {item}"))
            else:
                story.append(_p("(não especificado)"))
            story.append(_sp())

        _list_section("Categorias de Dados Pessoais", report.data_categories)
        _list_section("Destinatários", report.recipients)
        _list_section("Riscos Identificados", report.risks_identified)
        _list_section("Salvaguardas e Controles", report.safeguards)

        story.append(_h2("Base Legal — LGPD art. 7"))
        story.append(_p(
            "Este tratamento de dados pessoais está amparado pela base legal indicada acima, "
            "nos termos da Lei 13.709/2018 (LGPD)."
        ))
        story.append(_sp())
        story.append(_p(
            "Documento gerado automaticamente pela plataforma Heillon Legal. "
            "Este RIPD deve ser revisado e aprovado pelo Encarregado de Dados (DPO) "
            "antes de ser considerado definitivo."
        ))

        doc.build(story)
        return buf.getvalue()

    def _render_plaintext(self, report: RIPDReport) -> bytes:
        lines = [
            "RELATÓRIO DE IMPACTO À PROTEÇÃO DE DADOS PESSOAIS (RIPD)",
            f"ID: {report.ripd_id}",
            f"Título: {report.title}",
            f"Elaborado em: {report.created_at.isoformat()}",
            f"DPO: {report.dpo_name} <{report.dpo_email}>",
            "",
            f"Tipo de Tratamento: {report.processing_type}",
            f"Base Legal: {report.legal_basis.value}",
            f"Finalidade: {report.purpose}",
            f"Ciclo de Vida: {report.data_lifecycle}",
            "",
            "Categorias de Dados:",
            *[f"  - {c}" for c in report.data_categories],
            "",
            "Destinatários:",
            *[f"  - {r}" for r in report.recipients],
            "",
            "Riscos Identificados:",
            *[f"  - {r}" for r in report.risks_identified],
            "",
            "Salvaguardas:",
            *[f"  - {s}" for s in report.safeguards],
        ]
        return "\n".join(lines).encode("utf-8")


# ─── DPO Service ──────────────────────────────────────────────────────────────


class DPOService:
    """Manages data subject rights requests (LGPD art. 18-19, 15-day SLA)."""

    def __init__(
        self,
        *,
        dpo_name: str = "Encarregado de Dados",
        dpo_email: str = "dpo@heillon.com",
        organization_name: str = "Heillon Legal",
        public_base_url: str = "https://heillon-legal-ui.vercel.app",
        repository: DPORepository | None = None,
    ) -> None:
        self.dpo_name = dpo_name
        self.dpo_email = dpo_email
        self.organization_name = organization_name
        self.public_base_url = public_base_url
        self._repo = repository or DPORepository()

    @property
    def contact(self) -> DPOContact:
        return DPOContact(
            dpo_name=self.dpo_name,
            dpo_email=self.dpo_email,
            organization_name=self.organization_name,
            privacy_policy_url=f"{self.public_base_url}/privacy",
            request_form_url=f"{self.public_base_url}/privacy/request",
        )

    def submit_request(
        self,
        conn: Any,
        *,
        organization_id: str,
        payload: DPORequestCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> DPORequest:
        request_id = f"dpo_{uuid.uuid4().hex}"
        req = self._repo.create(
            conn,
            request_id=request_id,
            organization_id=organization_id,
            payload=payload,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info(
            "DPO request created: %s type=%s email=%s",
            request_id,
            payload.request_type.value,
            payload.requester_email,
        )
        return req

    def get_request(self, conn: Any, *, request_id: str, organization_id: str) -> DPORequest | None:
        return self._repo.get(conn, request_id=request_id, organization_id=organization_id)

    def list_requests(
        self,
        conn: Any,
        *,
        organization_id: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DPORequest]:
        return self._repo.list_by_org(
            conn, organization_id=organization_id, status=status, limit=limit, offset=offset
        )

    def update_request(
        self,
        conn: Any,
        *,
        request_id: str,
        organization_id: str,
        update: DPORequestUpdate,
    ) -> DPORequest | None:
        req = self._repo.update(
            conn, request_id=request_id, organization_id=organization_id, update=update
        )
        if req:
            logger.info("DPO request updated: %s status=%s", request_id, req.status.value)
        return req


# ─── Incident Service ─────────────────────────────────────────────────────────


class IncidentService:
    """Manages ANPD security incident workflow (Res. 15/2024 — ≤72h notification)."""

    def __init__(self, repository: IncidentRepository | None = None) -> None:
        self._repo = repository or IncidentRepository()

    def register(
        self,
        conn: Any,
        *,
        organization_id: str,
        detected_by: str,
        payload: IncidentCreate,
    ) -> SecurityIncident:
        incident_id = f"inc_{uuid.uuid4().hex}"
        incident = self._repo.create(
            conn,
            incident_id=incident_id,
            organization_id=organization_id,
            detected_by=detected_by,
            payload=payload,
        )
        logger.warning(
            "Security incident registered: %s severity=%s category=%s org=%s",
            incident_id,
            payload.severity.value,
            payload.category.value,
            organization_id,
        )
        return incident

    def get(self, conn: Any, *, incident_id: str, organization_id: str) -> SecurityIncident | None:
        return self._repo.get(conn, incident_id=incident_id, organization_id=organization_id)

    def list_by_org(
        self, conn: Any, *, organization_id: str, limit: int = 50, offset: int = 0
    ) -> list[SecurityIncident]:
        return self._repo.list_by_org(conn, organization_id=organization_id, limit=limit, offset=offset)

    def update(
        self,
        conn: Any,
        *,
        incident_id: str,
        organization_id: str,
        update: IncidentUpdate,
        closed_by: str | None = None,
    ) -> SecurityIncident | None:
        incident = self._repo.update(
            conn,
            incident_id=incident_id,
            organization_id=organization_id,
            update=update,
            closed_by=closed_by,
        )
        if incident:
            logger.info("Incident updated: %s status=%s", incident_id, incident.status.value)
        return incident

    def generate_anpd_notification_text(self, incident: SecurityIncident) -> str:
        """Generate ANPD notification draft (Res. 15/2024 art. 6-12)."""
        lines = [
            "NOTIFICAÇÃO DE INCIDENTE DE SEGURANÇA — ANPD",
            f"Protocolo interno: {incident.incident_id}",
            f"Data/hora de detecção: {incident.detected_at.strftime('%d/%m/%Y %H:%M UTC')}",
            f"Prazo de notificação ANPD: {incident.anpd_notification_due_at.strftime('%d/%m/%Y %H:%M UTC') if incident.anpd_notification_due_at else 'N/A'}",
            "",
            "1. DESCRIÇÃO DO INCIDENTE",
            f"   Categoria: {incident.category.value}",
            f"   Gravidade: {incident.severity.value}",
            f"   Descrição: {incident.description}",
            "",
            "2. DADOS AFETADOS",
            f"   Titulares afetados (estimativa): {incident.affected_subjects_count}",
            f"   Tipos de dados: {', '.join(incident.affected_data_types) or 'Em avaliação'}",
            f"   Dano potencial: {incident.potential_harm or 'Em avaliação'}",
            "",
            "3. MEDIDAS DE CONTENÇÃO",
            f"   {incident.containment_measures or 'Em implementação'}",
            "",
            "4. PLANO DE REMEDIAÇÃO",
            f"   {incident.remediation_plan or 'Em elaboração'}",
            "",
            "Gerado automaticamente pela plataforma Heillon Legal.",
            "Este documento deve ser revisado antes do envio à ANPD.",
        ]
        return "\n".join(lines)


# ─── Consent Service ──────────────────────────────────────────────────────────


class ConsentService:
    """Manages granular consent records (LGPD art. 8)."""

    def __init__(self, repository: ConsentRepository | None = None) -> None:
        self._repo = repository or ConsentRepository()

    def get_bundle(self, conn: Any, *, user_id: str, organization_id: str) -> ConsentBundle:
        return self._repo.get_bundle(conn, user_id=user_id, organization_id=organization_id)

    def set_consent(
        self,
        conn: Any,
        *,
        user_id: str,
        organization_id: str,
        update: ConsentUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ConsentRecord:
        consent_id = f"cns_{uuid.uuid4().hex}"
        record = self._repo.set_consent(
            conn,
            consent_id=consent_id,
            user_id=user_id,
            organization_id=organization_id,
            update=update,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        action = "granted" if update.granted else "revoked"
        logger.info("Consent %s: user=%s purpose=%s", action, user_id, update.purpose.value)
        return record

    def revoke_all(
        self, conn: Any, *, user_id: str, organization_id: str
    ) -> list[ConsentRecord]:
        """Revoke all consent-based purposes for the user (LGPD art. 8 §5)."""
        from app.domain.privacy.models import ConsentPurpose, LegalBasis

        bundle = self.get_bundle(conn, user_id=user_id, organization_id=organization_id)
        revoked = []
        for record in bundle.records:
            # only revoke consent-based purposes; contract/legal obligation cannot be revoked
            if record.legal_basis == LegalBasis.CONSENT and record.granted:
                r = self.set_consent(
                    conn,
                    user_id=user_id,
                    organization_id=organization_id,
                    update=ConsentUpdate(purpose=record.purpose, granted=False),
                )
                revoked.append(r)
        logger.info("All consent revoked for user=%s count=%d", user_id, len(revoked))
        return revoked


# ─── Access Log Service ────────────────────────────────────────────────────────


class AccessLogService:
    """Writes access events and runs Marco Civil purge."""

    def __init__(self, repository: AccessLogRepository | None = None) -> None:
        self._repo = repository or AccessLogRepository()

    def log(self, conn: Any, *, payload: AccessLogCreate) -> None:
        log_id = f"log_{uuid.uuid4().hex}"
        try:
            self._repo.write(conn, log_id=log_id, payload=payload)
        except Exception as exc:
            logger.warning("Access log write failed: %s", exc)

    def purge_expired(self, conn: Any) -> PurgeStats:
        """Run weekly purge of expired access logs (Marco Civil compliance)."""
        stats = self._repo.purge_expired(conn)
        logger.info(
            "Access log purge: deleted=%d cutoff=%s",
            stats.purged_count,
            stats.purge_cutoff.isoformat(),
        )
        return stats
