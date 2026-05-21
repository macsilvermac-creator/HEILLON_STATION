"""SQL helpers that diverge between SQLite (dev) and PostgreSQL (produção)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.db.compat import CompatConnection


def _dialect(conn: Any) -> str:
    return getattr(conn, "dialect", "sqlite")


def mission_chain_order_clause(conn: Any) -> str:
    if _dialect(conn) == "postgresql":
        return "ORDER BY timestamp_iso ASC"
    return "ORDER BY rowid ASC"


def mission_list_order_clause(conn: Any) -> str:
    if _dialect(conn) == "postgresql":
        return "ORDER BY created_at DESC"
    return "ORDER BY datetime(created_at) DESC"


def persist_mission_plan(conn: Any, plan, *, json_module) -> None:
    """Persist mission dossier (upsert) for either dialect."""

    snapshot = plan.model_dump(mode="json")
    mission_plan_snapshot = json_module.dumps(snapshot, separators=(",", ":"), sort_keys=False)
    dag_json = json_module.dumps(plan.dag.model_dump(mode="json"), separators=(",", ":"))
    authorized_json = json_module.dumps(plan.authorized_agent_ids)
    hdrs_generated_json = json_module.dumps(plan.hdrs_generated)
    normative_json = (
        json_module.dumps(plan.normative_result.model_dump(mode="json"), separators=(",", ":"))
        if plan.normative_result
        else None
    )

    params = (
        plan.mission_id,
        plan.description,
        authorized_json,
        dag_json,
        normative_json,
        plan.status.value,
        float(plan.estimated_cost_gas),
        plan.created_at.isoformat(),
        plan.approved_at.isoformat() if plan.approved_at else None,
        plan.executed_at.isoformat() if plan.executed_at else None,
        plan.completed_at.isoformat() if plan.completed_at else None,
        hdrs_generated_json,
        mission_plan_snapshot,
        plan.organization_id,
    )

    if _dialect(conn) == "postgresql":
        conn.execute(
            """INSERT INTO missions (
                    mission_id, description, authorized_agents_json, dag_json,
                    normative_json, status, estimated_cost_gas, created_at,
                    approved_at, executed_at, completed_at, hdrs_generated_json,
                    mission_plan_snapshot, organization_id
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (mission_id) DO UPDATE SET
                    description = EXCLUDED.description,
                    authorized_agents_json = EXCLUDED.authorized_agents_json,
                    dag_json = EXCLUDED.dag_json,
                    normative_json = EXCLUDED.normative_json,
                    status = EXCLUDED.status,
                    estimated_cost_gas = EXCLUDED.estimated_cost_gas,
                    created_at = EXCLUDED.created_at,
                    approved_at = EXCLUDED.approved_at,
                    executed_at = EXCLUDED.executed_at,
                    completed_at = EXCLUDED.completed_at,
                    hdrs_generated_json = EXCLUDED.hdrs_generated_json,
                    mission_plan_snapshot = EXCLUDED.mission_plan_snapshot,
                    organization_id = EXCLUDED.organization_id
            """,
            params,
        )
        return

    conn.execute(
        """INSERT OR REPLACE INTO missions (
                mission_id, description, authorized_agents_json, dag_json,
                normative_json, status, estimated_cost_gas, created_at,
                approved_at, executed_at, completed_at, hdrs_generated_json,
                mission_plan_snapshot, organization_id
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        params,
    )


def aggregate_mission_stats(conn: CompatConnection, organization_id: str | None = None) -> dict[str, Any]:
    """Dashboard aggregates with dialect-specific JSON/time helpers."""

    import json

    dialect = _dialect(conn)

    if dialect == "postgresql":
        norm_blocked_sql = """normative_json IS NOT NULL
            AND COALESCE((normative_json->>'allowed')::boolean, false) = false"""
        hdrs_sum_sql = "SUM(COALESCE(jsonb_array_length(hdrs_generated_json), 0))"
        duration_base = """
            SELECT AVG(
                EXTRACT(EPOCH FROM (completed_at - executed_at)) * 1000.0
            ) AS ms
            FROM missions
            WHERE executed_at IS NOT NULL AND completed_at IS NOT NULL
              AND completed_at >= executed_at
        """
        duration_org = """
            SELECT AVG(
                EXTRACT(EPOCH FROM (completed_at - executed_at)) * 1000.0
            ) AS ms
            FROM missions
            WHERE organization_id = ?
              AND executed_at IS NOT NULL AND completed_at IS NOT NULL
              AND completed_at >= executed_at
        """
    else:
        norm_blocked_sql = """normative_json IS NOT NULL
            AND CAST(json_extract(normative_json, '$.allowed') AS INTEGER) = 0"""
        hdrs_sum_sql = "SUM(COALESCE(json_array_length(hdrs_generated_json), 0))"
        duration_base = """
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
        duration_org = """
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
            conn.execute(f"SELECT COUNT(*) AS c FROM missions WHERE {norm_blocked_sql}").fetchone()["c"],
        )
        hdr_row = conn.execute(f"SELECT {hdrs_sum_sql} AS s FROM missions").fetchone()
        total_hdrs = int(hdr_row["s"] or 0)
        ms_row = conn.execute(duration_base).fetchone()
        dag_rows = conn.execute("SELECT dag_json FROM missions").fetchall()
    else:
        oid_bind = organization_id
        total_missions = int(
            conn.execute("SELECT COUNT(*) AS c FROM missions WHERE organization_id = ?", (oid_bind,)).fetchone()["c"],
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
                f"""SELECT COUNT(*) AS c FROM missions
                         WHERE organization_id = ?
                           AND {norm_blocked_sql}""",
                (oid_bind,),
            ).fetchone()["c"],
        )
        hdr_row = conn.execute(
            f"SELECT {hdrs_sum_sql} AS s FROM missions WHERE organization_id = ?",
            (oid_bind,),
        ).fetchone()
        total_hdrs = int(hdr_row["s"] or 0)
        ms_row = conn.execute(duration_org, (oid_bind,)).fetchone()
        dag_rows = conn.execute(
            "SELECT dag_json FROM missions WHERE organization_id = ?",
            (oid_bind,),
        ).fetchall()

    avg_execution_time_ms = float(ms_row["ms"]) if ms_row and ms_row["ms"] is not None else 0.0

    agent_histogram: dict[str, int] = {}
    for row in dag_rows:
        raw = row["dag_json"]
        if dialect == "postgresql" and not isinstance(raw, str):
            try:
                dag_payload = raw if isinstance(raw, dict) else json.loads(json.dumps(raw))
            except (TypeError, ValueError):
                continue
        else:
            try:
                dag_payload = json.loads(raw) if isinstance(raw, str) else raw
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
