"""EU AI Act + eIDAS 2.0 + ISO 27001 repository layer."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.euaiact.models import isms_risk_level


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── EU AI Act Technical Documentation ─────────────────────────────────────────


class EUAITechDocRepository:
    """CRUD for ``euai_technical_docs`` (Annex IV technical documentation)."""

    def create(
        self,
        conn: Any,
        *,
        doc_id: str,
        organization_id: str = "org_default",
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
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO euai_technical_docs (
                doc_id, organization_id, system_name, system_version,
                system_description, risk_category, annex_iii_category,
                intended_purpose,
                general_description, training_data, testing_validation,
                performance_metrics, human_oversight, cybersecurity,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                doc_id,
                organization_id,
                system_name,
                system_version,
                system_description,
                risk_category,
                annex_iii_category,
                intended_purpose,
                json.dumps(general_description or {}),
                json.dumps(training_data or {}),
                json.dumps(testing_validation or {}),
                json.dumps(performance_metrics or {}),
                json.dumps(human_oversight or {}),
                json.dumps(cybersecurity or {}),
                "draft",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, doc_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM euai_technical_docs WHERE doc_id=?", (doc_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self,
        conn: Any,
        organization_id: str,
        *,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if status:
            rows = conn.execute(
                """SELECT * FROM euai_technical_docs
                   WHERE organization_id=? AND status=?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (organization_id, status, limit, skip),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM euai_technical_docs
                   WHERE organization_id=?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (organization_id, limit, skip),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, conn: Any, doc_id: str, status: str) -> None:
        now = _now()
        conn.execute(
            "UPDATE euai_technical_docs SET status=?, updated_at=? WHERE doc_id=?",
            (status, now, doc_id),
        )

    def mark_conformity(
        self, conn: Any, doc_id: str, *, notified_body: str | None = None
    ) -> None:
        now = _now()
        conn.execute(
            """UPDATE euai_technical_docs
               SET conformity_assessed=1, conformity_date=?, notified_body=?, updated_at=?
               WHERE doc_id=?""",
            (now, notified_body, now, doc_id),
        )


# ── DPIA Records ──────────────────────────────────────────────────────────────


class DPIARepository:
    """CRUD for ``dpia_records``."""

    def create(
        self,
        conn: Any,
        *,
        dpia_id: str,
        organization_id: str = "org_default",
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
    ) -> None:
        now = _now()
        # Annual review
        review_due = (datetime.now(UTC) + timedelta(days=365)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        conn.execute(
            """INSERT INTO dpia_records (
                dpia_id, organization_id, processing_name, processing_purpose,
                legal_basis, data_categories, data_subjects,
                necessity_assessment, proportionality_check,
                risks_identified, mitigations,
                status, review_due_at, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                dpia_id,
                organization_id,
                processing_name,
                processing_purpose,
                legal_basis,
                json.dumps(data_categories or []),
                json.dumps(data_subjects or []),
                necessity_assessment,
                proportionality_check,
                json.dumps(risks_identified or []),
                json.dumps(mitigations or []),
                "draft",
                review_due,
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, dpia_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM dpia_records WHERE dpia_id=?", (dpia_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM dpia_records
               WHERE organization_id=?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def approve(self, conn: Any, dpia_id: str, *, approved_by: str) -> None:
        now = _now()
        conn.execute(
            """UPDATE dpia_records
               SET status='approved', approved_by=?, approved_at=?, updated_at=?
               WHERE dpia_id=?""",
            (approved_by, now, now, dpia_id),
        )


# ── eIDAS QES Records ─────────────────────────────────────────────────────────


class EIDASQESRepository:
    """CRUD for ``eidas_qes_records``."""

    def create(
        self,
        conn: Any,
        *,
        qes_id: str,
        organization_id: str = "org_default",
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
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO eidas_qes_records (
                qes_id, organization_id, document_type, document_ref, document_hash,
                signatory_name, signatory_email, qtsp_provider, qtsp_country,
                signature_format, signature_level,
                eudi_wallet_used, eudi_pid_verified,
                signature_timestamp, tsa_provider, status, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                qes_id,
                organization_id,
                document_type,
                document_ref,
                document_hash,
                signatory_name,
                signatory_email,
                qtsp_provider,
                qtsp_country,
                signature_format,
                signature_level,
                int(eudi_wallet_used),
                int(eudi_pid_verified),
                signature_timestamp or now,
                tsa_provider,
                "valid",
                now,
            ),
        )

    def get(self, conn: Any, qes_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM eidas_qes_records WHERE qes_id=?", (qes_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM eidas_qes_records
               WHERE organization_id=?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


# ── ISMS Risk Register ────────────────────────────────────────────────────────


class ISMSRiskRepository:
    """CRUD for ``isms_risks`` (ISO 27001:2022 risk register)."""

    def create(
        self,
        conn: Any,
        *,
        risk_id: str,
        organization_id: str = "org_default",
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
    ) -> None:
        now = _now()
        score = likelihood * impact
        level = isms_risk_level(score).value
        review_due = (datetime.now(UTC) + timedelta(days=365)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        conn.execute(
            """INSERT INTO isms_risks (
                risk_id, organization_id, asset, threat, vulnerability,
                likelihood, impact, risk_level,
                control_ref, control_description, treatment_option, residual_risk,
                risk_owner, review_due_at, status,
                identified_at, updated_at, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                risk_id,
                organization_id,
                asset,
                threat,
                vulnerability,
                likelihood,
                impact,
                level,
                control_ref,
                control_description,
                treatment_option,
                residual_risk,
                risk_owner,
                review_due,
                "open",
                now,
                now,
                now,
            ),
        )

    def get(self, conn: Any, risk_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM isms_risks WHERE risk_id=?", (risk_id,)
        ).fetchone()
        return dict(row) if row else None

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
        conditions = ["organization_id=?"]
        params: list[Any] = [organization_id]
        if risk_level:
            conditions.append("risk_level=?")
            params.append(risk_level)
        if status:
            conditions.append("status=?")
            params.append(status)
        where = " AND ".join(conditions)
        params.extend([limit, skip])
        rows = conn.execute(
            f"SELECT * FROM isms_risks WHERE {where} ORDER BY risk_score DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, conn: Any, risk_id: str, status: str) -> None:
        now = _now()
        conn.execute(
            "UPDATE isms_risks SET status=?, updated_at=? WHERE risk_id=?",
            (status, now, risk_id),
        )
