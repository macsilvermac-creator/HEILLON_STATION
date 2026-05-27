"""F31 — Gateway tests with mocked upstream provider."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient


def _fresh_app():
    """Isolated DB + app + TestClient."""
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/gw_test.db"
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
            email=f"gw-{datetime.now().timestamp()}@x.com",
            name="GW User",
            hashed_password="x",
            role=UserRole.ADVOGADO,
            organization_id="org_default",
        )
        minted = ApiKeyService.mint(
            conn,
            organization_id="org_default",
            user_id=user.user_id,
            name="GW key",
        )
    return minted.plaintext_key


def _mock_openai_success_response():
    """Standard OpenAI Chat Completions success response."""
    return {
        "id": "chatcmpl-test-123",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "O art. 7º da LGPD elenca as bases legais para tratamento de dados pessoais.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 20, "completion_tokens": 18, "total_tokens": 38},
    }


def _valid_chat_payload() -> dict:
    return {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Você é um assistente jurídico."},
            {"role": "user", "content": "Resuma o art. 7º da LGPD."},
        ],
        "temperature": 0.2,
    }


# ── 1. Missing X-Heillon-Api-Key → 401 ─────────────────────────────────────────


def test_gateway_requires_heillon_api_key():
    client, _ = _fresh_app()
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={"X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 401


# ── 2. Missing X-Upstream-Api-Key → 400 ────────────────────────────────────────


def test_gateway_requires_upstream_api_key():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={"X-Heillon-Api-Key": key},
    )
    assert r.status_code == 400
    assert "X-Upstream-Api-Key" in r.json()["detail"]


# ── 3. Streaming: forwards SSE + accumulates + creates HDR + emits metadata ──


def _mock_streaming_sse_lines():
    """Standard OpenAI streaming SSE chunks (3 deltas + finish + [DONE])."""
    return [
        'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1700000000,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"role":"assistant","content":"O "},"finish_reason":null}]}',
        "",
        'data: {"id":"chatcmpl-1","choices":[{"index":0,"delta":{"content":"art. "},"finish_reason":null}]}',
        "",
        'data: {"id":"chatcmpl-1","choices":[{"index":0,"delta":{"content":"7º LGPD."},"finish_reason":null}]}',
        "",
        'data: {"id":"chatcmpl-1","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}',
        "",
        "data: [DONE]",
        "",
    ]


class _FakeAsyncLineIterator:
    """httpx response.aiter_lines() async iterator stand-in."""

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
    """httpx.AsyncClient.stream() context-manager stand-in."""

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
def test_gateway_streaming_happy_path(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    fake_stream = _FakeStreamResponse(status_code=200, lines=_mock_streaming_sse_lines())
    instance = MockClient.return_value.__aenter__.return_value
    instance.stream = lambda *a, **kw: fake_stream

    payload = _valid_chat_payload()
    payload["stream"] = True
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=payload,
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers.get("x-accel-buffering") == "no"

    text = r.text
    assert "data: {" in text
    assert "data: [DONE]" in text
    assert ": heillon-hdr-id=" in text
    assert ": heillon-quota-used=1" in text
    assert ": heillon-quota-tier=free" in text

    hdr_id = None
    for line in text.splitlines():
        if line.startswith(": heillon-hdr-id="):
            hdr_id = line.split("=", 1)[1].strip()
            break
    assert hdr_id is not None and len(hdr_id) == 64

    from app.db.compat import open_connection

    with open_connection(settings) as conn:
        row = conn.execute(
            "SELECT hdr_type, payload FROM hdrs WHERE hdr_id = ?", (hdr_id,)
        ).fetchone()
    assert row is not None
    assert row[0] == "analysis"
    import json as _json

    payload_decoded = _json.loads(row[1])
    cognitive = payload_decoded.get("cognitive_snapshot", {})
    assert "O " in cognitive["result"]
    assert "art." in cognitive["result"]
    assert "7º LGPD" in cognitive["result"]


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_gateway_streaming_upstream_error_surfaces_in_sse(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    err_body = b'{"error":{"message":"Invalid model","type":"invalid_request_error"}}'
    fake_stream = _FakeStreamResponse(status_code=400, error_body=err_body)
    instance = MockClient.return_value.__aenter__.return_value
    instance.stream = lambda *a, **kw: fake_stream

    payload = _valid_chat_payload()
    payload["stream"] = True
    payload["model"] = "gpt-fake-9000"
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=payload,
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    # Streaming returns 200 to client; upstream error surfaces inside the SSE
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    text = r.text
    assert "Invalid model" in text
    assert "data: [DONE]" in text
    # No HDR created on upstream error
    assert ": heillon-hdr-id=" not in text


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_gateway_streaming_respects_quota_402(MockClient):
    """When quota is exceeded, streaming returns 402 BEFORE any upstream call."""
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
                    f"qpad_{i:03d}", "mq", "analysis", now_iso,
                    "h" * 64, "{}", "org_default", now_iso,
                ),
            )

    instance = MockClient.return_value.__aenter__.return_value
    instance.stream = MagicMock()

    payload = _valid_chat_payload()
    payload["stream"] = True
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=payload,
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 402
    assert r.json()["detail"]["error"] == "quota_exceeded"
    # Upstream stream must NOT have been called
    instance.stream.assert_not_called()


# ── 4. Happy path: forwards + creates HDR + returns headers ───────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_gateway_happy_path_forwards_and_audits(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    # Mock upstream OpenAI response
    mock_resp = httpx.Response(200, json=_mock_openai_success_response())
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock(return_value=mock_resp)

    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["choices"][0]["message"]["content"].startswith("O art. 7º")

    # Heillon-specific headers present
    assert "X-Heillon-Hdr-Id" in r.headers
    assert len(r.headers["X-Heillon-Hdr-Id"]) == 64  # SHA-256
    assert r.headers["X-Heillon-Quota-Used"] == "1"
    assert r.headers["X-Heillon-Quota-Tier"] == "free"

    # Confirm forward was actually called with bearer auth
    call_args = instance.post.call_args
    assert call_args[0][0].endswith("/v1/chat/completions")
    assert call_args.kwargs["headers"]["Authorization"] == "Bearer sk-fake"


# ── 5. Upstream error proxied verbatim ─────────────────────────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_gateway_proxies_upstream_errors(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    # Upstream returns 429 rate limit
    err_body = {"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}}
    mock_resp = httpx.Response(429, json=err_body)
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock(return_value=mock_resp)

    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 429
    assert r.json()["error"]["message"] == "Rate limit exceeded"


# ── 6. SSRF: localhost in upstream URL rejected ────────────────────────────────


def test_gateway_blocks_localhost_upstream():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={
            "X-Heillon-Api-Key": key,
            "X-Upstream-Api-Key": "sk-fake",
            "X-Heillon-Upstream-Url": "http://localhost:8000",
        },
    )
    assert r.status_code == 400
    assert "SSRF" in r.json()["detail"] or "not allowed" in r.json()["detail"]


# ── 7. SSRF: AWS metadata IP rejected ──────────────────────────────────────────


def test_gateway_blocks_aws_metadata_upstream():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={
            "X-Heillon-Api-Key": key,
            "X-Upstream-Api-Key": "sk-fake",
            "X-Heillon-Upstream-Url": "http://169.254.169.254",
        },
    )
    assert r.status_code == 400


# ── 8. Quota exceeded → 402 (without burning upstream call) ────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_gateway_quota_exceeded_returns_402(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)

    # Pre-fill quota with raw inserts (free=50)
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
                    f"pad_{i:03d}", "mp", "analysis", now_iso,
                    "h" * 64, "{}", "org_default", now_iso,
                ),
            )

    # Mock should NOT be called (quota check is first)
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock()

    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 402
    assert r.json()["detail"]["error"] == "quota_exceeded"
    # CRITICAL: upstream MUST NOT be called when quota exceeded (no $ burned)
    instance.post.assert_not_called()


# ── 9. Custom upstream URL (Together AI) accepted ──────────────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_gateway_accepts_custom_upstream_url(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    mock_resp = httpx.Response(200, json=_mock_openai_success_response())
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock(return_value=mock_resp)

    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={
            "X-Heillon-Api-Key": key,
            "X-Upstream-Api-Key": "tok-fake",
            "X-Heillon-Upstream-Url": "https://api.together.xyz",
            "X-Heillon-Upstream-Provider": "other",
        },
    )
    assert r.status_code == 200
    # Confirm called the Together endpoint
    assert instance.post.call_args[0][0].startswith("https://api.together.xyz")


# ── 10. Missing model rejected (Pydantic validation) ──────────────────────────


def test_gateway_rejects_missing_model():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},  # no model
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 422


# ── 11. Empty messages rejected ────────────────────────────────────────────────


def test_gateway_rejects_empty_messages():
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json={"model": "gpt-4o-mini", "messages": []},
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 422


# ── 12. HDR persisted contains the prompt + response hashes ────────────────────


@patch("app.domain.gateway.services.httpx.AsyncClient")
def test_gateway_hdr_contains_correct_hashes(MockClient):
    client, settings = _fresh_app()
    key = _bootstrap_user_and_key(settings)
    mock_resp = httpx.Response(200, json=_mock_openai_success_response())
    instance = MockClient.return_value.__aenter__.return_value
    instance.post = AsyncMock(return_value=mock_resp)

    r = client.post(
        "/api/v1/gateway/v1/chat/completions",
        json=_valid_chat_payload(),
        headers={"X-Heillon-Api-Key": key, "X-Upstream-Api-Key": "sk-fake"},
    )
    assert r.status_code == 200
    hdr_id = r.headers["X-Heillon-Hdr-Id"]

    # Fetch the HDR and confirm it has proper hash format + analysis type
    from app.db.compat import open_connection

    with open_connection(settings) as conn:
        row = conn.execute(
            "SELECT hdr_type, canonical_hash, mission_id FROM hdrs WHERE hdr_id = ?",
            (hdr_id,),
        ).fetchone()
    assert row is not None
    assert row[0] == "analysis"
    assert len(row[1]) == 64  # canonical_hash SHA-256
    assert row[2].startswith("ext_")  # mission ID generated via build_capture_hdr
