"""Mission persistence and diary analytic queries."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.domain.mission.models import MissionPlan


class MissionRepository:
    """SQLite-backed dossier archival with diary exploration helpers."""

    def persist_plan(self, conn: sqlite3.Connection, plan: MissionPlan) -> None:
        """UPSERT mission dossier snapshot."""

        from app.db.database import persist_mission_plan

        persist_mission_plan(conn, plan)

    def fetch_plan(
        self,
        conn: sqlite3.Connection,
        mission_id: str,
        organization_id: str | None = None,
    ) -> MissionPlan | None:
        """Load mission by identifier enforcing optional tenant segregation."""

        from app.db.database import fetch_mission_plan

        dossier = fetch_mission_plan(conn, mission_id)
        if dossier is None:
            return None

        if organization_id is None:
            return dossier

        return dossier if dossier.organization_id == organization_id else None

    def list_plans(
        self,
        conn: sqlite3.Connection,
        skip: int,
        limit: int,
        organization_id: str | None = None,
    ) -> list[MissionPlan]:
        """Return paginated dossiers descending by creation."""

        from app.db.database import list_mission_plans

        return list_mission_plans(
            conn, skip=skip, limit=limit, organization_id=organization_id
        )

    def diary_query(
        self,
        conn: sqlite3.Connection,
        *,
        skip: int,
        limit: int,
        status_filter: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        search: str | None = None,
        organization_id: str | None = None,
    ) -> tuple[int, list[MissionPlan]]:
        """Return missions matching diary filters."""

        predicates: list[str] = []
        params: list[Any] = []

        if organization_id is not None:
            predicates.append("organization_id = ?")
            params.append(organization_id)

        if status_filter:
            predicates.append("status = ?")
            params.append(status_filter)

        if search:
            predicates.append("description LIKE ?")
            params.append(f"%{search}%")

        if date_from:
            predicates.append("datetime(created_at) >= datetime(?)")
            params.append(date_from)

        if date_to:
            predicates.append("datetime(created_at) <= datetime(?, '23:59:59')")
            params.append(date_to)

        where_sql = ""
        if predicates:
            where_sql = "WHERE " + " AND ".join(predicates)

        count_row = conn.execute(
            f"SELECT COUNT(*) AS c FROM missions {where_sql}", params
        ).fetchone()
        total = int(count_row["c"]) if count_row else 0

        pagination_params = [*params, limit, skip]

        snapshot_rows = conn.execute(
            f"""
            SELECT mission_plan_snapshot FROM missions
            {where_sql}
            ORDER BY datetime(created_at) DESC
            LIMIT ? OFFSET ?
            """,  # noqa: S608
            pagination_params,
        ).fetchall()

        hydrated = [
            MissionPlan.model_validate_json(r["mission_plan_snapshot"])
            for r in snapshot_rows
        ]
        return total, hydrated

    def aggregate_stats(
        self, conn: sqlite3.Connection, organization_id: str | None = None
    ) -> dict[str, Any]:
        """Return aggregate metrics for EASY diary dashboards."""

        from app.db.dialect_sql import aggregate_mission_stats

        return aggregate_mission_stats(conn, organization_id)
