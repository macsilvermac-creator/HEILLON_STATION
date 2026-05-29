"""Governance domain repository — CRUD for CNJ/OAB governance tables."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.governance.models import (
    AIRiskLevel,
    GateStatus,
    GateType,
    gate_expiry_hours,
)


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── AI Risk Classification ─────────────────────────────────────────────────────


class AIRiskRepository:
    """CRUD for ``ai_risk_classifications``."""

    def create(
        self,
        conn: Any,
        *,
        classification_id: str,
        organization_id: str = "org_default",
        system_name: str,
        system_version: str = "1.0",
        system_description: str = "",
        risk_level: str,
        risk_justification: str = "",
        impact_areas: str = "",
        regulatory_refs: list[str] | None = None,
        classified_by: str,
    ) -> None:
        now = _now()
        # Review due in 1 year per CNJ 615/2025 lifecycle requirements
        review_due = (datetime.now(UTC) + timedelta(days=365)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        conn.execute(
            """INSERT INTO ai_risk_classifications (
                classification_id, organization_id,
                system_name, system_version, system_description,
                risk_level, risk_justification, impact_areas, regulatory_refs,
                classified_by, classified_at, review_due_at, status, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                classification_id,
                organization_id,
                system_name,
                system_version,
                system_description,
                risk_level,
                risk_justification,
                impact_areas,
                json.dumps(regulatory_refs or []),
                classified_by,
                now,
                review_due,
                "active",
                now,
            ),
        )

    def get(self, conn: Any, classification_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM ai_risk_classifications WHERE classification_id=?",
            (classification_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self,
        conn: Any,
        organization_id: str,
        *,
        status: str | None = "active",
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if status:
            rows = conn.execute(
                """SELECT * FROM ai_risk_classifications
                   WHERE organization_id=? AND status=?
                   ORDER BY classified_at DESC LIMIT ? OFFSET ?""",
                (organization_id, status, limit, skip),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM ai_risk_classifications
                   WHERE organization_id=?
                   ORDER BY classified_at DESC LIMIT ? OFFSET ?""",
                (organization_id, limit, skip),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, conn: Any, classification_id: str, status: str) -> None:
        conn.execute(
            "UPDATE ai_risk_classifications SET status=? WHERE classification_id=?",
            (status, classification_id),
        )


# ── AI Decision Log ────────────────────────────────────────────────────────────


class AIDecisionLogRepository:
    """Append-only audit log for AI-assisted decisions."""

    def create(
        self,
        conn: Any,
        *,
        decision_id: str,
        organization_id: str = "org_default",
        hdr_id: str | None = None,
        mission_id: str | None = None,
        classification_id: str | None = None,
        decision_type: str,
        decision_summary: str = "",
        ai_model: str = "",
        ai_provider: str = "",
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO ai_decision_logs (
                decision_id, organization_id, hdr_id, mission_id, classification_id,
                decision_type, decision_summary, ai_model, ai_provider,
                human_reviewed, decided_at, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                decision_id,
                organization_id,
                hdr_id,
                mission_id,
                classification_id,
                decision_type,
                decision_summary,
                ai_model,
                ai_provider,
                0,
                now,
                now,
            ),
        )

    def get(self, conn: Any, decision_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM ai_decision_logs WHERE decision_id=?",
            (decision_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self,
        conn: Any,
        organization_id: str,
        *,
        human_reviewed: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if human_reviewed is not None:
            rows = conn.execute(
                """SELECT * FROM ai_decision_logs
                   WHERE organization_id=? AND human_reviewed=?
                   ORDER BY decided_at DESC LIMIT ? OFFSET ?""",
                (organization_id, int(human_reviewed), limit, skip),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM ai_decision_logs
                   WHERE organization_id=?
                   ORDER BY decided_at DESC LIMIT ? OFFSET ?""",
                (organization_id, limit, skip),
            ).fetchall()
        return [dict(r) for r in rows]

    def record_human_review(
        self,
        conn: Any,
        decision_id: str,
        *,
        reviewer_id: str,
        human_decision: str,
        notes: str = "",
    ) -> None:
        now = _now()
        conn.execute(
            """UPDATE ai_decision_logs
               SET human_reviewed=1, human_reviewer_id=?, human_decision=?,
                   human_notes=?, reviewed_at=?
               WHERE decision_id=?""",
            (reviewer_id, human_decision, notes, now, decision_id),
        )

    def record_disclosure(
        self,
        conn: Any,
        decision_id: str,
        *,
        method: str = "written",
    ) -> None:
        now = _now()
        conn.execute(
            """UPDATE ai_decision_logs
               SET disclosed_to_client=1, disclosure_method=?, disclosed_at=?
               WHERE decision_id=?""",
            (method, now, decision_id),
        )


# ── Human Approval Gate ────────────────────────────────────────────────────────


class HumanApprovalGateRepository:
    """CRUD for ``human_approval_gates``."""

    def create(
        self,
        conn: Any,
        *,
        gate_id: str,
        organization_id: str = "org_default",
        decision_id: str,
        gate_type: str = GateType.MANDATORY,
        risk_level: str = AIRiskLevel.HIGH,
        required_role: str = "advogado",
    ) -> None:
        now = _now()
        hours = gate_expiry_hours(GateType(gate_type))
        expires_at = (datetime.now(UTC) + timedelta(hours=hours)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        conn.execute(
            """INSERT INTO human_approval_gates (
                gate_id, organization_id, decision_id, gate_type,
                risk_level, required_role, expires_at, status, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                gate_id,
                organization_id,
                decision_id,
                gate_type,
                risk_level,
                required_role,
                expires_at,
                GateStatus.PENDING,
                now,
            ),
        )

    def get(self, conn: Any, gate_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM human_approval_gates WHERE gate_id=?",
            (gate_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_for_decision(self, conn: Any, decision_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            """SELECT * FROM human_approval_gates
               WHERE decision_id=? ORDER BY created_at DESC LIMIT 1""",
            (decision_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_pending_by_org(
        self, conn: Any, organization_id: str, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM human_approval_gates
               WHERE organization_id=? AND status=?
               ORDER BY expires_at ASC LIMIT ?""",
            (organization_id, GateStatus.PENDING, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def resolve(
        self,
        conn: Any,
        gate_id: str,
        *,
        status: str,
        resolved_by: str,
        notes: str = "",
    ) -> None:
        now = _now()
        conn.execute(
            """UPDATE human_approval_gates
               SET status=?, resolved_by=?, resolution_notes=?, resolved_at=?
               WHERE gate_id=?""",
            (status, resolved_by, notes, now, gate_id),
        )

    def expire_overdue(self, conn: Any) -> int:
        """Mark all pending gates past their expiry as ``expired``. Returns count."""
        now = _now()
        cursor = conn.execute(
            """UPDATE human_approval_gates
               SET status=?
               WHERE status=? AND expires_at < ?""",
            (GateStatus.EXPIRED, GateStatus.PENDING, now),
        )
        return int(cursor.rowcount)


# ── AI Disclosures ─────────────────────────────────────────────────────────────


class AIDisclosureRepository:
    """CRUD for ``ai_disclosures``."""

    def create(
        self,
        conn: Any,
        *,
        disclosure_id: str,
        organization_id: str = "org_default",
        lawyer_id: str,
        client_identifier: str,
        ai_systems_used: list[str] | None = None,
        mission_ids: list[str] | None = None,
        disclosure_text: str = "",
        method: str = "written",
        channel: str = "email",
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO ai_disclosures (
                disclosure_id, organization_id, lawyer_id, client_identifier,
                ai_systems_used, mission_ids, disclosure_text,
                method, channel, client_acknowledged, disclosed_at, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                disclosure_id,
                organization_id,
                lawyer_id,
                client_identifier,
                json.dumps(ai_systems_used or []),
                json.dumps(mission_ids or []),
                disclosure_text,
                method,
                channel,
                0,
                now,
                now,
            ),
        )

    def get(self, conn: Any, disclosure_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM ai_disclosures WHERE disclosure_id=?",
            (disclosure_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM ai_disclosures
               WHERE organization_id=?
               ORDER BY disclosed_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def acknowledge(self, conn: Any, disclosure_id: str) -> None:
        now = _now()
        conn.execute(
            "UPDATE ai_disclosures SET client_acknowledged=1, acknowledged_at=? WHERE disclosure_id=?",
            (now, disclosure_id),
        )
