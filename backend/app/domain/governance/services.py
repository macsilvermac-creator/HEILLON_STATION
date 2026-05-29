"""Governance domain services — AI risk assessment, human gates, OAB disclosure.

Implements CNJ Res. 615/2025 and OAB Rec. 001/2024 workflows:
- Risk classification lifecycle with annual review deadline
- Mandatory human approval gates for HIGH/PROHIBITED risk decisions
- OAB disclosure tracking with client acknowledgement
- Audit log enrichment for AI-assisted decisions
"""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.governance.models import (
    AIRiskLevel,
    GateStatus,
    GateType,
    gate_type_for_risk,
    requires_human_gate,
)
from app.domain.governance.repository import (
    AIDecisionLogRepository,
    AIDisclosureRepository,
    AIRiskRepository,
    HumanApprovalGateRepository,
)


# ── Risk Classification Service ────────────────────────────────────────────────


class AIRiskService:
    """Manage AI system risk classifications (CNJ 615/2025 Art. 4)."""

    def __init__(self, repo: AIRiskRepository | None = None) -> None:
        self._repo = repo or AIRiskRepository()

    def classify(
        self,
        conn: Any,
        *,
        organization_id: str,
        system_name: str,
        system_version: str = "1.0",
        system_description: str = "",
        risk_level: str,
        risk_justification: str = "",
        impact_areas: list[str] | None = None,
        regulatory_refs: list[str] | None = None,
        classified_by: str,
    ) -> str:
        """Create a new risk classification record. Returns ``classification_id``."""
        _valid = {r.value for r in AIRiskLevel}
        if risk_level not in _valid:
            raise ValueError(
                f"risk_level must be one of {sorted(_valid)}, got {risk_level!r}"
            )

        cid = str(uuid.uuid4())
        self._repo.create(
            conn,
            classification_id=cid,
            organization_id=organization_id,
            system_name=system_name,
            system_version=system_version,
            system_description=system_description,
            risk_level=risk_level,
            risk_justification=risk_justification,
            impact_areas=",".join(impact_areas or []),
            regulatory_refs=regulatory_refs,
            classified_by=classified_by,
        )
        return cid

    def get(self, conn: Any, classification_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, classification_id)

    def list_by_org(
        self,
        conn: Any,
        organization_id: str,
        *,
        status: str | None = "active",
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(
            conn, organization_id, status=status, skip=skip, limit=limit
        )

    def retire(self, conn: Any, classification_id: str) -> None:
        self._repo.update_status(conn, classification_id, "retired")


# ── Decision Audit Service ─────────────────────────────────────────────────────


class AIDecisionService:
    """Log and audit AI-assisted decisions with human oversight tracking."""

    def __init__(
        self,
        decision_repo: AIDecisionLogRepository | None = None,
        gate_repo: HumanApprovalGateRepository | None = None,
        risk_repo: AIRiskRepository | None = None,
    ) -> None:
        self._decision_repo = decision_repo or AIDecisionLogRepository()
        self._gate_repo = gate_repo or HumanApprovalGateRepository()
        self._risk_repo = risk_repo or AIRiskRepository()

    def log_decision(
        self,
        conn: Any,
        *,
        organization_id: str,
        decision_type: str,
        decision_summary: str = "",
        ai_model: str = "",
        ai_provider: str = "",
        hdr_id: str | None = None,
        mission_id: str | None = None,
        classification_id: str | None = None,
        risk_level: str = AIRiskLevel.LOW,
    ) -> dict[str, Any]:
        """Log an AI decision. Creates a human gate for HIGH-risk decisions.

        Returns a dict with ``decision_id`` and optional ``gate_id``.
        """
        decision_id = str(uuid.uuid4())
        self._decision_repo.create(
            conn,
            decision_id=decision_id,
            organization_id=organization_id,
            hdr_id=hdr_id,
            mission_id=mission_id,
            classification_id=classification_id,
            decision_type=decision_type,
            decision_summary=decision_summary,
            ai_model=ai_model,
            ai_provider=ai_provider,
        )

        gate_id: str | None = None
        rl = AIRiskLevel(risk_level)
        if requires_human_gate(rl):
            gate_type = gate_type_for_risk(rl) or GateType.MANDATORY
            gate_id = str(uuid.uuid4())
            self._gate_repo.create(
                conn,
                gate_id=gate_id,
                organization_id=organization_id,
                decision_id=decision_id,
                gate_type=gate_type.value,
                risk_level=risk_level,
            )

        return {"decision_id": decision_id, "gate_id": gate_id}

    def get_decision(self, conn: Any, decision_id: str) -> dict[str, Any] | None:
        return self._decision_repo.get(conn, decision_id)

    def list_decisions(
        self,
        conn: Any,
        organization_id: str,
        *,
        human_reviewed: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self._decision_repo.list_by_org(
            conn, organization_id, human_reviewed=human_reviewed, skip=skip, limit=limit
        )

    def review_decision(
        self,
        conn: Any,
        decision_id: str,
        *,
        reviewer_id: str,
        human_decision: str,
        notes: str = "",
    ) -> None:
        """Record a human review verdict and resolve the associated gate if present."""
        self._decision_repo.record_human_review(
            conn,
            decision_id,
            reviewer_id=reviewer_id,
            human_decision=human_decision,
            notes=notes,
        )
        gate = self._gate_repo.get_for_decision(conn, decision_id)
        if gate and gate.get("status") == GateStatus.PENDING:
            gate_status = (
                GateStatus.APPROVED
                if human_decision == "approved"
                else GateStatus.REJECTED
            )
            self._gate_repo.resolve(
                conn,
                gate["gate_id"],
                status=gate_status.value,
                resolved_by=reviewer_id,
                notes=notes,
            )


# ── Human Gate Service ─────────────────────────────────────────────────────────


class HumanGateService:
    """Manage human approval gates for HIGH-risk AI decisions."""

    def __init__(self, repo: HumanApprovalGateRepository | None = None) -> None:
        self._repo = repo or HumanApprovalGateRepository()

    def get_gate(self, conn: Any, gate_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, gate_id)

    def list_pending(
        self, conn: Any, organization_id: str, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List all pending gates, expiring overdue ones first."""
        self._repo.expire_overdue(conn)
        return self._repo.list_pending_by_org(conn, organization_id, limit=limit)

    def resolve(
        self,
        conn: Any,
        gate_id: str,
        *,
        status: str,
        resolved_by: str,
        notes: str = "",
    ) -> None:
        """Resolve a gate: ``approved`` or ``rejected``."""
        valid = {GateStatus.APPROVED.value, GateStatus.REJECTED.value}
        if status not in valid:
            raise ValueError(
                f"Gate resolution must be one of {sorted(valid)}, got {status!r}"
            )
        self._repo.resolve(
            conn, gate_id, status=status, resolved_by=resolved_by, notes=notes
        )


# ── Disclosure Service ─────────────────────────────────────────────────────────


class AIDisclosureService:
    """Manage OAB Rec. 001/2024 AI disclosure records."""

    _DEFAULT_TEXT = (
        "This analysis was assisted by artificial intelligence tools. "
        "All AI-generated content has been reviewed by a qualified lawyer "
        "before delivery per OAB Recommendation 001/2024."
    )

    def __init__(self, repo: AIDisclosureRepository | None = None) -> None:
        self._repo = repo or AIDisclosureRepository()

    def create_disclosure(
        self,
        conn: Any,
        *,
        organization_id: str,
        lawyer_id: str,
        client_identifier: str,
        ai_systems_used: list[str] | None = None,
        mission_ids: list[str] | None = None,
        disclosure_text: str | None = None,
        method: str = "written",
        channel: str = "email",
    ) -> str:
        """Create disclosure record. Returns ``disclosure_id``."""
        did = str(uuid.uuid4())
        self._repo.create(
            conn,
            disclosure_id=did,
            organization_id=organization_id,
            lawyer_id=lawyer_id,
            client_identifier=client_identifier,
            ai_systems_used=ai_systems_used,
            mission_ids=mission_ids,
            disclosure_text=disclosure_text or self._DEFAULT_TEXT,
            method=method,
            channel=channel,
        )
        return did

    def get(self, conn: Any, disclosure_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, disclosure_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)

    def acknowledge(self, conn: Any, disclosure_id: str) -> None:
        """Mark the disclosure as acknowledged by the client."""
        self._repo.acknowledge(conn, disclosure_id)

    @property
    def default_disclosure_text(self) -> str:
        return self._DEFAULT_TEXT
