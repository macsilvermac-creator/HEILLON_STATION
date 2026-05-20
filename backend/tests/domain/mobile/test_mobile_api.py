"""Phase 8 mobile façade HTTP regressions."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.core.config import Settings
from app.main import create_application


def test_mobile_endpoints_require_bearer(api_client: TestClient) -> None:
    """Mobile routes use strict bearer like agent-config."""

    assert api_client.get("/api/v1/mobile/quick-stats").status_code == 403
    assert api_client.get("/api/v1/mobile/pending-approvals").status_code == 403


def test_mobile_quick_stats_and_push_token(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _scoped() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'mobile.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "ev_m",
            FORENSICS_PACKAGE_DIR=tmp_path / "fp_m",
            FORCE_STUB_TIMESTAMP=True,
        )

    monkeypatch.setattr(config, "get_settings", _scoped)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    cfg = _scoped()
    cfg.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    cfg.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    app = create_application()
    with TestClient(app) as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "mobile-suite@heillon.demo",
                "name": "Mobile Suite",
                "password": "long-enough-demo-password-phase8",
                "role": "perito",
                "organization_id": "org_demo_qa",
            },
        )
        assert reg.status_code == 200, reg.text
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        stats = client.get("/api/v1/mobile/quick-stats", headers=headers)
        assert stats.status_code == 200, stats.text
        body = stats.json()
        assert "pending_approvals" in body
        assert "total_missions" in body

        pend = client.get("/api/v1/mobile/pending-approvals", headers=headers)
        assert pend.status_code == 200, pend.text
        assert "missions" in pend.json()

        push = client.post(
            "/api/v1/mobile/push-token",
            headers=headers,
            json={"subscription_json": '{"bridge":"phase8-mvp","ok":true}'},
        )
        assert push.status_code == 200, push.text
        assert push.json()["stored"] is True
