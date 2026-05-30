"""Fase 32 — Beta feedback survey endpoint tests."""

from __future__ import annotations

import os
import tempfile

from fastapi.testclient import TestClient

ADMIN_TOKEN = "test-admin-token-with-enough-length-feedback-1"


def _fresh_app():
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/feedback_test.db"
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


def _register_and_login(client: TestClient) -> None:
    """Register an operator and ensure the session cookie is set."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "fb@x.com",
            "name": "Feedback Tester",
            "password": "supersecret123",
        },
    )
    client.post(
        "/api/v1/auth/login",
        json={"email": "fb@x.com", "password": "supersecret123"},
    )


def test_feedback_requires_auth():
    client, _ = _fresh_app()
    with client:
        r = client.post("/api/v1/feedback", json={"usability": 8})
    assert r.status_code == 401


def test_feedback_submit_and_summary():
    client, _ = _fresh_app()
    with client:
        _register_and_login(client)

        r = client.post(
            "/api/v1/feedback",
            json={
                "usability": 9,
                "experience": 8,
                "functionality": 7,
                "delivers": 10,
                "nps": 9,
                "adopt": "now",
                "most_valuable": "Cadeia de custódia que vale em juízo.",
                "frictions": "Setup da extensão poderia ser mais simples.",
                "improvements": "Integração nativa com mais provedores.",
                "contact_ok": True,
            },
        )
        assert r.status_code == 201, r.text
        ack = r.json()
        assert ack["id"].startswith("fb_")
        assert "created_at" in ack

        # Summary requires admin token
        r_noauth = client.get("/api/v1/feedback/summary")
        assert r_noauth.status_code == 401

        r2 = client.get(
            "/api/v1/feedback/summary",
            headers={"X-Heillon-Admin-Token": ADMIN_TOKEN},
        )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["response_count"] == 1
    assert body["averages"]["usability"] == 9.0
    assert body["averages"]["delivers"] == 10.0
    assert body["nps"]["promoters"] == 1
    assert body["nps"]["score"] == 100.0
    assert body["adopt_breakdown"].get("now") == 1
    assert body["contact_optins"] == 1
    # De-identified comments — never carry user/org identity
    assert len(body["recent_comments"]) == 1
    comment = body["recent_comments"][0]
    assert "user_id" not in comment
    assert "organization_id" not in comment
    assert comment["most_valuable"].startswith("Cadeia de custódia")


def test_feedback_rejects_out_of_range_score():
    client, _ = _fresh_app()
    with client:
        _register_and_login(client)
        r = client.post("/api/v1/feedback", json={"usability": 42})
    assert r.status_code == 422


def test_feedback_partial_submission_allowed():
    client, _ = _fresh_app()
    with client:
        _register_and_login(client)
        # Only NPS, nothing else — should still record
        r = client.post("/api/v1/feedback", json={"nps": 3})
        assert r.status_code == 201

        r2 = client.get(
            "/api/v1/feedback/summary",
            headers={"X-Heillon-Admin-Token": ADMIN_TOKEN},
        )
    body = r2.json()
    assert body["nps"]["detractors"] == 1
    assert body["nps"]["score"] == -100.0
