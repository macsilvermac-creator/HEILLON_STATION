"""Per-tenant EASY agent cognition routing configurations (model sovereignty)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AgentModelSource(str, Enum):
    """Where inference runs — local Ollama, hosted APIs, or deterministic stub."""

    STUB = "stub"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class AgentConfig(BaseModel):
    """Sanitized projection returned via HTTP (secrets never surfaced)."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    organization_id: str
    source: AgentModelSource
    model_name: str | None = None
    api_base_url: str | None = None
    api_key_is_set: bool = False
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentConfigUpdate(BaseModel):
    """Operator mutation payload — empty optional api_key retains prior encrypted value."""

    model_config = ConfigDict(extra="forbid")

    source: AgentModelSource = AgentModelSource.STUB
    model_name: str | None = None
    api_key: str | None = None
    api_base_url: str | None = None


class AgentConfigTestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    execution_status: str | None = None
    cognitive_excerpt: str | None = None
    detail: str | None = None
