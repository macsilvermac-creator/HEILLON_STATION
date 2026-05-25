"""Legal evidence AI models — FRE 707 + Citation + Hallucination — Fase 20."""

from __future__ import annotations

from enum import Enum


class AdmissibilityOpinion(str, Enum):
    PENDING = "pending"
    ADMISSIBLE = "admissible"
    CONDITIONAL = "conditional"
    INADMISSIBLE = "inadmissible"


class EvidenceStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ADMITTED = "admitted"
    EXCLUDED = "excluded"
    WITHDRAWN = "withdrawn"


class CitationType(str, Enum):
    CASE = "case"
    STATUTE = "statute"
    REGULATION = "regulation"
    TREATISE = "treatise"
    ARTICLE = "article"
    SECONDARY = "secondary"


class HallucinationType(str, Enum):
    FABRICATED_CITATION = "fabricated_citation"
    WRONG_HOLDING = "wrong_holding"
    WRONG_QUOTE = "wrong_quote"
    WRONG_YEAR = "wrong_year"
    REVERSED_OUTCOME = "reversed_outcome"


class HallucinationSeverity(str, Enum):
    NONE = "none"
    MINOR = "minor"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    REPORTED = "reported"


class VerificationMethod(str, Enum):
    MANUAL = "manual"
    WESTLAW = "westlaw"
    LEXISNEXIS = "lexisnexis"
    FASTCASE = "fastcase"
    GOOGLE_SCHOLAR = "google_scholar"
    CASETEXT = "casetext"


# ABA Rules most relevant to AI use — Formal Opinion 512 (Jul 2024)
ABA_AI_COMPETENCE_RULES: dict[str, str] = {
    "1.1": "Competence — duty to understand AI tools and outputs",
    "1.4": "Communication — disclose AI use to clients when material",
    "1.5": "Fees — AI-derived efficiency must benefit client, not inflate billing",
    "3.3": "Candor toward the Tribunal — verify AI-generated citations before filing",
    "5.3": "Supervision — supervise non-lawyer assistance including AI",
    "1.6": "Confidentiality — protect client data from AI training/disclosure",
}

# State bars with mandatory AI CLE requirements (as of 2026)
STATE_AI_CLE_REQUIREMENTS: dict[str, str] = {
    "CA": "California: 1 hour AI ethics CLE required (2025)",
    "FL": "Florida: AI CLE included in ethics requirement",
    "NC": "North Carolina: AI CLE guidance issued 2024",
    "SC": "South Carolina: formal AI guidance 2024",
    "NY": "New York: considering mandatory AI disclosure rules",
    "TX": "Texas: voluntary AI guidelines published",
}
