"""Persistence helpers for courtroom forensic dossiers."""

from __future__ import annotations

import json
import sqlite3

from app.domain.forensic.models import AuditManifest, ForensicPackage


class ForensicRepository:
    """Stores immutable forensic artefacts within SQLite bookkeeping rows."""

    def insert_completed_package(
        self,
        conn: sqlite3.Connection,
        *,
        package: ForensicPackage,
        pdf_path: str,
        json_path: str,
        verification_url_snapshot: str,
        generated_by: str,
        integrity_hash: str,
        pdf_checksum: str,
        json_chain_checksum: str,
        manifest: AuditManifest,
        signature_path: str | None = None,
    ) -> None:
        """Record a hardened forensic dossier keyed by cryptographic package identifiers."""

        payload = manifest.model_dump(mode="json")
        manifest_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        conn.execute(
            """INSERT OR REPLACE INTO forensic_packages (
                       package_id, mission_id, status, manifest_json, integrity_hash,
                       pdf_path, json_chain_path, pdf_checksum, json_chain_checksum,
                       created_at, generated_by, verification_url_snapshot,
                       signature_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                package.package_id,
                package.mission_id,
                package.status.value,
                manifest_json,
                integrity_hash,
                pdf_path,
                json_path,
                pdf_checksum,
                json_chain_checksum,
                package.created_at.isoformat(),
                generated_by,
                verification_url_snapshot,
                signature_path,
            ),
        )

    def fetch_row(
        self, conn: sqlite3.Connection, package_id: str
    ) -> dict[str, str] | None:
        """Return raw bookkeeping row keyed by forensic package identifier."""

        row = conn.execute(
            "SELECT * FROM forensic_packages WHERE package_id = ?",
            (package_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
