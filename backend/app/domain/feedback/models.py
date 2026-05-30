"""Domain models for the beta feedback bounded context.

The submission model accepts four 0..10 usability/experience/functionality/
"delivers" axes, an NPS score, an adoption intent, and free-text. The summary
models are aggregate-only and de-identified: averages, NPS breakdown, adoption
breakdown, and a flat list of comments NEVER joined to user/organization — the
same privacy posture as the /admin metrics surface.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Adoption-intent vocabulary (kept loose; validated by length only).
ADOPT_CHOICES = ("now", "3-6m", "12m", "depends", "no")


class FeedbackSubmission(BaseModel):
    """Payload posted by an authenticated beta user. All fields optional so a
    respondent can answer only the axes they care about."""

    model_config = ConfigDict(extra="forbid")

    usability: int | None = Field(default=None, ge=0, le=10)
    experience: int | None = Field(default=None, ge=0, le=10)
    functionality: int | None = Field(default=None, ge=0, le=10)
    delivers: int | None = Field(default=None, ge=0, le=10)
    nps: int | None = Field(default=None, ge=0, le=10)

    adopt: str | None = Field(default=None, max_length=40)
    role: str | None = Field(default=None, max_length=60)

    most_valuable: str | None = Field(default=None, max_length=2000)
    frictions: str | None = Field(default=None, max_length=2000)
    improvements: str | None = Field(default=None, max_length=2000)

    contact_ok: bool = False


class FeedbackAck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: str
    message: str = "Obrigado pela sua opinião — ela molda diretamente o produto."


class AxisAverages(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usability: float | None = None
    experience: float | None = None
    functionality: float | None = None
    delivers: float | None = None


class NpsSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    responses: int = 0
    promoters: int = 0
    passives: int = 0
    detractors: int = 0
    score: float | None = None  # classic NPS, range -100..100


class FeedbackComment(BaseModel):
    """De-identified free-text — never carries user/org identity."""

    model_config = ConfigDict(extra="forbid")

    created_at: str
    most_valuable: str | None = None
    frictions: str | None = None
    improvements: str | None = None


class FeedbackSummary(BaseModel):
    """Aggregate snapshot for the operator dashboard."""

    model_config = ConfigDict(extra="forbid")

    snapshot_at: str
    response_count: int = 0
    averages: AxisAverages
    nps: NpsSummary
    adopt_breakdown: dict[str, int] = Field(default_factory=dict)
    contact_optins: int = 0
    recent_comments: list[FeedbackComment] = Field(default_factory=list)
