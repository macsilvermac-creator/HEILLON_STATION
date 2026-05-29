"""F30 — Admin metrics endpoint tests."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

from fastapi.testclient import TestClient

ADMIN_TOKEN = "test-admin-token-with-enough-length-1234"


def _fresh_app():
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/admin_test.db"
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["FORCE_STUB_TIMESTAMP"] = "true"
    os.environ["HEILLON_ADMIN_TOKEN"] = ADMIN_TOKEN

    from app.core import config

    config._settings = None
    from app.core.config import get_settings
    from app.db.database import init_database
    from app.main import create_application

    settings = get_settings()
    init_database(settings)
    return TestClient(create_application()), settings


def _bootstrap_test_data(settings) -> None:
    """Create test users + HDRs to make metrics meaningful."""
    from app.db.compat import open_connection
    from app.domain.api_keys.services import ApiKeyService
    from app.domain.user.models import UserRole
    from app.domain.user.repository import UserRepository

    now_iso = datetime.now(timezone.utc).isoformat()
    with open_connection(settings) as conn:
        u1 = UserRepository.create_user(
            conn,
            email="u1@x.com",
            name="U1",
            hashed_password="x",
            role=UserRole.ADVOGADO,
            organization_id="org_default",
        )
        u2 = UserRepository.create_user(
            conn,
            email="u2@x.com",
            name="U2",
            hashed_password="x",
            role=UserRole.PERITO,
            organization_id="org_default",
        )
        ApiKeyService.mint(
            conn, organization_id="org_default", user_id=u1.user_id, name="k1"
        )
        ApiKeyService.mint(
            conn, organization_id="org_default", user_id=u2.user_id, name="k2"
        )
        # Insert 3 HDRs
        for i in range(3):
            conn.execute(
                """INSERT INTO hdrs (hdr_id, mission_id, previous_hdr, hdr_type,
                                      timestamp_iso, canonical_hash, payload,
                                      organization_id, created_at)
                   VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)""",
                (
                    f"adm_{i:03d}",
                    "mam",
                    "analysis",
                    now_iso,
                    "h" * 64,
                    "{}",
                    "org_default",
                    now_iso,
                ),
            )


def test_admin_requires_token():
    client, _ = _fresh_app()
    r = client.get("/api/v1/admin/beta-metrics")
    assert r.status_code == 401


def test_admin_rejects_bad_token():
    client, _ = _fresh_app()
    r = client.get(
        "/api/v1/admin/beta-metrics",
        headers={"X-Heillon-Admin-Token": "wrong-token"},
    )
    assert r.status_code == 401


def test_admin_returns_503_when_disabled():
    """When HEILLON_ADMIN_TOKEN is empty, endpoints return 503."""
    # Clear admin token
    os.environ["HEILLON_ADMIN_TOKEN"] = ""
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/admin_503.db"
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["ENVIRONMENT"] = "development"

    from app.core import config

    config._settings = None
    from app.core.config import get_settings
    from app.db.database import init_database
    from app.main import create_application

    settings = get_settings()
    init_database(settings)
    client = TestClient(create_application())

    r = client.get(
        "/api/v1/admin/beta-metrics",
        headers={"X-Heillon-Admin-Token": "anything"},
    )
    assert r.status_code == 503

    # Restore for other tests
    os.environ["HEILLON_ADMIN_TOKEN"] = ADMIN_TOKEN


def test_admin_beta_metrics_returns_snapshot():
    client, settings = _fresh_app()
    _bootstrap_test_data(settings)

    r = client.get(
        "/api/v1/admin/beta-metrics",
        headers={"X-Heillon-Admin-Token": ADMIN_TOKEN},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert "snapshot_at" in body
    assert body["organizations"]["total"] >= 1
    assert "free" in body["organizations"]["by_tier"]
    assert body["users"]["total"] >= 2
    assert body["api_keys"]["active"] >= 2
    assert body["api_keys"]["revoked"] == 0
    assert body["hdrs"]["total"] >= 3
    assert body["hdrs"]["last_24h"] >= 3
    assert "analysis" in body["hdrs"]["by_type"]
    assert body["hdrs"]["latest_at"] is not None


def test_admin_beta_feed_returns_events():
    client, settings = _fresh_app()
    _bootstrap_test_data(settings)

    r = client.get(
        "/api/v1/admin/beta-feed?limit=5",
        headers={"X-Heillon-Admin-Token": ADMIN_TOKEN},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 3
    assert isinstance(body["events"], list)
    # Each event has the sanitized fields (no prompt/response content)
    for ev in body["events"]:
        assert "hdr_id" in ev
        assert "created_at" in ev
        assert "hdr_type" in ev
        # NEVER expose payload/prompt
        assert "prompt" not in ev
        assert "response" not in ev
        assert "payload" not in ev


def test_admin_beta_feed_respects_limit():
    client, settings = _fresh_app()
    _bootstrap_test_data(settings)

    r = client.get(
        "/api/v1/admin/beta-feed?limit=2",
        headers={"X-Heillon-Admin-Token": ADMIN_TOKEN},
    )
    assert r.status_code == 200
    assert r.json()["count"] <= 2


def test_admin_beta_feed_clamps_limit():
    client, settings = _fresh_app()
    _bootstrap_test_data(settings)

    # limit > 100 should be clamped to 100; limit < 1 to 1
    r = client.get(
        "/api/v1/admin/beta-feed?limit=99999",
        headers={"X-Heillon-Admin-Token": ADMIN_TOKEN},
    )
    assert r.status_code == 200
    # Should not crash; returns whatever exists (bootstrap has 3)
    assert r.json()["count"] >= 3
