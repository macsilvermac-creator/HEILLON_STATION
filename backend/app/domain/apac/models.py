"""APAC + Global privacy compliance models — UK / Canada / Singapore / Australia."""

from __future__ import annotations

from enum import Enum


class UKLawfulBasis(str, Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class CanadaProvincialLaw(str, Enum):
    FEDERAL = "federal"
    QUEBEC = "quebec"
    ALBERTA = "alberta"
    BC = "bc"


class EUTransferMechanism(str, Enum):
    ADEQUACY = "adequacy"
    IDTA = "idta"
    BCR = "bcr"
    DEROGATIONS = "derogations"
    NONE = "none"


# UK ICO registration threshold (organizations processing personal data)
UK_ICO_EXEMPTIONS: dict[str, str] = {
    "small_business": "Annual turnover under £632K + fewer than 10 employees",
    "not_for_profit": "Not-for-profit processing only for member/supporter data",
    "personal_use": "Processing solely for personal/household purposes",
    "judicial": "Processing for judicial functions",
}

# Singapore PDPA — Agentic AI Framework 5 obligations (Jan 2026)
PDPC_AGENTIC_OBLIGATIONS: dict[str, str] = {
    "accountability": "Human oversight mechanisms for autonomous AI actions",
    "transparency": "Disclosure to data subjects that they interact with an AI agent",
    "consent": "Appropriate consent scope for autonomous data processing",
    "data_minimisation": "Limit data access to what is necessary for agent tasks",
    "incident_response": "Procedures for autonomous agent failures and data breaches",
}

# Australia Privacy Principles (APPs) summary
AUSTRALIA_APPS: dict[str, str] = {
    "APP1": "Open/transparent management of personal information",
    "APP2": "Anonymity and pseudonymity options",
    "APP3": "Collection of solicited personal information",
    "APP4": "Dealing with unsolicited personal information",
    "APP5": "Notification of collection of personal information",
    "APP6": "Use or disclosure of personal information",
    "APP7": "Direct marketing",
    "APP8": "Cross-border disclosure of personal information",
    "APP9": "Adoption, use or disclosure of government identifiers",
    "APP10": "Quality of personal information",
    "APP11": "Security of personal information",
    "APP12": "Access to personal information",
    "APP13": "Correction of personal information",
}
