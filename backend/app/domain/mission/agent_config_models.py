"""Per-tenant EASY agent cognition routing configurations (model sovereignty)."""

from __future__ import annotations

import ipaddress
from datetime import UTC, datetime
from enum import Enum
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


def _validate_ssrf_safe_url(url: str | None) -> str | None:
    """Reject SSRF-prone URLs: loopback, link-local, private ranges, metadata endpoints."""

    if url is None:
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        msg = "api_base_url must use http or https"
        raise ValueError(msg)
    host = parsed.hostname or ""
    if not host:
        msg = "api_base_url must include a valid hostname"
        raise ValueError(msg)
    _BLOCKED_HOSTS = {
        "localhost",
        "metadata.google.internal",
        "169.254.169.254",
    }
    if host.lower() in _BLOCKED_HOSTS:
        msg = f"api_base_url host '{host}' is not allowed (SSRF protection)"
        raise ValueError(msg)
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_loopback or addr.is_link_local or addr.is_private or addr.is_reserved:
            msg = f"api_base_url resolves to a restricted IP range: {host}"
            raise ValueError(msg)
    except ValueError as exc:
        if "not allowed" in str(exc) or "resolves to" in str(exc):
            raise
    return url.strip()


class AgentConfigUpdate(BaseModel):
    """Operator mutation payload — empty optional api_key retains prior encrypted value."""

    model_config = ConfigDict(extra="forbid")

    source: AgentModelSource = AgentModelSource.STUB
    model_name: str | None = None
    api_key: str | None = None
    api_base_url: str | None = None

    @model_validator(mode="after")
    def validate_ssrf_for_custom_source(self) -> AgentConfigUpdate:
        """Apply SSRF restrictions only for CUSTOM source; OLLAMA allows localhost."""

        if self.source == AgentModelSource.CUSTOM:
            _validate_ssrf_safe_url(self.api_base_url)
        return self


class AgentConfigTestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    execution_status: str | None = None
    cognitive_excerpt: str | None = None
    detail: str | None = None
