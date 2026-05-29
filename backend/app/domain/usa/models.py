"""USA regulatory compliance models — Fase 18.

Standards covered:
- Colorado AI Act SB 205 (2024, effective Feb 2026)
- CCPA / CPRA (California Consumer Privacy Act / Rights Act)
- ABA Model Rules 1.1 (Competence), 1.6 (Confidentiality), 3.4, 5.3
- NIST AI RMF 1.0 (2023) — GOVERN / MAP / MEASURE / MANAGE
- ESIGN Act (2000) + UETA (1999) — electronic signature legality
"""

from __future__ import annotations

from enum import Enum


class ColoradoRiskTier(str, Enum):
    HIGH = "high"
    LIMITED = "limited"


class ColoradoHighRiskCategory(str, Enum):
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    FINANCIAL_SERVICES = "financial_services"
    HOUSING = "housing"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"
    CRIMINAL_JUSTICE = "criminal_justice"
    LEGAL_SERVICES = "legal_services"
    OTHER = "other"


class CCPAConsentType(str, Enum):
    OPT_IN = "opt_in"
    OPT_OUT = "opt_out"
    DO_NOT_SELL = "do_not_sell"
    DO_NOT_SHARE = "do_not_share"
    LIMIT_SENSITIVE = "limit_sensitive"


class NISTProfileTier(str, Enum):
    TIER_1 = "tier-1"  # Partial — ad hoc risk practices
    TIER_2 = "tier-2"  # Risk-informed — approved but not org-wide
    TIER_3 = "tier-3"  # Repeatable — org-wide consistent practices
    TIER_4 = "tier-4"  # Adaptive — continuous improvement, real-time


class ESIGNEventType(str, Enum):
    DOCUMENT_CREATED = "document_created"
    INVITATION_SENT = "invitation_sent"
    DOCUMENT_VIEWED = "document_viewed"
    SIGNED = "signed"
    DECLINED = "declined"
    DELEGATED = "delegated"
    VOIDED = "voided"
    COMPLETED = "completed"


# ABA Model Rules relevant to AI use in legal practice
ABA_RULES = {
    "1.1": "Competence — duty to understand AI tool capabilities and limitations",
    "1.6": "Confidentiality — ensure client data not exposed to third-party AI",
    "3.4": "Fairness to opposing party — no misleading AI-generated content",
    "5.3": "Supervision — attorney must review AI output before reliance",
    "7.1": "Communications — no false advertising of AI-enhanced services",
    "8.4": "Misconduct — AI does not excuse dishonesty or incompetence",
}

# NIST AI RMF Trustworthiness characteristics (NIST AI 100-1)
NIST_TRUSTWORTHINESS = {
    1: "Accountable and transparent",
    2: "Explainable and interpretable",
    3: "Privacy-enhanced",
    4: "Reliable",
    5: "Safe",
    6: "Secure and resilient",
    7: "Fair with harmful bias managed",
}
