"""EU AI Act + eIDAS 2.0 + ISO 27001 services — Fase 17."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.euaiact.models import (
    EUAIRiskCategory,
    ISMSRiskLevel,
    ISMSTreatment,
    QESLevel,
    isms_risk_level,
)
from app.domain.euaiact.repository import (
    DPIARepository,
    EIDASQESRepository,
    EUAITechDocRepository,
    ISMSRiskRepository,
)


# ── EU AI Act Technical Documentation Service ─────────────────────────────────


class EUAITechDocService:
    """Manage EU AI Act Annex IV technical documentation."""

    def __init__(self, repo: EUAITechDocRepository | None = None) -> None:
        self._repo = repo or EUAITechDocRepository()

    def create_doc(
        self,
        conn: Any,
        *,
        organization_id: str,
        system_name: str,
        system_version: str = "1.0",
        system_description: str = "",
        risk_category: str = "high",
        annex_iii_category: str | None = None,
        intended_purpose: str = "",
        general_description: dict | None = None,
        training_data: dict | None = None,
        testing_validation: dict | None = None,
        performance_metrics: dict | None = None,
        human_oversight: dict | None = None,
        cybersecurity: dict | None = None,
        created_by: str,
    ) -> str:
        """Create an Annex IV technical documentation record. Returns ``doc_id``."""
        _valid = {r.value for r in EUAIRiskCategory}
        if risk_category not in _valid:
            raise ValueError(f"risk_category must be one of {sorted(_valid)}")
        doc_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            doc_id=doc_id,
            organization_id=organization_id,
            system_name=system_name,
            system_version=system_version,
            system_description=system_description,
            risk_category=risk_category,
            annex_iii_category=annex_iii_category,
            intended_purpose=intended_purpose,
            general_description=general_description,
            training_data=training_data,
            testing_validation=testing_validation,
            performance_metrics=performance_metrics,
            human_oversight=human_oversight,
            cybersecurity=cybersecurity,
            created_by=created_by,
        )
        return doc_id

    def get(self, conn: Any, doc_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, doc_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, status: str | None = None
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, status=status)

    def activate(self, conn: Any, doc_id: str) -> None:
        self._repo.update_status(conn, doc_id, "active")

    def archive(self, conn: Any, doc_id: str) -> None:
        self._repo.update_status(conn, doc_id, "archived")

    def mark_conformity(
        self, conn: Any, doc_id: str, *, notified_body: str | None = None
    ) -> None:
        self._repo.mark_conformity(conn, doc_id, notified_body=notified_body)

    def generate_summary_text(self, doc: dict[str, Any]) -> str:
        """Generate a plain-text EU AI Act conformity summary for the document."""
        name = doc.get("system_name", "—")
        version = doc.get("system_version", "—")
        cat = doc.get("risk_category", "—")
        annex = doc.get("annex_iii_category") or "—"
        assessed = bool(doc.get("conformity_assessed"))
        body = doc.get("notified_body") or "—"
        return (
            f"EU AI Act — Technical Documentation Summary\n"
            f"============================================\n"
            f"System: {name} v{version}\n"
            f"Risk Category: {cat.upper()}\n"
            f"Annex III Area: {annex}\n"
            f"Conformity Assessed: {'YES' if assessed else 'NO'}\n"
            f"Notified Body: {body}\n"
            f"Status: {doc.get('status', '—')}\n"
            f"\nReg. (EU) 2024/1689 — Art. 11 + Annex IV Technical Documentation\n"
        )


# ── DPIA Service ──────────────────────────────────────────────────────────────


class DPIAService:
    """Manage GDPR Art. 35 / LGPD Art. 38 Data Protection Impact Assessments."""

    def __init__(self, repo: DPIARepository | None = None) -> None:
        self._repo = repo or DPIARepository()

    def create_dpia(
        self,
        conn: Any,
        *,
        organization_id: str,
        processing_name: str,
        processing_purpose: str = "",
        legal_basis: str = "legitimate_interest",
        data_categories: list[str] | None = None,
        data_subjects: list[str] | None = None,
        necessity_assessment: str = "",
        proportionality_check: str = "",
        risks_identified: list[dict] | None = None,
        mitigations: list[dict] | None = None,
        created_by: str,
    ) -> str:
        dpia_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            dpia_id=dpia_id,
            organization_id=organization_id,
            processing_name=processing_name,
            processing_purpose=processing_purpose,
            legal_basis=legal_basis,
            data_categories=data_categories,
            data_subjects=data_subjects,
            necessity_assessment=necessity_assessment,
            proportionality_check=proportionality_check,
            risks_identified=risks_identified,
            mitigations=mitigations,
            created_by=created_by,
        )
        return dpia_id

    def get(self, conn: Any, dpia_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, dpia_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)

    def approve(self, conn: Any, dpia_id: str, *, approved_by: str) -> None:
        self._repo.approve(conn, dpia_id, approved_by=approved_by)


# ── eIDAS QES Service ─────────────────────────────────────────────────────────


class EIDASQESService:
    """Track eIDAS 2.0 Qualified Electronic Signatures."""

    def __init__(self, repo: EIDASQESRepository | None = None) -> None:
        self._repo = repo or EIDASQESRepository()

    def record_qes(
        self,
        conn: Any,
        *,
        organization_id: str,
        document_type: str,
        document_ref: str,
        document_hash: str,
        signatory_name: str,
        signatory_email: str,
        qtsp_provider: str = "",
        qtsp_country: str = "EU",
        signature_format: str = "PAdES-LTA",
        signature_level: str = "QES",
        eudi_wallet_used: bool = False,
        eudi_pid_verified: bool = False,
        signature_timestamp: str | None = None,
        tsa_provider: str | None = None,
    ) -> str:
        """Record a QES signature. Returns ``qes_id``."""
        qes_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            qes_id=qes_id,
            organization_id=organization_id,
            document_type=document_type,
            document_ref=document_ref,
            document_hash=document_hash,
            signatory_name=signatory_name,
            signatory_email=signatory_email,
            qtsp_provider=qtsp_provider,
            qtsp_country=qtsp_country,
            signature_format=signature_format,
            signature_level=signature_level,
            eudi_wallet_used=eudi_wallet_used,
            eudi_pid_verified=eudi_pid_verified,
            signature_timestamp=signature_timestamp,
            tsa_provider=tsa_provider,
        )
        return qes_id

    def get(self, conn: Any, qes_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, qes_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)


# ── ISMS Risk Service ─────────────────────────────────────────────────────────


class ISMSRiskService:
    """Manage ISO 27001:2022 information security risk register."""

    def __init__(self, repo: ISMSRiskRepository | None = None) -> None:
        self._repo = repo or ISMSRiskRepository()

    def register_risk(
        self,
        conn: Any,
        *,
        organization_id: str,
        asset: str,
        threat: str,
        vulnerability: str = "",
        likelihood: int,
        impact: int,
        control_ref: str | None = None,
        control_description: str = "",
        treatment_option: str = "mitigate",
        residual_risk: str | None = None,
        risk_owner: str,
    ) -> dict[str, Any]:
        """Register a new risk. Returns dict with ``risk_id`` and ``risk_level``."""
        if not (1 <= likelihood <= 5) or not (1 <= impact <= 5):
            raise ValueError("likelihood and impact must be integers 1–5.")
        risk_id = str(uuid.uuid4())
        score = likelihood * impact
        level = isms_risk_level(score).value
        self._repo.create(
            conn,
            risk_id=risk_id,
            organization_id=organization_id,
            asset=asset,
            threat=threat,
            vulnerability=vulnerability,
            likelihood=likelihood,
            impact=impact,
            control_ref=control_ref,
            control_description=control_description,
            treatment_option=treatment_option,
            residual_risk=residual_risk,
            risk_owner=risk_owner,
        )
        return {"risk_id": risk_id, "risk_level": level, "risk_score": score}

    def get(self, conn: Any, risk_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, risk_id)

    def list_by_org(
        self,
        conn: Any,
        organization_id: str,
        *,
        risk_level: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(
            conn, organization_id, risk_level=risk_level, status=status, skip=skip, limit=limit
        )

    def close_risk(self, conn: Any, risk_id: str) -> None:
        self._repo.update_status(conn, risk_id, "closed")

    def accept_risk(self, conn: Any, risk_id: str) -> None:
        self._repo.update_status(conn, risk_id, "accepted")
