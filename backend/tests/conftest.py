"""Pytest fixtures for Heillon Legal backend."""

from __future__ import annotations

import os

os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

from collections.abc import Generator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core import config


@pytest.fixture(autouse=False)
def test_settings(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[config.Settings, None, None]:
    """Provision isolated SQLite + deterministic custody directories."""

    def _override() -> config.Settings:
        return config.Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'custody.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "evidence_vault",
            FORENSICS_PACKAGE_DIR=tmp_path / "forensics_out",
            FORCE_STUB_TIMESTAMP=True,
            FORENSICS_USE_STUB_PDF=True,
            MISSION_ROUTES_REQUIRE_AUTH=False,
            ENVIRONMENT="development",
        )

    monkeypatch.setattr(config, "get_settings", _override)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    cfg = _override()
    cfg.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    cfg.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    yield cfg


@pytest.fixture()
def api_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[TestClient, None, None]:
    """HTTPX-backed ASGI exercising lifecycles deterministically."""

    def _override() -> config.Settings:
        return config.Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'custody.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "evidence_vault",
            FORENSICS_PACKAGE_DIR=tmp_path / "forensics_out",
            FORCE_STUB_TIMESTAMP=True,
            FORENSICS_USE_STUB_PDF=True,
            MISSION_ROUTES_REQUIRE_AUTH=False,
            ENVIRONMENT="development",
        )

    monkeypatch.setattr(config, "get_settings", _override)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Import after monkeypatch avoids premature cache of settings proxies.
    from app.main import create_application

    app = create_application()
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def auth_headers(api_client):
    """Bearer headers for an operator on the ephemeral custody database."""

    reg = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "fixture_ingest@heillon.demo",
            "name": "Fixture Ingest",
            "password": "long-password-for-fixture-ingest-999",
            "role": "perito",
            "organization_id": "org_fixture_ingest",
        },
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def hdr_service_fixture(test_settings):  # noqa: ARG001
    """HDRService anchored to ephemeral settings partitions."""

    _ = test_settings

    from app.domain.hdr.services import HDRService

    return HDRService()


@pytest.fixture()
def sample_agent_stack():
    """Return reusable fixture payload for cryptographic minting."""

    from app.domain.hdr.models import (
        HDRAgent,
        HDRCognitiveSnapshot,
        HDRExecution,
        HDRIntent,
        HDRNormative,
        HDRUser,
    )

    return {
        "agent": HDRAgent(id="fixture_agent", model="stub", version="test"),
        "user": HDRUser(id="fixture_user"),
        "intent": HDRIntent(description="fixture", tools_required=[], estimated_cost_gas=0.0),
        "execution": HDRExecution(status="completed", input_hash="a" * 64, output_hash="b" * 64, duration_ms=1),
        "cognitive_snapshot": HDRCognitiveSnapshot(hypothesis="h", action="a", result="r"),
        "normative": HDRNormative(checked=True, violations=[], corpus_version="test"),
    }


@pytest.fixture()
def normative_service():
    """Standalone Corpus Normativo aligned with courthouse defaults."""

    from app.domain.normative.services import DEFAULT_LEGAL_RULES, NormativeService

    return NormativeService(rules=list(DEFAULT_LEGAL_RULES))


@pytest.fixture()
def orchestration_engine(test_settings, normative_service):  # noqa: ARG001
    """Synthetic EASY engine with deterministic stub cognition."""

    from app.domain.hdr.services import HDRService
    from app.domain.mission.agent_registry_setup import build_agent_registry
    from app.domain.mission.services import OrchestrationEngine

    hdr = HDRService()
    registry = build_agent_registry()
    return OrchestrationEngine(normative_service, hdr, registry)


@pytest.fixture()
def completed_mission(api_client):
    """Finished EASY mission yielding HDR artefacts suitable for forensic export."""

    plan_resp = api_client.post(
        "/api/v1/mission/plan",
        json={
            "description": "OCR and analyze documents",
            "authorized_agents": ["ocr-agent", "analysis-agent"],
        },
    )
    assert plan_resp.status_code == 200
    mission_id = plan_resp.json()["mission_id"]
    assert api_client.post(f"/api/v1/mission/{mission_id}/approve").status_code == 200
    exec_resp = api_client.post(f"/api/v1/mission/{mission_id}/execute")
    assert exec_resp.status_code == 200
    return SimpleNamespace(mission_id=mission_id)


@pytest.fixture()
def seeded_missions_diary(api_client, completed_mission):  # noqa: ARG001
    """Populate missions table with permissive workflows plus corpus blockages."""

    blocked = api_client.post(
        "/api/v1/mission/plan",
        json={
            "description": "Access privileged attorney-client documents",
            "authorized_agents": ["analysis-agent"],
        },
    )
    assert blocked.status_code == 200
    payload = blocked.json()
    assert payload["normative_result"]["allowed"] is False

    return True
