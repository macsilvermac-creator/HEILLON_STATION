"""Gateway forwarding service.

We use httpx.AsyncClient for upstream calls (no blocking I/O). HDR creation
runs in a FastAPI BackgroundTask so the response returns to the client as
fast as the upstream allows.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.domain.gateway.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    GatewayUpstreamConfig,
)

logger = logging.getLogger("heillon.legal.gateway")

# Upstream timeouts: be patient with LLMs (some take >30s for long completions)
UPSTREAM_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=120.0,
    write=30.0,
    pool=10.0,
)


class UpstreamError(RuntimeError):
    """Raised when upstream returns non-2xx; carries status + body for proxying."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Upstream returned HTTP {status_code}")


async def forward_chat_completion(
    *,
    request: ChatCompletionRequest,
    upstream: GatewayUpstreamConfig,
) -> ChatCompletionResponse:
    """Forward a chat completion to the configured upstream and return its response.

    Raises UpstreamError on non-2xx (preserves status + body for verbatim proxying).
    """
    url = f"{upstream.upstream_base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {upstream.upstream_api_key}",
        "Content-Type": "application/json",
        # Identify ourselves to upstream so they can attribute traffic
        "User-Agent": "HeillonGateway/1.0",
    }
    # Pass through every field the client sent (including future OpenAI additions)
    body = request.model_dump(exclude_none=True, mode="json")

    async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
        try:
            response = await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            logger.warning("Upstream HTTP error to %s: %s", url, exc)
            raise UpstreamError(502, {"error": {"message": f"Upstream unreachable: {exc}"}})

    if response.status_code >= 400:
        # Parse JSON body if possible; fall back to raw text
        try:
            err_body: Any = response.json()
        except Exception:  # noqa: BLE001
            err_body = {"error": {"message": response.text[:500]}}
        raise UpstreamError(response.status_code, err_body)

    try:
        payload = response.json()
    except Exception as exc:  # noqa: BLE001
        raise UpstreamError(
            502,
            {"error": {"message": f"Upstream returned non-JSON: {exc}"}},
        ) from exc

    # Lenient parsing — extras pass through via extra="allow"
    return ChatCompletionResponse.model_validate(payload)


def extract_prompt_text(request: ChatCompletionRequest) -> str:
    """Concatenate messages into a single prompt blob for hashing + preview.

    Format: "<role>: <content>" joined by double newline. System messages
    included as they shape the model's behavior and are evidence-worthy.
    """
    parts: list[str] = []
    for msg in request.messages:
        content = (msg.content or "").strip()
        if not content:
            continue
        parts.append(f"{msg.role}: {content}")
    return "\n\n".join(parts)


def extract_response_text(response: ChatCompletionResponse) -> str:
    """Concatenate all assistant choice contents (some models return N alternatives)."""
    parts: list[str] = []
    for choice in response.choices:
        content = (choice.message.content or "").strip()
        if content:
            parts.append(content)
    return "\n\n---\n\n".join(parts) if parts else "(empty response)"
