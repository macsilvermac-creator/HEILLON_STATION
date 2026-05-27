"""Gateway forwarding service.

We use httpx.AsyncClient for upstream calls (no blocking I/O). HDR creation
runs synchronously in the request so X-Heillon-Hdr-Id can be returned in
response headers (non-streaming) or via SSE comment (streaming).

Streaming (F31.1): forward_chat_completion_stream yields SSE bytes verbatim
to the client while a StreamAccumulator captures delta.content in parallel.
After the stream ends, caller reads accumulator.text and creates the HDR.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

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


# ── Streaming (F31.1) ────────────────────────────────────────────────────────


class StreamAccumulator:
    """Captures delta.content fragments as they stream through.

    Single-stream, not thread-safe; one per request. Caller reads `text`
    after the streaming generator exhausts, then persists HDR.
    """

    __slots__ = ("_parts", "had_error", "upstream_status")

    def __init__(self) -> None:
        self._parts: list[str] = []
        self.had_error: bool = False
        self.upstream_status: int = 0

    def append(self, fragment: str) -> None:
        if fragment:
            self._parts.append(fragment)

    @property
    def text(self) -> str:
        return "".join(self._parts) if self._parts else "(empty streamed response)"


def _parse_sse_data_line(line: str) -> dict[str, Any] | None:
    """Parse 'data: {...}' → dict. Returns None for [DONE], comments, or invalid JSON."""
    if not line.startswith("data:"):
        return None
    payload = line[len("data:"):].strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _extract_delta_content(parsed_chunk: dict[str, Any]) -> str | None:
    """OpenAI stream chunk → assistant delta.content fragment (if any)."""
    choices = parsed_chunk.get("choices") or []
    for choice in choices:
        delta = choice.get("delta") or {}
        content = delta.get("content")
        if isinstance(content, str) and content:
            return content
    return None


async def forward_chat_completion_stream(
    *,
    request_body: dict[str, Any],
    upstream: GatewayUpstreamConfig,
    accumulator: StreamAccumulator,
) -> AsyncIterator[bytes]:
    """Yield SSE bytes verbatim from upstream while accumulating delta.content.

    Caller responsibilities:
    - Pass an empty StreamAccumulator that will be populated as chunks flow
    - After generator exhausts: read accumulator.text to persist HDR
    - Check accumulator.had_error for upstream non-2xx (HDR not created in that case)

    Connection/timeout failures surface as a synthetic SSE error event so
    OpenAI-compatible clients can handle them in their event loop instead of
    seeing an opaque connection drop.
    """
    url = f"{upstream.upstream_base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {upstream.upstream_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "HeillonGateway/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
            async with client.stream(
                "POST", url, headers=headers, json=request_body
            ) as response:
                accumulator.upstream_status = response.status_code

                if response.status_code >= 400:
                    accumulator.had_error = True
                    raw = await response.aread()
                    try:
                        err_payload = json.loads(raw.decode("utf-8"))
                    except Exception:  # noqa: BLE001
                        err_payload = {
                            "error": {
                                "message": raw.decode("utf-8", errors="replace")[:500],
                                "type": "upstream_error",
                            }
                        }
                    yield f"data: {json.dumps(err_payload)}\n\n".encode("utf-8")
                    yield b"data: [DONE]\n\n"
                    return

                async for line in response.aiter_lines():
                    # httpx aiter_lines strips the trailing newline; reassemble SSE format.
                    # Per SSE spec, events are terminated by a blank line.
                    if line == "":
                        yield b"\n"
                        continue

                    # Accumulate content chunks in parallel with forwarding
                    parsed = _parse_sse_data_line(line)
                    if parsed is not None:
                        delta = _extract_delta_content(parsed)
                        if delta:
                            accumulator.append(delta)

                    yield (line + "\n").encode("utf-8")
    except httpx.HTTPError as exc:
        logger.warning("Streaming upstream HTTP error: %s", exc)
        accumulator.had_error = True
        err_payload = {
            "error": {
                "message": f"Upstream unreachable: {exc}",
                "type": "heillon_gateway_error",
            }
        }
        yield f"data: {json.dumps(err_payload)}\n\n".encode("utf-8")
        yield b"data: [DONE]\n\n"
