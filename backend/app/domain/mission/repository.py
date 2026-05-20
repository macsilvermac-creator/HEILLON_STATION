"""Mission persistence and diary analytic queries."""

from __future__ import annotations

import json
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

        return list_mission_plans(conn, skip=skip, limit=limit, organization_id=organization_id)

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

        count_row = conn.execute(f"SELECT COUNT(*) AS c FROM missions {where_sql}", params).fetchone()
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

        hydrated = [MissionPlan.model_validate_json(r["mission_plan_snapshot"]) for r in snapshot_rows]
        return total, hydrated

    def aggregate_stats(self, conn: sqlite3.Connection, organization_id: str | None = None) -> dict[str, Any]:
        """Return aggregate metrics for EASY diary dashboards."""

        if organization_id is None:
            total_missions = int(conn.execute("SELECT COUNT(*) AS c FROM missions").fetchone()["c"])
            completed = int(
                conn.execute("SELECT COUNT(*) AS c FROM missions WHERE status = 'completed'").fetchone()["c"]
            )
            failed = int(
                conn.execute(
                    "SELECT COUNT(*) AS c FROM missions WHERE status IN ('failed', 'aborted')",
                ).fetchone()["c"],
            )

            blocked_by_normative = int(
                conn.execute(
                    """SELECT COUNT(*) AS c FROM missions
                         WHERE normative_json IS NOT NULL
                           AND CAST(json_extract(normative_json, '$.allowed') AS INTEGER) = 0"""
                ).fetchone()["c"],
            )

            hdrs_sql = (
                """SELECT SUM(COALESCE(json_array_length(hdrs_generated_json), 0)) AS s FROM missions"""
            )
            hdr_row = conn.execute(hdrs_sql).fetchone()
            total_hdrs = int(hdr_row["s"] or 0)

            duration_sql = """
                SELECT AVG(
                    (
                        CAST(strftime('%s', completed_at) AS REAL) -
                        CAST(strftime('%s', executed_at) AS REAL)
                    )
                ) * 1000.0 AS ms
                FROM missions
                WHERE executed_at IS NOT NULL AND completed_at IS NOT NULL
                  AND datetime(completed_at) >= datetime(executed_at)
            """
            ms_row = conn.execute(duration_sql).fetchone()
            avg_execution_time_ms = float(ms_row["ms"]) if ms_row and ms_row["ms"] is not None else 0.0

            dag_rows = conn.execute("SELECT dag_json FROM missions").fetchall()
        else:
            oid_bind = organization_id

            total_missions = int(
                conn.execute("SELECT COUNT(*) AS c FROM missions WHERE organization_id = ?", (oid_bind,)).fetchone()[
                    "c"
                ],
            )

            completed = int(
                conn.execute(
                    "SELECT COUNT(*) AS c FROM missions WHERE organization_id = ? AND status = 'completed'",
                    (oid_bind,),
                ).fetchone()["c"],
            )

            failed = int(
                conn.execute(
                    """SELECT COUNT(*) AS c FROM missions
                           WHERE organization_id = ?
                             AND status IN ('failed','aborted')""",
                    (oid_bind,),
                ).fetchone()["c"],
            )

            blocked_by_normative = int(
                conn.execute(
                    """SELECT COUNT(*) AS c FROM missions
                         WHERE organization_id = ?
                           AND normative_json IS NOT NULL
                           AND CAST(json_extract(normative_json, '$.allowed') AS INTEGER) = 0
                    """,
                    (oid_bind,),
                ).fetchone()["c"],
            )

            hdr_row = conn.execute(
                """SELECT SUM(COALESCE(json_array_length(hdrs_generated_json), 0)) AS s
                       FROM missions WHERE organization_id = ?""",
                (oid_bind,),
            ).fetchone()
            total_hdrs = int(hdr_row["s"] or 0)

            duration_sql = """
                SELECT AVG(
                    (
                        CAST(strftime('%s', completed_at) AS REAL) -
                        CAST(strftime('%s', executed_at) AS REAL)
                    )
                ) * 1000.0 AS ms
                FROM missions
                WHERE organization_id = ?
                  AND executed_at IS NOT NULL AND completed_at IS NOT NULL
                  AND datetime(completed_at) >= datetime(executed_at)
            """
            ms_row = conn.execute(duration_sql, (oid_bind,)).fetchone()
            avg_execution_time_ms = float(ms_row["ms"]) if ms_row and ms_row["ms"] is not None else 0.0

            dag_rows = conn.execute(
                "SELECT dag_json FROM missions WHERE organization_id = ?",
                (oid_bind,),
            ).fetchall()

        agent_histogram: dict[str, int] = {}
        for row in dag_rows:
            try:
                dag_payload = json.loads(row["dag_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            for node in dag_payload.get("nodes", []):
                aid = node.get("agent_id")
                if isinstance(aid, str) and aid:
                    agent_histogram[aid] = agent_histogram.get(aid, 0) + 1

        sorted_agents = sorted(agent_histogram.items(), key=lambda item: (-item[1], item[0]))
        formatted_agents = [{"agent_id": k, "count": v} for k, v in sorted_agents[:10]]

        return {
            "total_missions": total_missions,
            "completed": completed,
            "failed": failed,
            "blocked_by_normative": blocked_by_normative,
            "total_hdrs_generated": total_hdrs,
            "avg_execution_time_ms": avg_execution_time_ms,
            "most_used_agents": formatted_agents,
        }
