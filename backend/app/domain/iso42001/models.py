"""ISO 42001 AIMS + FRIA models — Fase 20."""

from __future__ import annotations

from enum import Enum


class CertificationStatus(str, Enum):
    NOT_STARTED = "not_started"
    GAP_ANALYSIS = "gap_analysis"
    STAGE1_AUDIT = "stage1_audit"
    STAGE2_AUDIT = "stage2_audit"
    CERTIFIED = "certified"
    SURVEILLANCE = "surveillance"


class ControlStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    NOT_APPLICABLE = "not_applicable"


class ImpactSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ImpactLikelihood(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CERTAIN = "certain"


class ResidualRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"


class FRIAStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


# ISO 42001 Annex A controls reference
ANNEX_A_CONTROLS: dict[str, str] = {
    "A.2": "Policies for AI system development",
    "A.3": "Internal audit function for AI",
    "A.4": "AI system impact assessment",
    "A.5": "AI system life cycle management",
    "A.6": "Data management practices",
    "A.7": "Data for AI system training and testing",
    "A.8": "AI system information and documentation",
    "A.9": "Logging and monitoring of AI systems",
}

# EU Charter of Fundamental Rights — rights relevant to AI
EU_CHARTER_RIGHTS: dict[str, str] = {
    "right_dignity": "Art. 1 — Human dignity",
    "right_privacy": "Art. 7-8 — Respect for private life and data protection",
    "right_nondiscrimination": "Art. 21 — Non-discrimination",
    "right_fair_trial": "Art. 47 — Right to an effective remedy and to a fair trial",
    "right_presumption": "Art. 48 — Presumption of innocence and right of defence",
    "right_labour": "Art. 31 — Fair and just working conditions",
    "right_education": "Art. 14 — Right to education",
    "right_property": "Art. 17 — Right to property",
}
