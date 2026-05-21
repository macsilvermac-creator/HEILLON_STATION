"""Agent cognition sovereignty endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.core.config import Settings
from app.main import create_application


def _scoped_settings(tmp_path) -> Settings:
    return Settings(
        DATABASE_URL=f"sqlite:///{(tmp_path / 'agent_cfg_http.db').as_posix()}",
        EVIDENCE_DIR=tmp_path / "vault_ac",
        FORENSICS_PACKAGE_DIR=tmp_path / "for_ac",
        FORCE_STUB_TIMESTAMP=True,
    )


def test_agent_config_crud_requires_bearer(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    cfg = _scoped_settings(tmp_path)
    cfg.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    cfg.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "get_settings", lambda: cfg)

    app = create_application()
    with TestClient(app) as client:
        r = client.get("/api/v1/agent-config/analysis-agent")
        assert r.status_code == 401  # bearer ou cookie obrigatório


def test_agent_config_stub_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    cfg = _scoped_settings(tmp_path)
    cfg.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    cfg.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "get_settings", lambda: cfg)

    app = create_application()
    with TestClient(app) as tc:
        reg = tc.post(
            "/api/v1/auth/register",
            json={
                "email": "sovereignty@court.demo",
                "name": "Soberania Tester",
                "password": "notasecret-but-long-pass",
                "role": "admin",
                "organization_id": "org_sovereignty",
            },
        )
        assert reg.status_code == 200
        token = reg.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        upsert = tc.put(
            "/api/v1/agent-config/analysis-agent",
            headers=headers,
            json={
                "source": "stub",
                "model_name": "fixture-stub",
            },
        )
        assert upsert.status_code == 200, upsert.text
        assert upsert.json()["agent_id"] == "analysis-agent"
        assert upsert.json()["source"] == "stub"

        listed = tc.get("/api/v1/agent-config/", headers=headers)
        assert listed.status_code == 200
        rows = listed.json()
        assert any(entry["agent_id"] == "analysis-agent" for entry in rows)

        probe = tc.post("/api/v1/agent-config/analysis-agent/test", headers=headers)
        assert probe.status_code == 200
        assert probe.json()["status"] == "ok"
