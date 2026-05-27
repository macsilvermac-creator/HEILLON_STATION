"""OpenAI Chat Completions-compatible request/response models.

We use lenient validation (extra="allow") so future OpenAI API additions
pass through transparently without code changes.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


MessageRole = Literal["system", "user", "assistant", "tool", "function"]


class ChatMessage(BaseModel):
    """A single message in the conversation.

    Permissive: name/tool_call_id/etc may appear; we forward whatever the
    client sends. We only require role + content for capture.
    """

    model_config = ConfigDict(extra="allow")

    role: MessageRole
    content: str | None = Field(
        default=None,
        description="Text content. None when only tool_calls are present.",
    )


class ChatCompletionRequest(BaseModel):
    """Subset we read for routing + capture. Extras pass through to upstream."""

    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1, max_length=200)
    messages: list[ChatMessage] = Field(min_length=1)
    stream: bool = Field(default=False, description="MVP rejects stream=true.")
    temperature: float | None = None
    max_tokens: int | None = None
    user: str | None = Field(
        default=None,
        description="Optional client-side user identifier (passed to upstream + captured).",
    )


class ChatCompletionChoiceMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str = "assistant"
    content: str | None = None


class ChatCompletionChoice(BaseModel):
    model_config = ConfigDict(extra="allow")

    index: int
    message: ChatCompletionChoiceMessage
    finish_reason: str | None = None


class ChatCompletionUsage(BaseModel):
    model_config = ConfigDict(extra="allow")

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """Upstream response as we surface it to the client (extras allowed)."""

    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage | None = None


# ── Gateway-specific surface ─────────────────────────────────────────────────


class GatewayUpstreamConfig(BaseModel):
    """Parsed gateway routing inputs (from headers + defaults)."""

    model_config = ConfigDict(frozen=True)

    upstream_base_url: str
    upstream_api_key: str
    upstream_provider: str  # "openai" | "anthropic" | etc for HDR labeling


class GatewayQuotaHeaders(BaseModel):
    """Heillon-specific response headers added on top of the upstream response."""

    model_config = ConfigDict(frozen=True)

    hdr_id: str | None
    quota_used: int
    quota_limit: int | None
    quota_tier: str
