"""UAE regulatory compliance models — Fase 19.

Standards covered:
- UAE PDPL: Federal Decree-Law No. 45 of 2021 on Personal Data Protection
- UAE AI Ethics Principles (7 pillars — Ministry of AI, 2019)
- UAE AI Strategy 2031 (National AI Plan)
- Dubai AI Seal (awarded by Ministry of AI / Smart Dubai)
- DIFC Data Protection Law 2020 (DIFC Law No. 5 of 2020)
- ADGM Data Protection Regulations 2021
- UAE PASS — national digital identity / qualified signatures (TDRA)
- UAE Electronic Transactions Law (Federal Law No. 1 of 2006, updated)
"""

from __future__ import annotations

from enum import Enum


class UAELegalBasis(str, Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_INTEREST = "public_interest"
    LEGITIMATE_INTEREST = "legitimate_interest"


class UAEJurisdiction(str, Enum):
    FEDERAL = "federal"
    DUBAI = "dubai"
    ABU_DHABI = "abu_dhabi"
    SHARJAH = "sharjah"
    DIFC = "difc"          # Dubai International Financial Centre (separate legal system)
    ADGM = "adgm"          # Abu Dhabi Global Market (separate legal system)
    DMCC = "dmcc"          # Dubai Multi Commodities Centre


class UAEAISector(str, Enum):
    LEGAL = "legal"
    HEALTH = "health"
    TRANSPORT = "transport"
    SPACE = "space"
    RENEWABLE_ENERGY = "renewable_energy"
    WATER = "water"
    TECHNOLOGY = "technology"
    EDUCATION = "education"
    ECONOMY = "economy"
    CYBERSECURITY = "cybersecurity"
    TELECOMMUNICATIONS = "telecommunications"


class UAEPassIdentityLevel(str, Enum):
    BASIC = "basic"
    VERIFIED = "verified"
    QUALIFIED = "qualified"


class UAETrustServiceLevel(str, Enum):
    QUALIFIED = "qualified"
    ADVANCED = "advanced"
    BASIC = "basic"


# UAE AI Ethics Principles (7 pillars, Ministry of AI 2019)
UAE_AI_ETHICS_PRINCIPLES = {
    "ethics_human_centered": (
        "Principle 1: Human-Centred — AI must augment human capabilities, "
        "respect human rights and dignity"
    ),
    "ethics_fairness": (
        "Principle 2: Fairness — AI must not discriminate, must be inclusive "
        "across demographics"
    ),
    "ethics_transparency": (
        "Principle 3: Transparency — AI decisions must be explainable and auditable"
    ),
    "ethics_safety_reliability": (
        "Principle 4: Safety & Reliability — AI must be robust, tested, and safe to deploy"
    ),
    "ethics_privacy_security": (
        "Principle 5: Privacy & Security — data handled per UAE PDPL and TDRA guidelines"
    ),
    "ethics_accountability": (
        "Principle 6: Accountability — clear responsibility chain for AI decisions"
    ),
    "ethics_sustainability": (
        "Principle 7: Environmental Sustainability — AI must consider energy and "
        "environmental impact"
    ),
}

# DIFC-specific data protection requirements
DIFC_DP_REQUIREMENTS = {
    "lawful_basis": "Art. 10 — Processing must have lawful basis",
    "purpose_limitation": "Art. 11 — Data used only for specified purposes",
    "data_minimisation": "Art. 12 — Only necessary data collected",
    "accuracy": "Art. 13 — Data must be accurate and up-to-date",
    "storage_limitation": "Art. 14 — Data not kept longer than necessary",
    "security": "Art. 15 — Appropriate technical and organisational measures",
    "accountability": "Art. 16 — Controller responsibility and DPO",
    "cross_border": "Art. 27 — Transfer only to adequate jurisdictions",
}
