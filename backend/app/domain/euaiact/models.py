"""EU AI Act + eIDAS 2.0 + ISO 27001 domain models — Fase 17.

Risk categories per EU AI Act Art. 6–7 + Annex III.
QES levels per eIDAS 2.0 Regulation (EU) 2024/1183.
ISMS risk scoring per ISO 27001:2022 + ISO 27005.
"""

from __future__ import annotations

from enum import Enum


# ── EU AI Act ─────────────────────────────────────────────────────────────────


class EUAIRiskCategory(str, Enum):
    """EU AI Act risk classification tiers."""

    UNACCEPTABLE = "unacceptable"   # Art. 5: prohibited (social scoring, real-time biometrics)
    HIGH = "high"                   # Art. 6 + Annex III: conformity assessment required
    LIMITED = "limited"             # Art. 50: transparency obligations (chatbots, deepfakes)
    MINIMAL = "minimal"             # No specific obligations


class AnnexIIICategory(str, Enum):
    """EU AI Act Annex III high-risk application areas."""

    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    ESSENTIAL_SERVICES = "essential_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION_ASYLUM = "migration_asylum"
    ADMINISTRATION_JUSTICE = "administration_justice"  # Most relevant for legal AI
    DEMOCRATIC_PROCESSES = "democratic_processes"


class TechDocStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


# ── GDPR / LGPD DPIA ─────────────────────────────────────────────────────────


class DPIAStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


class DPIALegalBasis(str, Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTEREST = "legitimate_interest"


# ── eIDAS 2.0 ─────────────────────────────────────────────────────────────────


class QESLevel(str, Enum):
    """Electronic signature security levels per eIDAS."""

    QES = "QES"   # Qualified Electronic Signature — highest level
    AES = "AES"   # Advanced Electronic Signature
    SES = "SES"   # Simple Electronic Signature


class QESFormat(str, Enum):
    """Qualified signature formats (ETSI EN 319 series)."""

    PADES_LTA = "PAdES-LTA"   # PDF — long-term archive
    CADES_LTA = "CAdES-LTA"   # CMS — long-term archive
    XADES_LTA = "XAdES-LTA"   # XML — long-term archive


class QESStatus(str, Enum):
    VALID = "valid"
    REVOKED = "revoked"
    EXPIRED = "expired"


# ── ISO 27001 ISMS ─────────────────────────────────────────────────────────────


class ISMSRiskLevel(str, Enum):
    LOW = "low"        # score 1-4
    MEDIUM = "medium"  # score 5-9
    HIGH = "high"      # score 10-14
    CRITICAL = "critical"  # score 15-25


class ISMSTreatment(str, Enum):
    MITIGATE = "mitigate"
    ACCEPT = "accept"
    TRANSFER = "transfer"
    AVOID = "avoid"


class ISMSRiskStatus(str, Enum):
    OPEN = "open"
    TREATED = "treated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


def isms_risk_level(score: int) -> ISMSRiskLevel:
    """Derive ISO 27005 risk level from likelihood × impact score (1–25)."""
    if score <= 4:
        return ISMSRiskLevel.LOW
    if score <= 9:
        return ISMSRiskLevel.MEDIUM
    if score <= 14:
        return ISMSRiskLevel.HIGH
    return ISMSRiskLevel.CRITICAL
