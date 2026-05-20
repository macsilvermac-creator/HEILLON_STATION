"""Shared keyword → agent mapping for lightweight mission planning (MVP, no LLM)."""

from __future__ import annotations

KEYWORD_AGENT_MAP: dict[str, str] = {
    "analisar": "analysis-agent",
    "análise": "analysis-agent",
    "analyze": "analysis-agent",
    "classify": "classification-agent",
    "classificar": "classification-agent",
    "ocr": "ocr-agent",
    "digitalizado": "ocr-agent",
    "risco": "analysis-agent",
    "fraude": "analysis-agent",
    "agrupar": "clustering-agent",
    "cluster": "clustering-agent",
    "priorizar": "prioritization-agent",
    "prioritize": "prioritization-agent",
    "relevância": "prioritization-agent",
    "relevancia": "prioritization-agent",
    "extrair": "extraction-agent",
    "resumir": "summarization-agent",
}

SECURITY_SCOPE_MARKERS = (
    "hack",
    "hackear",
    "mainframe",
    "exploit",
    "contrabando",
)


def normalize_text(text: str) -> str:
    """Normalize text into comparable lowercase lexical tokens."""

    return text.casefold()
