"""Forensic dossier generation unit coverage."""

from __future__ import annotations

import sqlite3

import pytest

from app.domain.forensic.models import ForensicPackageStatus
from app.domain.forensic.services import ForensicPackageService


@pytest.fixture()
def forensic_conn(api_client):
    """Mutable SQLite mirror of the ephemeral TestClient datastore."""

    path = api_client.app.state.sqlite_path
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def test_generate_package(forensic_conn, completed_mission):
    """Completed missions hydrate deterministic forensic bundles."""

    service = ForensicPackageService()
    package = service.generate_package(
        forensic_conn,
        completed_mission.mission_id,
        generated_by="perito_001",
    )

    assert package.status == ForensicPackageStatus.COMPLETED
    assert package.manifest is not None
    assert package.manifest.chain_root
    assert package.manifest.chain_tail
    forensic_conn.commit()


def test_package_integrity_hash_stable(forensic_conn, completed_mission):
    """Regenerating a dossier from the immutable HDR lineage keeps integrity tokens."""

    service = ForensicPackageService()

    primary = service.generate_package(
        forensic_conn,
        completed_mission.mission_id,
        generated_by="perito_001",
    )
    primary_hash = primary.manifest.integrity_hash if primary.manifest else None
    forensic_conn.commit()

    secondary = service.generate_package(
        forensic_conn,
        completed_mission.mission_id,
        generated_by="perito_001",
    )
    assert primary.manifest
    assert secondary.manifest
    assert primary_hash == secondary.manifest.integrity_hash


def test_manifest_verification_url(forensic_conn, completed_mission):
    """Court disclosure manifests embed public EASY verification gateways."""

    service = ForensicPackageService()
    package = service.generate_package(
        forensic_conn,
        completed_mission.mission_id,
        generated_by="perito_001",
    )
    assert package.manifest
    assert "/verify/" in package.manifest.verification_url
