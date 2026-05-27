"""F31.2 — Gateway Anthropic Messages compat tests."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient


def _fresh_app():
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/gw_anth_test.db"
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["FORCE_STUB_TIMESTAMP"] = "true"

    from app.core import config

    config._settings = None
    from app.core.config import get_settings
    from app.db.database import init_database
    from app.main import create_application

    settings = get_settings()
    init_database(settings)
    return TestClient(create_application()), settings


def _bootstrap_user_and_key(settings) -> str:
    from app.db.compat import open_connection
    from app.domain.api_keys.services import ApiKeyService
    from app.domain.user.models import UserRole
    from app.domain.user.repository import UserRepository

    with open_connection(settings) as conn:
        user = UserRepository.create_user(
            conn,
            email=f"anth-{datetime.now().timestamp()}@x.com",
            name="Anth User",
            hashed_password="x",
            role=UserRole.ADVOGADO,
            organization_id="org_default",
        )
        minted = ApiKeyService.mint(
            conn,
            organization_id="org_default",
            user_id=user.user_id,
            name="Anthropic gw key",
        )
    return minted.plaintext_key


def _mock_anthropic_response():
    """Standard Anthropic Messages API success response."""
    return {
        "id": "msg_01abc",
        "type": "message",
        "role": "assistant",
        "model": "claude-3-5-sonnet-20241022",
        "content": [
            {"type": "text", "text": "O art. 7º LGPD lista as bases legais."},
        ],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 30, "output_tokens": 12},
    }


def _valid_anthropic_payload() -> dict:
    return {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 256,
        "system": "Você é um advogado especialista em LGPD.",
        "messages": [
            {"role": "user", "content": "Resuma o art. 7º da LGPD."}
        ],
    }


# ── 1. Auth required ───────────────────────────────────────────────────────────


def test_anthropic_requires_heillon_api_key():
    client, _ = _fresh_app()
    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=_valid_anthropic_payload(),
        headers={"X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 401


def test_anthropic_requires_upstream_api_key():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=_valid_anthropic_payload(),
        headers={"X-Heillon-Api-Key": key},
    )
    assert r.status_code == 400
    assert "X-Upstream-Api-Key" in r.json()["detail"]


# ── 2. Validation: model + messages required ───────────────────────────────────


def test_anthropic_missing_model_rejected():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    payload = _valid_anthropic_payload()
    del payload["model"]
    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=payload,
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 422
    assert "model" in r.json()["detail"].lower()


def test_anthropic_missing_messages_rejected():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    payload = _valid_anthropic_payload()
    del payload["messages"]
    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=payload,
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 422


# ── 3. Happy path sync: forward + HDR + headers ───────────────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_anthropic_sync_happy_path(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    mock_resp = httpx.Response(200, json=_mock_anthropic_response())
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock(return_value=mock_resp)

    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=_valid_anthropic_payload(),
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"] == "message"
    assert body["content"][0]["text"].startswith("O art. 7º")

    # Heillon headers present
    assert "X-Heillon-Hdr-Id" in r.headers
    assert len(r.headers["X-Heillon-Hdr-Id"]) == 64
    assert r.headers["X-Heillon-Quota-Used"] == "1"
    assert r.headers["X-Heillon-Quota-Tier"] == "free"

    # Confirm upstream was called with proper Anthropic auth headers
    call_args = instance.post.call_args
    assert call_args[0][0].endswith("/v1/messages")
    headers_sent = call_args.kwargs["headers"]
    assert headers_sent["x-api-key"] == "sk-ant-fake"
    assert "anthropic-version" in headers_sent


# ── 4. anthropic-version header propagated ─────────────────────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_anthropic_version_header_forwarded(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    mock_resp = httpx.Response(200, json=_mock_anthropic_response())
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock(return_value=mock_resp)

    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=_valid_anthropic_payload(),
        headers={
            "X-Heillon-Api-Key": key,
            "X-Upstream-Api-Key": "sk-ant-fake",
            "anthropic-version": "2024-10-22",
        },
    )
    assert r.status_code == 200
    headers_sent = instance.post.call_args.kwargs["headers"]
    assert headers_sent["anthropic-version"] == "2024-10-22"


# ── 5. Upstream error proxied verbatim ─────────────────────────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_anthropic_proxies_upstream_errors(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    err_body = {"type": "error", "error": {"type": "invalid_request_error", "message": "model not found"}}
    mock_resp = httpx.Response(400, json=err_body)
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock(return_value=mock_resp)

    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=_valid_anthropic_payload(),
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["type"] == "invalid_request_error"


# ── 6. Quota 402 (without burning upstream) ────────────────────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_anthropic_quota_402(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    from app.db.compat import open_connection

    now_iso = datetime.now(timezone.utc).isoformat()
    with open_connection(settings) as conn:
        for i in range(50):
            conn.execute(
                """INSERT INTO hdrs (hdr_id, mission_id, previous_hdr, hdr_type,
                                      timestamp_iso, canonical_hash, payload,
                                      organization_id, created_at)
                   VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)""",
                (
                    f"apad_{i:03d}", "ma", "analysis", now_iso,
                    "h" * 64, "{}", "org_default", now_iso,
                ),
            )

    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock()

    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=_valid_anthropic_payload(),
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 402
    instance.post.assert_not_called()


# ── 7. System message (top-level) captured in HDR prompt ──────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_anthropic_system_captured_in_hdr(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    mock_resp = httpx.Response(200, json=_mock_anthropic_response())
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock(return_value=mock_resp)

    payload = _valid_anthropic_payload()
    payload["system"] = "Você é um especialista em LGPD."

    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=payload,
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 200
    hdr_id = r.headers["X-Heillon-Hdr-Id"]

    from app.db.compat import open_connection

    with open_connection(settings) as conn:
        row = conn.execute(
            "SELECT payload FROM hdrs WHERE hdr_id = ?", (hdr_id,)
        ).fetchone()
    assert row is not None
    import json as _json

    payload_decoded = _json.loads(row[0])
    cognitive_action = payload_decoded.get("cognitive_snapshot", {}).get("action", "")
    # System message and user prompt both in the action text
    assert "Você é um especialista em LGPD" in cognitive_action
    assert "Resuma o art. 7º da LGPD" in cognitive_action


# ── 8. Streaming: SSE forwarded + accumulated + HDR + metadata ────────────────


def _mock_anthropic_stream_lines():
    """Anthropic SSE format with named events."""
    return [
        'event: message_start',
        'data: {"type":"message_start","message":{"id":"msg_01","type":"message","role":"assistant","model":"claude-3-5-sonnet-20241022","content":[],"stop_reason":null}}',
        '',
        'event: content_block_start',
        'data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}',
        '',
        'event: content_block_delta',
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"O art. "}}',
        '',
        'event: content_block_delta',
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"7º "}}',
        '',
        'event: content_block_delta',
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"LGPD."}}',
        '',
        'event: content_block_stop',
        'data: {"type":"content_block_stop","index":0}',
        '',
        'event: message_delta',
        'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":15}}',
        '',
        'event: message_stop',
        'data: {"type":"message_stop"}',
        '',
    ]


class _FakeAsyncLineIterator:
    def __init__(self, lines):
        self._lines = list(lines)
        self._i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._i >= len(self._lines):
            raise StopAsyncIteration
        line = self._lines[self._i]
        self._i += 1
        return line


class _FakeStreamResponse:
    def __init__(self, status_code=200, lines=None, error_body=None):
        self.status_code = status_code
        self._lines = lines or []
        self._error_body = error_body or b""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def aiter_lines(self):
        return _FakeAsyncLineIterator(self._lines)

    async def aread(self):
        return self._error_body


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_anthropic_streaming_happy_path(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    fake_stream = _FakeStreamResponse(
        status_code=200, lines=_mock_anthropic_stream_lines()
    )
    instance = MockClient.return_value.__aenter__.return_value
    instance.stream = lambda *a, **kw: fake_stream

    payload = _valid_anthropic_payload()
    payload["stream"] = True
    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=payload,
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")

    text = r.text
    # Anthropic events forwarded verbatim
    assert "event: message_start" in text
    assert "event: content_block_delta" in text
    assert "event: message_stop" in text

    # Heillon metadata appended as SSE comments
    assert ": heillon-hdr-id=" in text
    assert ": heillon-quota-used=1" in text

    # Extract HDR id and verify response was accumulated from text_delta events
    hdr_id = None
    for line in text.splitlines():
        if line.startswith(": heillon-hdr-id="):
            hdr_id = line.split("=", 1)[1].strip()
            break
    assert hdr_id is not None and len(hdr_id) == 64

    from app.db.compat import open_connection

    with open_connection(settings) as conn:
        row = conn.execute(
            "SELECT payload FROM hdrs WHERE hdr_id = ?", (hdr_id,)
        ).fetchone()
    import json as _json

    cognitive = _json.loads(row[0])["cognitive_snapshot"]
    # All 3 fragments concatenated: "O art. " + "7º " + "LGPD."
    assert "O art." in cognitive["result"]
    assert "7º" in cognitive["result"]
    assert "LGPD" in cognitive["result"]


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_anthropic_streaming_upstream_error_in_sse(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    err_body = b'{"type":"error","error":{"type":"overloaded_error","message":"Service overloaded"}}'
    fake_stream = _FakeStreamResponse(status_code=529, error_body=err_body)
    instance = MockClient.return_value.__aenter__.return_value
    instance.stream = lambda *a, **kw: fake_stream

    payload = _valid_anthropic_payload()
    payload["stream"] = True
    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=payload,
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-ant-fake"},
    )
    assert r.status_code == 200  # SSE always returns 200; error inside the stream
    text = r.text
    assert "event: error" in text
    assert "overloaded" in text
    # No HDR created on upstream error
    assert ": heillon-hdr-id=" not in text


# ── 10. SSRF: localhost blocked on Anthropic endpoint ─────────────────────────


def test_anthropic_blocks_localhost_upstream():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/gateway/anthropic/v1/messages",
        json=_valid_anthropic_payload(),
        headers={
            "X-Heillon-Api-Key": key,
            "X-Upstream-Api-Key": "sk-ant-fake",
            "X-Heillon-Upstream-Url": "http://localhost:8080",
        },
    )
    assert r.status_code == 400
