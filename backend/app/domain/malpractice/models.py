"""Malpractice insurance + compliance scoring models — Fase 20."""

from __future__ import annotations

from enum import Enum


class ConsequentialDecisionType(str, Enum):
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    FINANCIAL_SERVICES = "financial_services"
    HOUSING = "housing"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"
    CRIMINAL_JUSTICE = "criminal_justice"
    LEGAL_SERVICES = "legal_services"
    OTHER = "other"


class ADMTPurpose(str, Enum):
    PROFILING = "profiling"
    EMPLOYMENT_DECISIONS = "employment_decisions"
    CREDIT = "credit"
    HOUSING = "housing"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    LEGAL = "legal"
    PUBLIC_ACCOMMODATION = "public_accommodation"
    OTHER = "other"


class CertificationTier(str, Enum):
    UNRATED = "unrated"
    BRONZE = "bronze"      # < 50
    SILVER = "silver"      # 50-74
    GOLD = "gold"          # 75-89
    PLATINUM = "platinum"  # 90+


def tier_from_score(score: int) -> CertificationTier:
    if score >= 90:
        return CertificationTier.PLATINUM
    if score >= 75:
        return CertificationTier.GOLD
    if score >= 50:
        return CertificationTier.SILVER
    if score > 0:
        return CertificationTier.BRONZE
    return CertificationTier.UNRATED


# Colorado SB 26-189 (May 2026) consumer rights
COLORADO_SB26189_RIGHTS: dict[str, str] = {
    "disclosure": "Art. 8: Right to know an AI system made a consequential decision",
    "explanation": "Art. 9: Right to a plain-language explanation of the AI decision",
    "data_correction": "Art. 10: Right to correct inaccurate data used in the decision",
    "human_review": "Art. 11: Right to appeal to a human decision-maker",
    "opt_out": "Art. 12: Right to opt out (limited categories)",
}

# CCPA ADMT Regulations — key rights (effective Jan 1, 2027)
CCPA_ADMT_RIGHTS: dict[str, str] = {
    "pre_use_notice": "§7085: Pre-use notice before ADMT deployment affecting consumers",
    "opt_out": "§1798.121: Right to opt out of ADMT for certain purposes",
    "access": "§1798.100: Right to access ADMT logic and data used",
    "human_review": "Art. 11 Regs: Right to meaningful human review of ADMT outcomes",
    "risk_assessment": "Art. 22 Regs: Risk assessment for high-risk ADMT uses",
}

# Heillon compliance score weights (must sum to 100)
SCORE_WEIGHTS: dict[str, int] = {
    "score_hdr_coverage": 15,        # Core HDR audit trail
    "score_citation_accuracy": 10,   # AI citation verification
    "score_hallucination": 10,       # Hallucination incident rate
    "score_lgpd": 5,                 # Brazil
    "score_gdpr_eu": 8,              # EU
    "score_gdpr_uk": 4,              # UK
    "score_ccpa": 4,                 # California
    "score_colorado": 3,             # Colorado
    "score_pdpl_uae": 4,             # UAE
    "score_pdpa_sg": 3,              # Singapore
    "score_privacy_au": 3,           # Australia
    "score_pipeda_ca": 3,            # Canada
    "score_iso42001": 10,            # AIMS
    "score_iso27001": 8,             # ISMS
    "score_nist_rmf": 5,             # NIST
    "score_euai_act": 8,             # EU AI Act
    "score_attorney_competence": 7,  # ABA compliance
}
# Total: 110 → normalize to 100 in computation
