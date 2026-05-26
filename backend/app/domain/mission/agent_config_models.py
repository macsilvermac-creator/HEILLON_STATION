"""Per-tenant EASY agent cognition routing configurations (model sovereignty)."""

from __future__ import annotations

import ipaddress
import socket
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
    # 1) Check literal hostname (covers raw IPs like 127.0.0.1, 169.254.169.254)
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_loopback or addr.is_link_local or addr.is_private or addr.is_reserved:
            msg = f"api_base_url resolves to a restricted IP range: {host}"
            raise ValueError(msg)
    except ValueError as exc:
        if "not allowed" in str(exc) or "resolves to" in str(exc):
            raise
        # host is a domain name, not an IP — fall through to DNS resolution
    # 2) Resolve DNS and validate EVERY returned IP (defeats DNS rebinding)
    try:
        resolved_ips = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except (socket.gaierror, OSError) as exc:
        msg = f"api_base_url DNS resolution failed for host '{host}': {exc}"
        raise ValueError(msg) from exc
    for ip_str in resolved_ips:
        try:
            resolved_addr = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (
            resolved_addr.is_loopback
            or resolved_addr.is_link_local
            or resolved_addr.is_private
            or resolved_addr.is_reserved
            or resolved_addr.is_multicast
        ):
            msg = (
                f"api_base_url host '{host}' resolves to restricted IP {ip_str} "
                "(SSRF protection: DNS rebinding blocked)"
            )
            raise ValueError(msg)
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
