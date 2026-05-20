"""Normative Corpus models enforcing pre-execution governance."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class NormativeCategory(str, Enum):
    """High-level segregation of Corpus Normativo rules."""

    LEGAL = "legal"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    CUSTOM = "custom"


class ViolationAction(str, Enum):
    """Enforcement modality when a deterministic rule predicates match."""

    BLOCK = "BLOCK"
    REALIGN = "REALIGN"
    WARN = "WARN"


class NormativeRule(BaseModel):
    """Declarative courtroom-grade rule metadata evaluated prior to EASY execution."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    rule_id: str
    name: str
    description: str
    category: NormativeCategory
    condition: str
    action_on_violation: ViolationAction
    priority: int = Field(default=50, ge=1, le=100)
    enabled: bool = True


class NormativeViolation(BaseModel):
    """Evidence-grade record describing a breached normative invariant."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    rule_name: str
    reason: str


class NormativeResult(BaseModel):
    """Composite adjudication artefact surfaced to orchestration services."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    allowed: bool
    violations: list[NormativeViolation] = Field(default_factory=list)
    warnings: list[NormativeViolation] = Field(default_factory=list)
    suggested_realignment: str | None = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
