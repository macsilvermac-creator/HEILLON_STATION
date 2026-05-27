"""FastAPI deps: parse upstream headers + validate SSRF safety."""

from __future__ import annotations

import ipaddress
import socket
from typing import Annotated
from urllib.parse import urlparse

from fastapi import Header, HTTPException, status

from app.domain.gateway.models import GatewayUpstreamConfig

DEFAULT_UPSTREAM_BASE = "https://api.openai.com"
DEFAULT_UPSTREAM_PROVIDER = "openai"
DEFAULT_ANTHROPIC_BASE = "https://api.anthropic.com"


def _validate_upstream_url(url: str) -> str:
    """SSRF defense — same logic as agent_config_models but headers-level.

    Reject loopback, link-local, private IPs (including via DNS resolution).
    """
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Heillon-Upstream-Url must use http or https",
        )
    host = parsed.hostname or ""
    if not host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Heillon-Upstream-Url missing hostname",
        )

    _BLOCKED_HOSTS = {"localhost", "metadata.google.internal", "169.254.169.254"}
    if host.lower() in _BLOCKED_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upstream host '{host}' not allowed (SSRF protection)",
        )

    # Check literal IP
    try:
        addr = ipaddress.ip_address(host)
        if (
            addr.is_loopback
            or addr.is_link_local
            or addr.is_private
            or addr.is_reserved
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Upstream resolves to restricted IP range: {host}",
            )
    except ValueError:
        # hostname not an IP — resolve and check each
        try:
            resolved_ips = {info[4][0] for info in socket.getaddrinfo(host, None)}
        except (socket.gaierror, OSError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Upstream DNS resolution failed: {host}",
            ) from exc
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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Upstream host '{host}' resolves to restricted IP {ip_str}"
                    ),
                )

    return url.rstrip("/")


def get_upstream_config(
    x_upstream_api_key: Annotated[
        str | None, Header(alias="X-Upstream-Api-Key")
    ] = None,
    x_heillon_upstream_url: Annotated[
        str | None, Header(alias="X-Heillon-Upstream-Url")
    ] = None,
    x_heillon_upstream_provider: Annotated[
        str | None, Header(alias="X-Heillon-Upstream-Provider")
    ] = None,
) -> GatewayUpstreamConfig:
    """Resolve upstream provider/URL/API-key from request headers + defaults.

    The X-Upstream-Api-Key is REQUIRED — the gateway is a pure proxy that does
    not own upstream credentials. Clients supply their own OpenAI/Together/etc
    keys per request. This keeps Heillon out of the credential-custody business.
    """
    if not x_upstream_api_key or not x_upstream_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Missing X-Upstream-Api-Key header — supply your OpenAI/Together/"
                "etc API key. The gateway forwards it as Authorization: Bearer."
            ),
        )

    base_url = (x_heillon_upstream_url or DEFAULT_UPSTREAM_BASE).strip()
    base_url = _validate_upstream_url(base_url)

    provider = (x_heillon_upstream_provider or DEFAULT_UPSTREAM_PROVIDER).strip().lower()
    return GatewayUpstreamConfig(
        upstream_base_url=base_url,
        upstream_api_key=x_upstream_api_key.strip(),
        upstream_provider=provider,
    )


def get_anthropic_upstream_config(
    x_upstream_api_key: Annotated[
        str | None, Header(alias="X-Upstream-Api-Key")
    ] = None,
    x_heillon_upstream_url: Annotated[
        str | None, Header(alias="X-Heillon-Upstream-Url")
    ] = None,
) -> GatewayUpstreamConfig:
    """Resolve upstream config for Anthropic /v1/messages calls.

    Default base URL is api.anthropic.com. Provider is hardcoded to
    "anthropic" so the HDR is labelled correctly even if the user overrides
    upstream_url (e.g. self-hosted Claude proxy).
    """
    if not x_upstream_api_key or not x_upstream_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Missing X-Upstream-Api-Key header — supply your Anthropic "
                "API key (sk-ant-...). Gateway forwards it as x-api-key."
            ),
        )

    base_url = (x_heillon_upstream_url or DEFAULT_ANTHROPIC_BASE).strip()
    base_url = _validate_upstream_url(base_url)

    return GatewayUpstreamConfig(
        upstream_base_url=base_url,
        upstream_api_key=x_upstream_api_key.strip(),
        upstream_provider="anthropic",
    )
