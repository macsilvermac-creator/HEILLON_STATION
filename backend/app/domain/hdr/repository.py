"""HDR persistence façade decoupled from SQLite row layout."""

from __future__ import annotations

import sqlite3

from app.domain.hdr.models import HDR


class HDRRepository:
    """Append-only HDR store delegating to the shared SQLite connection."""

    def insert(self, conn: sqlite3.Connection, hdr: HDR, *, organization_id: str | None = None) -> None:
        """Persist a complete HDR artefact."""

        from app.db.database import insert_hdr

        insert_hdr(conn, hdr, organization_id=organization_id)

    def fetch_hdr(self, conn: sqlite3.Connection, hdr_id: str) -> HDR | None:
        """Load a solitary HDR fingerprint."""

        from app.db.database import fetch_hdr as _fetch_hdr

        return _fetch_hdr(conn, hdr_id)

    def fetch_hdr_organization_id(self, conn: sqlite3.Connection, hdr_id: str) -> str | None:
        """Resolve organization row for tenant-scoped chain validation."""

        from app.db.database import fetch_hdr_organization_id as _org_for_hdr

        return _org_for_hdr(conn, hdr_id)

    def fetch_mission_chain(self, conn: sqlite3.Connection, mission_id: str) -> list[HDR]:
        """Return chronological custody for ``mission_id``."""

        from app.db.database import fetch_mission_chain as _fetch_mission_chain

        return _fetch_mission_chain(conn, mission_id)

    def hdr_ids_for_mission(self, conn: sqlite3.Connection, mission_id: str) -> list[str]:
        """Return HDR ids in insertion order."""

        rows = conn.execute(
            "SELECT hdr_id FROM hdrs WHERE mission_id = ? ORDER BY rowid ASC",
            (mission_id,),
        )
        return [str(r["hdr_id"]) for r in rows.fetchall()]
