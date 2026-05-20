"""Normative framework registry (constitutional anchor metadata)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class FrameworkType(str, Enum):
    """Legal instrument classification."""

    LAW = "law"
    REGULATION = "regulation"
    CERTIFICATION = "certification"
    CORPORATE_POLICY = "corporate"
    CONTRACT = "contract"


class FrameworkArticle(BaseModel):
    """Article / clause slice used for HDR evidence mapping."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    article_id: str
    title: str
    text_summary: str
    compliance_requirements: List[str] = Field(default_factory=list)
    hdr_evidence_fields: List[str] = Field(default_factory=list)


class NormativeFramework(BaseModel):
    """A jurisdiction or policy stack that HDRs can be anchored against."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    framework_id: str
    name: str
    type: FrameworkType
    jurisdiction: str
    version: str
    articles: List[FrameworkArticle] = Field(default_factory=list)
    effective_date: datetime
    description: str
