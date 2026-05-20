"""Tests HDR minting primitives."""

from __future__ import annotations

import pytest


def test_generate_hdr(hdr_service_fixture, sample_agent_stack):
    svc = hdr_service_fixture
    hdr = svc.generate_hdr(
        hdr_type="analysis",
        mission_id="fixture_mission",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )

    assert hdr.hdr_id == hdr.canonical_hash
    assert svc.verify_single_hdr(hdr)


def test_chain_hdr_success(hdr_service_fixture, sample_agent_stack):
    svc = hdr_service_fixture
    first = svc.generate_hdr(
        hdr_type="ocr",
        mission_id="fixture_mission",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )

    second = svc.generate_hdr(
        hdr_type="analysis",
        mission_id="fixture_mission",
        previous_hdr=first.hdr_id,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )

    chained = svc.chain_hdr(first, second)
    assert chained is second


def test_chain_hdr_raises_on_gap(hdr_service_fixture, sample_agent_stack):
    svc = hdr_service_fixture
    first = svc.generate_hdr(
        hdr_type="ocr",
        mission_id="fixture_mission",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )

    orphan = svc.generate_hdr(
        hdr_type="analysis",
        mission_id="fixture_mission",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )

    with pytest.raises(ValueError):
        svc.chain_hdr(first, orphan)


def test_verify_chain_valid(hdr_service_fixture, sample_agent_stack):
    svc = hdr_service_fixture
    first = svc.generate_hdr(
        hdr_type="ocr",
        mission_id="fixture_mission",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )
    second = svc.generate_hdr(
        hdr_type="analysis",
        mission_id="fixture_mission",
        previous_hdr=first.hdr_id,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )

    report = svc.verify_chain([second, first])  # intentionally unsorted ingress
    assert report.valid


def test_verify_chain_broken(hdr_service_fixture, sample_agent_stack):
    svc = hdr_service_fixture
    first = svc.generate_hdr(
        hdr_type="ocr",
        mission_id="fixture_mission",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )
    tampered_payload = first.model_dump()
    tampered_payload["intent"]["description"] = "tampered"
    from app.domain.hdr.models import HDR

    tampered = HDR(**tampered_payload)

    report = svc.verify_chain([first, tampered])
    assert not report.valid


def test_init_database_writes_core_tables(monkeypatch, tmp_path):
    """Regression: ephemeral settings must hydrate the full SQLite DDL graph."""

    import sqlite3

    from app.core import config
    from app.core.config import Settings
    from app.db.database import init_database

    monkeypatch.delenv("DATABASE_URL", raising=False)

    def _cfg() -> Settings:
        base = Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'ddl_smoke.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "e",
            FORENSICS_PACKAGE_DIR=tmp_path / "p",
            FORCE_STUB_TIMESTAMP=True,
        )
        base.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        base.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
        return base

    monkeypatch.setattr(config, "get_settings", _cfg)
    init_database()

    sqlite_path = (tmp_path / "ddl_smoke.db").resolve().as_posix()
    conn = sqlite3.connect(sqlite_path)
    try:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()

    assert {"missions", "hdrs", "organizations", "users", "migration_history"} <= names


def test_init_database_runs_twice_without_corruption(monkeypatch, tmp_path):
    from app.core import config
    from app.core.config import Settings
    from app.db.database import init_database

    monkeypatch.delenv("DATABASE_URL", raising=False)

    def _cfg() -> Settings:
        base = Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'ddl_twice.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "e2",
            FORENSICS_PACKAGE_DIR=tmp_path / "p2",
            FORCE_STUB_TIMESTAMP=True,
        )
        base.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        base.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
        return base

    monkeypatch.setattr(config, "get_settings", _cfg)
    cfg = _cfg()
    init_database(cfg)
    init_database(cfg)
