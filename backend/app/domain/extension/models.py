"""Extension capture payloads — strict validation, privacy-first."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# Max sizes — protect against runaway prompts and DoS
MAX_PROMPT_CHARS = 64_000
MAX_RESPONSE_CHARS = 256_000
MAX_URL_CHARS = 2048


class AiProvider(str, Enum):
    """Recognized AI providers (extension may detect others; we whitelist common ones)."""

    OPENAI = "openai"  # ChatGPT, GPT-4, GPT-5
    ANTHROPIC = "anthropic"  # Claude
    GOOGLE = "google"  # Gemini, Bard
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    META = "meta"  # Llama, Meta.ai
    PERPLEXITY = "perplexity"
    OTHER = "other"


class ExtensionCaptureRequest(BaseModel):
    """Single AI interaction captured by the browser extension.

    Each capture becomes 1 HDR (counts against monthly quota).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: AiProvider
    model: str = Field(
        min_length=1,
        max_length=120,
        description="Model identifier as known by the provider (e.g. 'gpt-4o', 'claude-3.5-sonnet').",
    )
    prompt: str = Field(
        min_length=1,
        max_length=MAX_PROMPT_CHARS,
        description="User's input to the AI (truncated by extension if longer).",
    )
    response: str = Field(
        min_length=1,
        max_length=MAX_RESPONSE_CHARS,
        description="AI's response captured from the DOM.",
    )
    source_url: HttpUrl = Field(
        description="URL where the interaction occurred (e.g. https://chat.openai.com/c/...).",
    )
    captured_at: datetime = Field(
        description="When the extension observed this interaction (client clock).",
    )
    ai_session_id: str | None = Field(
        default=None,
        max_length=200,
        description="Provider's conversation/session ID, when available — links related captures.",
    )
    extension_version: str | None = Field(
        default=None,
        max_length=20,
        description="Browser extension version (semver) for compatibility tracking.",
    )
    page_title: str | None = Field(
        default=None,
        max_length=300,
        description="Page title at capture time — helps user identify the case context.",
    )


class ExtensionCaptureResponse(BaseModel):
    """Response to a successful capture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["captured"] = "captured"
    hdr_id: str = Field(description="Cryptographic ID of the generated HDR (64 hex).")
    mission_id: str = Field(description="Mission grouping this capture (auto-created if needed).")
    verification_url: str = Field(
        description="Public URL to verify this HDR (no auth required).",
    )
    quota: ExtensionCaptureQuota = Field(
        description="Updated quota snapshot — extension uses this to show usage.",
    )


class ExtensionCaptureQuota(BaseModel):
    """Subset of QuotaSnapshot relevant to the extension UI."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    used: int
    limit: int | None
    remaining: int | None
    tier: str


class ExtensionHealthResponse(BaseModel):
    """GET /api/v1/extension/health — verifies API key + returns config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ok: Literal[True] = True
    organization_id: str
    tier: str
    quota: ExtensionCaptureQuota
    server_time: datetime
    capture_endpoint: str = "/api/v1/extension/capture"
