"""JWT registration / login regressions."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.core.config import Settings
from app.main import create_application


def test_register_login_and_me_roundtrip(tmp_path, monkeypatch: pytest.MonkeyPatch):
    def _scoped() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'auth.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "vault",
            FORENSICS_PACKAGE_DIR=tmp_path / "for",
            FORCE_STUB_TIMESTAMP=True,
        )

    monkeypatch.setattr(config, "get_settings", _scoped)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    scoped = _scoped()
    scoped.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    scoped.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    app = create_application()
    with TestClient(app) as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "perito@heillon.demo",
                "name": "Perito QA",
                "password": "notasecret-but-long",
                "role": "perito",
                "organization_id": "org_demo_qa",
            },
        )
        assert reg.status_code == 200, reg.text
        token = reg.json()["access_token"]

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "perito@heillon.demo", "password": "notasecret-but-long"},
        )
        assert login.status_code == 200

        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        payload = me.json()
        assert payload["email"] == "perito@heillon.demo"
        assert payload["organization_id"] == "org_demo_qa"


def test_missions_require_bearer_when_flag_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    auth_db = tmp_path / "auth_dossier.db"

    def enforced() -> Settings:
        cfg = Settings(
            DATABASE_URL=f"sqlite:///{auth_db.as_posix()}",
            EVIDENCE_DIR=tmp_path / "vault_auth",
            FORENSICS_PACKAGE_DIR=tmp_path / "for_auth",
            FORCE_STUB_TIMESTAMP=True,
            MISSION_ROUTES_REQUIRE_AUTH=True,
            DEFAULT_ORGANIZATION_ID="org_demo_qa",
        )
        cfg.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        cfg.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
        return cfg

    monkeypatch.setattr(config, "get_settings", enforced)

    app = create_application()
    with TestClient(app) as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "operator@court.demo",
                "name": "Operador EASY",
                "password": "notasecret-but-long",
                "role": "perito",
                "organization_id": "org_demo_qa",
            },
        )
        assert reg.status_code == 200
        token = reg.json()["access_token"]

        client.cookies.clear()

        guarded = client.post(
            "/api/v1/mission/plan",
            json={"description": "OCR and analyze dossier attachments", "authorized_agents": ["ocr-agent"]},
        )
        assert guarded.status_code == 401

        ok = client.post(
            "/api/v1/mission/plan",
            json={"description": "OCR and analyze dossier attachments", "authorized_agents": ["ocr-agent"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ok.status_code == 200, ok.text


def test_register_conflict_duplicate_email(tmp_path, monkeypatch: pytest.MonkeyPatch):
    def _scoped() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'dup.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "v",
            FORENSICS_PACKAGE_DIR=tmp_path / "f",
            FORCE_STUB_TIMESTAMP=True,
        )

    monkeypatch.setattr(config, "get_settings", _scoped)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    s = _scoped()
    s.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    s.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    app = create_application()
    body = {
        "email": "dup@test.pt",
        "name": "A",
        "password": "pwd-one-two-three",
        "role": "advogado",
    }
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/register", json=body).status_code == 200
        second = client.post("/api/v1/auth/register", json={**body, "name": "B"})
        assert second.status_code == 409


def test_login_unknown_email_returns_401(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    def _scoped() -> Settings:
        cfg = Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'login.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "v2",
            FORENSICS_PACKAGE_DIR=tmp_path / "f2",
            FORCE_STUB_TIMESTAMP=True,
        )
        cfg.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        cfg.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
        return cfg

    monkeypatch.setattr(config, "get_settings", _scoped)
    app = create_application()
    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", json={"email": "x@test.pt", "password": "nope"})
        assert r.status_code == 401


def test_me_requires_bearer(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    def _scoped() -> Settings:
        cfg = Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'me.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "v3",
            FORENSICS_PACKAGE_DIR=tmp_path / "f3",
            FORCE_STUB_TIMESTAMP=True,
        )
        cfg.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        cfg.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
        return cfg

    monkeypatch.setattr(config, "get_settings", _scoped)
    app = create_application()
    with TestClient(app) as client:
        assert client.get("/api/v1/auth/me").status_code == 401
