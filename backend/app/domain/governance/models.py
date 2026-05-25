"""AI Governance domain models — CNJ Res. 615/2025 + OAB Rec. 001/2024.

Risk levels follow CNJ 615/2025 Art. 4 classification hierarchy.
Disclosure fields align with OAB Rec. 001/2024 Rules 1.1 (competence),
1.6 (confidentiality) and 5.3 (supervision of non-lawyer assistants).
"""

from __future__ import annotations

from enum import Enum


class AIRiskLevel(str, Enum):
    """CNJ 615/2025 Art. 4 AI system risk tiers."""

    LOW = "low"           # Minimal impact; no human gate required
    MEDIUM = "medium"     # Advisory human review recommended
    HIGH = "high"         # Mandatory human approval gate before use
    PROHIBITED = "prohibited"  # Cannot be used in judicial / legal context


class ClassificationStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


class DecisionType(str, Enum):
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    CLASSIFICATION = "classification"
    GENERATION = "generation"


class HumanDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class GateType(str, Enum):
    MANDATORY = "mandatory"   # High-risk: must have human sign-off
    ADVISORY = "advisory"     # Medium-risk: human review logged but not blocking


class GateStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DisclosureMethod(str, Enum):
    WRITTEN = "written"
    VERBAL = "verbal"
    AUTOMATED = "automated"


class DisclosureChannel(str, Enum):
    EMAIL = "email"
    PORTAL = "portal"
    DOCUMENT = "document"


# ── Risk level helpers ────────────────────────────────────────────────────────

_RISK_REQUIRES_GATE: dict[AIRiskLevel, bool] = {
    AIRiskLevel.LOW: False,
    AIRiskLevel.MEDIUM: False,
    AIRiskLevel.HIGH: True,
    AIRiskLevel.PROHIBITED: True,
}

_RISK_GATE_TYPE: dict[AIRiskLevel, GateType] = {
    AIRiskLevel.MEDIUM: GateType.ADVISORY,
    AIRiskLevel.HIGH: GateType.MANDATORY,
}

_GATE_EXPIRY_HOURS: dict[GateType, int] = {
    GateType.MANDATORY: 48,
    GateType.ADVISORY: 24,
}


def requires_human_gate(risk_level: AIRiskLevel) -> bool:
    """Return True when *risk_level* mandates a human approval gate."""
    return _RISK_REQUIRES_GATE.get(risk_level, False)


def gate_type_for_risk(risk_level: AIRiskLevel) -> GateType | None:
    """Return the appropriate gate type for *risk_level*, or None if no gate needed."""
    return _RISK_GATE_TYPE.get(risk_level)


def gate_expiry_hours(gate_type: GateType) -> int:
    """Return gate expiry window in hours."""
    return _GATE_EXPIRY_HOURS.get(gate_type, 48)
