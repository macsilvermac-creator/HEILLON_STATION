"""Compliance DTOs for constitutional anchoring & LGPD reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ArticleEvidence(BaseModel):
    """Evidence extracted for one framework article."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    article_id: str
    fields: dict[str, str] = Field(default_factory=dict)


class FrameworkAnchorBlock(BaseModel):
    """Anchoring outcome for one framework."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    framework_id: str
    framework_name: str
    articles: list[ArticleEvidence]
    anchored_at: datetime


class HDRAnchorRecord(BaseModel):
    """One HDR anchored against requested frameworks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hdr_id: str
    anchors: list[FrameworkAnchorBlock]

    def is_fully_compliant(self) -> bool:
        """Heuristic completeness — each article exposes at least one non-empty field mapping."""

        if not self.anchors:
            return False
        for block in self.anchors:
            for art in block.articles:
                if not any(bool(v and str(v).strip()) for v in art.fields.values()):
                    return False
        return True


class ComplianceReportSummary(BaseModel):
    """Machine report summarizing mission compliance versus a framework."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mission_id: str
    framework_id: str
    framework_name: str
    total_hdrs: int
    compliant_hdrs: int
    hdr_anchors: list[HDRAnchorRecord]
    generated_at: datetime
    extra: dict[str, Any] = Field(default_factory=dict)
