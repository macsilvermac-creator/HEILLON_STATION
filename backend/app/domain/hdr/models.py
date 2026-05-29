"""HDR (Heillon Decision Record) schema v1 — Pydantic models."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

HdrTypeLiteral = Literal[
    "ingestion",
    "intention",
    "ocr",
    "classification",
    "analysis",
    "clustering",
    "priority",
    "mission",
    "violation",
]

ExecutionStatusLiteral = Literal["completed", "failed", "aborted"]


class HDRAgent(BaseModel):
    """Identifies the autonomous agent executing the step."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    model: str = Field(
        description="Underlying model identifier (e.g. tesseract variant)."
    )
    version: str = Field(
        description="Version string of agent software / configuration."
    )


class HDRUser(BaseModel):
    """Acting credential information including optional Ed25519 signature."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    signature: str | None = Field(
        default=None,
        description="Detached Ed25519 signature over canonical payload (hex-encoded), if present.",
    )


class HDRIntent(BaseModel):
    """Declared intent preceding execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str
    tools_required: Annotated[list[str], Field(description="Tools or agents required.")]
    estimated_cost_gas: float = Field(
        ...,
        ge=0.0,
        description="Relative metering unit for budgeting (opaque v1 heuristic).",
    )


class HDRExecution(BaseModel):
    """Execution artefacts and hashing of inputs / outputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: ExecutionStatusLiteral
    input_hash: str = Field(...)
    output_hash: str | None = Field(
        None,
        description="Digest of deterministic output artefacts (hex SHA-256) when applicable.",
    )
    duration_ms: int | None = Field(default=None, ge=0)

    @staticmethod
    def _norm_hex_digest(value: str) -> str:
        """Normalize a 64-character lowercase SHA-256 digest string."""

        v = value.lower()
        if len(v) != 64 or any(c not in "0123456789abcdef" for c in v):
            msg = "Execution hashes must be 64 hexadecimal characters."
            raise ValueError(msg)
        return v

    @field_validator("input_hash", mode="before")
    @classmethod
    def normalized_input_sha256(cls, v: Any) -> str:
        """Force lowercase SHA-256 representation."""

        return cls._norm_hex_digest(str(v))

    @field_validator("output_hash", mode="before")
    @classmethod
    def normalized_output_optional(cls, v: Any) -> str | None:
        """Allow missing output hash or normalize hexadecimal digest."""

        if v is None or v == "":
            return None
        return cls._norm_hex_digest(str(v))


class HDRCognitiveSnapshot(BaseModel):
    """Interpretable heuristic snapshot documenting reasoning trace."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hypothesis: str
    action: str
    result: str


class HDRNormative(BaseModel):
    """Outcome of Corpus Normativo policy checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checked: bool
    violations: list[str]
    corpus_version: str


class HDR(BaseModel):
    """Immutable HDR record enforcing schema v1 invariants."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hdr_id: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    hdr_version: str = Field(default="1.0")
    hdr_type: HdrTypeLiteral
    mission_id: str

    timestamp: str = Field(
        ...,
        description="RFC 3339 / ISO8601 UTC timestamp emitted at authoring time.",
    )
    timestamp_trusted: str = Field(
        ...,
        description="Base64-encoded DER TimeStampResp from RFC 3161 authority.",
    )

    agent: HDRAgent
    user: HDRUser
    intent: HDRIntent
    execution: HDRExecution
    cognitive_snapshot: HDRCognitiveSnapshot
    normative: HDRNormative

    previous_hdr: str | None = Field(
        default=None,
        description="hdr_id predecessor in immutable append-only chain.",
    )
    supersedes: str | None = None
    corrects: str | None = None

    canonical_hash: str = Field(..., pattern=r"^[0-9a-f]{64}$")


class ChainVerificationDetails(BaseModel):
    """Structured machine-readable verdict details."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    steps: list[str] = Field(default_factory=list)


class ChainVerificationResult(BaseModel):
    """Outcome of chronological HDR chain validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool = Field(description="Overall chain cryptographic validity.")
    broken_at: int | None = Field(
        default=None,
        description="Index (0-based) of first offending HDR link; None when valid.",
    )
    details: ChainVerificationDetails = Field(default_factory=ChainVerificationDetails)
