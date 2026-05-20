"""Constitutional anchoring + LGPD rule smoke tests."""

from __future__ import annotations

import sqlite3

import pytest

from app.core import config as app_config
from app.domain.hdr.models import (
    HDRAgent,
    HDRCognitiveSnapshot,
    HDRExecution,
    HDRIntent,
    HDRNormative,
    HDRUser,
)
from app.domain.hdr.services import HDRService
from app.domain.normative.lgpd_br import LGPD_FRAMEWORK
from app.domain.normative.anchoring_service import NormativeAnchoringService
from app.domain.normative.services import NormativeService


def test_anchor_hdr_to_lgpd(tmp_path, monkeypatch: pytest.MonkeyPatch):
    def _scoped():
        db = tmp_path / "anc.db"
        vault = tmp_path / "vault"
        out = tmp_path / "fp"
        return app_config.Settings(
            DATABASE_URL=f"sqlite:///{db.as_posix()}",
            EVIDENCE_DIR=vault,
            FORENSICS_PACKAGE_DIR=out,
            FORCE_STUB_TIMESTAMP=True,
            ENVIRONMENT="development",
            MISSION_ROUTES_REQUIRE_AUTH=False,
        )

    monkeypatch.setattr(app_config, "get_settings", _scoped)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    scoped = _scoped()
    scoped.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    scoped.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    from app.db.database import init_database

    init_database(scoped)

    path = tmp_path / "anc.db"
    conn = sqlite3.connect(path.as_posix(), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    svc = HDRService()
    hdr = svc.generate_hdr(
        hdr_type="ingestion",
        mission_id="m1",
        agent=HDRAgent(id="ingest", model="stub", version="test"),
        user=HDRUser(id="operator"),
        intent=HDRIntent(description="ingestion artefact", tools_required=[], estimated_cost_gas=0.0),
        execution=HDRExecution(status="completed", input_hash="c" * 64, output_hash="d" * 64),
        cognitive_snapshot=HDRCognitiveSnapshot(hypothesis="", action="ingest", result="stored"),
        normative=HDRNormative(checked=True, violations=[], corpus_version="v1"),
    )

    from app.domain.hdr.repository import HDRRepository

    repo = HDRRepository()
    repo.insert(conn, hdr, organization_id="org_a")
    conn.commit()

    anchoring = NormativeAnchoringService()
    anchoring.register_framework(LGPD_FRAMEWORK)
    record = anchoring.anchor_hdr(conn, hdr.hdr_id, ["LGPD-BR"])
    assert record.hdr_id == hdr.hdr_id
    assert record.anchors[0].framework_id == "LGPD-BR"
    conn.close()


def test_framework_list_contains_lgpd(api_client):
    frameworks = api_client.get("/api/v1/compliance/frameworks")
    assert frameworks.status_code == 200
    ids = {f["framework_id"] for f in frameworks.json()}
    assert "LGPD-BR" in ids


def test_lgpd_rule_blocks_sensitive_without_consent(normative_service: NormativeService):
    verdict = normative_service.check_intent(
        "Processar dados sensíveis para triagem médica urgente.",
        {},
    )
    assert not verdict.allowed


def test_lgpd_rules_warn_on_minimization(normative_service: NormativeService):
    verdict = normative_service.check_intent(
        "Arquivo de cadastro trivial.",
        {"necessary_fields": 3, "input_field_count": 99},
    )
    lgpd_warnings = [w for w in verdict.warnings if w.rule_id == "LGPD-003"]
    assert lgpd_warnings
