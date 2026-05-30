"""Persistence for the admin metrics bounded context.

All aggregates use ALIASED columns and NAMED row access so they work on both
sqlite3.Row and psycopg2 RealDictCursor. Positional access (``row[1]``) raises
on RealDictCursor (dict rows have no integer keys), which is why the previous
inline router code was silently broken on Postgres.
"""

from __future__ import annotations

from typing import Any


def _val(row: Any, key: str) -> Any:
    """Read a column by name from sqlite3.Row or RealDictCursor dict row."""
    if row is None:
        return None
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


class AdminMetricsRepository:
    """Read-only aggregate queries for operator dashboards."""

    def organizations_by_tier(self, conn: Any) -> dict[str, int]:
        rows = conn.execute(
            "SELECT tier, COUNT(*) AS cnt FROM organizations "
            "GROUP BY tier ORDER BY tier"
        ).fetchall()
        return {str(_val(r, "tier")): int(_val(r, "cnt") or 0) for r in rows}

    def count_users(self, conn: Any) -> int:
        return self._scalar(conn, "SELECT COUNT(*) AS cnt FROM users")

    def count_active_users_since(self, conn: Any, since_iso: str) -> int:
        return self._scalar(
            conn,
            """SELECT COUNT(DISTINCT u.user_id) AS cnt
                 FROM users u
                 JOIN api_keys k ON k.user_id = u.user_id
                WHERE k.last_used_at >= ?""",
            (since_iso,),
        )

    def count_api_keys(self, conn: Any) -> tuple[int, int]:
        """Return (total, active)."""
        total = self._scalar(conn, "SELECT COUNT(*) AS cnt FROM api_keys")
        active = self._scalar(
            conn, "SELECT COUNT(*) AS cnt FROM api_keys WHERE revoked_at IS NULL"
        )
        return total, active

    def count_hdrs(self, conn: Any) -> int:
        return self._scalar(conn, "SELECT COUNT(*) AS cnt FROM hdrs")

    def count_hdrs_since(self, conn: Any, since_iso: str) -> int:
        return self._scalar(
            conn,
            "SELECT COUNT(*) AS cnt FROM hdrs WHERE created_at >= ?",
            (since_iso,),
        )

    def hdrs_by_type(self, conn: Any) -> dict[str, int]:
        rows = conn.execute(
            "SELECT hdr_type, COUNT(*) AS cnt FROM hdrs "
            "GROUP BY hdr_type ORDER BY hdr_type"
        ).fetchall()
        return {str(_val(r, "hdr_type")): int(_val(r, "cnt") or 0) for r in rows}

    def latest_hdr_at(self, conn: Any) -> str | None:
        row = conn.execute(
            "SELECT created_at FROM hdrs ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        value = _val(row, "created_at")
        return str(value) if value is not None else None

    def recent_hdrs(self, conn: Any, *, limit: int) -> list[dict[str, str]]:
        rows = conn.execute(
            """SELECT hdr_id, created_at, mission_id, hdr_type, organization_id
                 FROM hdrs
                ORDER BY created_at DESC
                LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {
                "hdr_id": str(_val(r, "hdr_id")),
                "created_at": str(_val(r, "created_at")),
                "mission_id": str(_val(r, "mission_id")),
                "hdr_type": str(_val(r, "hdr_type")),
                "organization_id": str(_val(r, "organization_id")),
            }
            for r in rows
        ]

    # ── private ────────────────────────────────────────────────────────────
    def _scalar(self, conn: Any, sql: str, params: tuple[Any, ...] = ()) -> int:
        row = conn.execute(sql, params).fetchone()
        return int(_val(row, "cnt") or 0)
