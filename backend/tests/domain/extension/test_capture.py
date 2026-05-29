"""F28 — Browser Extension capture endpoint tests (via TestClient)."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

from fastapi.testclient import TestClient


def _fresh_app():
    """Create an isolated DB + FastAPI app + TestClient."""
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/ext_test.db"
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


def _bootstrap_user_and_key(settings) -> tuple[str, str]:
    """Create a test user + API key. Returns (user_id, plaintext_api_key)."""
    from app.db.compat import open_connection
    from app.domain.api_keys.services import ApiKeyService
    from app.domain.user.models import UserRole
    from app.domain.user.repository import UserRepository

    with open_connection(settings) as conn:
        user = UserRepository.create_user(
            conn,
            email=f"ext-{datetime.now().timestamp()}@x.com",
            name="Ext User",
            hashed_password="x",
            role=UserRole.ADVOGADO,
            organization_id="org_default",
        )
        minted = ApiKeyService.mint(
            conn,
            organization_id="org_default",
            user_id=user.user_id,
            name="Test extension",
        )
    return user.user_id, minted.plaintext_key


def _valid_payload(**overrides) -> dict:
    base = {
        "provider": "openai",
        "model": "gpt-4o",
        "prompt": "Resuma o art. 7º da LGPD para defesa em juízo.",
        "response": "O art. 7º da LGPD dispõe que o tratamento só pode ser realizado nas hipóteses do rol legal...",
        "source_url": "https://chat.openai.com/c/abc-123",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "ai_session_id": "sess_abc",
        "extension_version": "0.1.0",
        "page_title": "ChatGPT — LGPD",
    }
    base.update(overrides)
    return base


# ── 1. /extension/health requires auth ─────────────────────────────────────────


def test_health_requires_api_key():
    client, _ = _fresh_app()
    r = client.get("/api/v1/extension/health")
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "ApiKey"


# ── 2. /extension/health works with valid key ──────────────────────────────────


def test_health_returns_quota():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    r = client.get(
        "/api/v1/extension/health",
        headers={"X-Heillon-Api-Key": key},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["tier"] == "free"
    assert body["quota"]["used"] == 0
    assert body["quota"]["limit"] == 50
    assert body["quota"]["remaining"] == 50
    assert body["organization_id"] == "org_default"


# ── 3. /extension/health rejects bad key ───────────────────────────────────────


def test_health_rejects_invalid_key():
    client, _ = _fresh_app()
    r = client.get(
        "/api/v1/extension/health",
        headers={"X-Heillon-Api-Key": "heillon_live_FAKEFAKEFAKEFAKE"},
    )
    assert r.status_code == 401


# ── 4. /extension/health rejects revoked key ───────────────────────────────────


def test_health_rejects_revoked_key():
    client, settings = _fresh_app()
    user_id, key = _bootstrap_user_and_key(settings)
    from app.db.compat import open_connection
    from app.domain.api_keys.services import ApiKeyService

    with open_connection(settings) as conn:
        rec = ApiKeyService.find_active_by_plaintext(conn, key)
        ApiKeyService.revoke(
            conn, api_key_id=rec.api_key_id, organization_id="org_default"
        )

    r = client.get("/api/v1/extension/health", headers={"X-Heillon-Api-Key": key})
    assert r.status_code == 401


# ── 5. /extension/capture creates an HDR ───────────────────────────────────────


def test_capture_creates_hdr():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/extension/capture",
        headers={"X-Heillon-Api-Key": key},
        json=_valid_payload(),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "captured"
    assert len(body["hdr_id"]) == 64  # SHA-256 hex
    assert body["mission_id"].startswith("ext_openai_")
    assert body["quota"]["used"] == 1
    assert body["quota"]["remaining"] == 49
    assert "/verification/" in body["verification_url"]


# ── 6. Same session_id => same mission_id (chaining) ───────────────────────────


def test_capture_same_session_chains_to_same_mission():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    h = {"X-Heillon-Api-Key": key}
    r1 = client.post(
        "/api/v1/extension/capture",
        headers=h,
        json=_valid_payload(ai_session_id="sess_xyz"),
    )
    r2 = client.post(
        "/api/v1/extension/capture",
        headers=h,
        json=_valid_payload(
            ai_session_id="sess_xyz",
            prompt="Continuação da conversa.",
            response="Detalhamento adicional.",
        ),
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["mission_id"] == r2.json()["mission_id"]
    assert r1.json()["hdr_id"] != r2.json()["hdr_id"]


# ── 7. Different session_id => different mission_id ───────────────────────────


def test_capture_different_session_creates_separate_missions():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    h = {"X-Heillon-Api-Key": key}
    r1 = client.post(
        "/api/v1/extension/capture",
        headers=h,
        json=_valid_payload(ai_session_id="sess_a"),
    )
    r2 = client.post(
        "/api/v1/extension/capture",
        headers=h,
        json=_valid_payload(ai_session_id="sess_b"),
    )
    assert r1.json()["mission_id"] != r2.json()["mission_id"]


# ── 8. Quota exceeded returns 402 ──────────────────────────────────────────────


def test_capture_returns_402_when_quota_exceeded():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    h = {"X-Heillon-Api-Key": key}

    # Fill quota with raw inserts (faster than 50 capture calls)
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
                    f"pad_{i:03d}",
                    "mp",
                    "analysis",
                    now_iso,
                    "h" * 64,
                    "{}",
                    "org_default",
                    now_iso,
                ),
            )

    r = client.post("/api/v1/extension/capture", headers=h, json=_valid_payload())
    assert r.status_code == 402
    detail = r.json()["detail"]
    assert detail["error"] == "quota_exceeded"
    assert detail["tier"] == "free"
    assert detail["used"] == 50
    assert detail["limit"] == 50


# ── 9. Oversize prompt rejected with 422 ───────────────────────────────────────


def test_capture_rejects_oversize_prompt():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/extension/capture",
        headers={"X-Heillon-Api-Key": key},
        json=_valid_payload(prompt="x" * 70_000),  # exceeds MAX_PROMPT_CHARS (64k)
    )
    assert r.status_code == 422


# ── 10. Missing required field rejected with 422 ───────────────────────────────


def test_capture_rejects_missing_response():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    payload = _valid_payload()
    del payload["response"]
    r = client.post(
        "/api/v1/extension/capture",
        headers={"X-Heillon-Api-Key": key},
        json=payload,
    )
    assert r.status_code == 422


# ── 11. Invalid provider rejected ──────────────────────────────────────────────


def test_capture_rejects_unknown_provider():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    r = client.post(
        "/api/v1/extension/capture",
        headers={"X-Heillon-Api-Key": key},
        json=_valid_payload(provider="invalid_corp"),
    )
    assert r.status_code == 422


# ── 12. last_used_at is updated after successful auth ──────────────────────────


def test_last_used_at_updates_on_auth():
    client, settings = _fresh_app()
    _, key = _bootstrap_user_and_key(settings)
    from app.db.compat import open_connection
    from app.domain.api_keys.services import ApiKeyService

    # Touch via /health
    client.get("/api/v1/extension/health", headers={"X-Heillon-Api-Key": key})

    with open_connection(settings) as conn:
        rec = ApiKeyService.find_active_by_plaintext(conn, key)
        assert rec.last_used_at is not None
