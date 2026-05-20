"""SQLite connectivity, schema provisioning, and HDR persistence primitives."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable
from urllib.parse import unquote

from app.core import config as runtime_config
from app.core.config import Settings
from app.domain.hdr.models import HDR
from app.domain.mission.models import MissionPlan


def sqlite_file_path(database_url: str) -> Path:
    """Translate ``DATABASE_URL`` into on-disk SQLite path."""

    if not database_url.startswith("sqlite:///"):
        msg = "Only sqlite:/// URIs targeting local filesystem are supported."
        raise ValueError(msg)

    stripped = database_url.removeprefix("sqlite:///")
    return Path(unquote(stripped))


@contextmanager
def db_connection(database_url: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Yield SQLite connection guarded by courtroom-oriented pragmas."""

    cfg = runtime_config.get_settings()
    target_url = database_url or cfg.DATABASE_URL
    sqlite_path = sqlite_file_path(target_url)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(sqlite_path.as_posix(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")

    try:
        yield conn
    finally:
        conn.close()


def apply_migrations(conn: sqlite3.Connection, migrations_dir: Path) -> None:
    """Execute sequential ``*.sql`` migrations guarded by bookkeeping table."""

    if not migrations_dir.exists():
        return

    migrations_dir.mkdir(parents=True, exist_ok=True)

    conn.execute(
        """CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )

    completed = {
        row[0] for row in conn.execute("SELECT filename FROM migration_history ORDER BY filename")
    }

    for sql_path in sorted(migrations_dir.glob("*.sql")):
        if sql_path.name in completed:
            continue

        ddl = sql_path.read_text(encoding="utf-8")
        with conn:
            conn.executescript(ddl)
            conn.execute(
                "INSERT INTO migration_history (filename) VALUES (?)",
                (sql_path.name,),
            )


def init_database(settings: Settings | None = None) -> None:
    """Bootstrap storage directory and DDL scripts."""

    settings = settings or runtime_config.get_settings()

    migrations_path = Path(__file__).resolve().parent / "migrations"

    with db_connection(settings.DATABASE_URL) as conn:
        apply_migrations(conn, migrations_path)
        conn.commit()


def insert_hdr(conn: sqlite3.Connection, hdr: HDR, *, organization_id: str | None = None) -> None:
    """Insert immutable HDR enforcing primary key collisions."""

    tenant = organization_id or "org_default"

    payload = hdr.model_dump_json()

    conn.execute(
        """INSERT INTO hdrs (
                   hdr_id, mission_id, previous_hdr,
                   hdr_type, timestamp_iso, canonical_hash,
                   payload,
                   organization_id
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            hdr.hdr_id,
            hdr.mission_id,
            hdr.previous_hdr,
            hdr.hdr_type,
            hdr.timestamp,
            hdr.canonical_hash,
            payload,
            tenant,
        ),
    )


def fetch_hdr(conn: sqlite3.Connection, hdr_id: str) -> HDR | None:
    """Retrieve HDR by cryptographic identifier."""

    cursor = conn.execute(
        "SELECT payload FROM hdrs WHERE hdr_id = ?",
        (hdr_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    return HDR.model_validate_json(row["payload"])  # type: ignore[arg-type]


def fetch_hdr_organization_id(conn: sqlite3.Connection, hdr_id: str) -> str | None:
    """Resolve tenant column for multi-tenant custody validation."""

    cursor = conn.execute(
        "SELECT organization_id FROM hdrs WHERE hdr_id = ?",
        (hdr_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return str(row["organization_id"])


def fetch_mission_chain(conn: sqlite3.Connection, mission_id: str) -> list[HDR]:
    """Enumerate HDR artefacts for adjudication timelines."""

    cursor = conn.execute(
        "SELECT payload FROM hdrs WHERE mission_id = ? ORDER BY rowid ASC",
        (mission_id,),
    )
    results: Iterable[sqlite3.Row] = cursor.fetchall()
    decoded: list[HDR] = [HDR.model_validate_json(row["payload"]) for row in results]
    return decoded


def persist_mission_plan(conn: sqlite3.Connection, plan: MissionPlan) -> None:
    """Persist immutable mission dossiers keyed by EASY identifier."""

    snapshot = plan.model_dump(mode="json")
    mission_plan_snapshot = json.dumps(snapshot, separators=(",", ":"), sort_keys=False)
    dag_json = json.dumps(plan.dag.model_dump(mode="json"), separators=(",", ":"))
    authorized_json = json.dumps(plan.authorized_agent_ids)
    hdrs_generated_json = json.dumps(plan.hdrs_generated)
    normative_json = (
        json.dumps(plan.normative_result.model_dump(mode="json"), separators=(",", ":"))
        if plan.normative_result
        else None
    )

    conn.execute(
        """INSERT OR REPLACE INTO missions (
                mission_id,
                description,
                authorized_agents_json,
                dag_json,
                normative_json,
                status,
                estimated_cost_gas,
                created_at,
                approved_at,
                executed_at,
                completed_at,
                hdrs_generated_json,
                mission_plan_snapshot,
                organization_id
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
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
        ),
    )


def fetch_mission_plan(conn: sqlite3.Connection, mission_id: str) -> MissionPlan | None:
    """Hydrate EASY mission dossier from archival snapshot."""

    cursor = conn.execute(
        "SELECT mission_plan_snapshot FROM missions WHERE mission_id = ?",
        (mission_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    return MissionPlan.model_validate_json(row["mission_plan_snapshot"])  # type: ignore[arg-type]


def list_mission_plans(conn: sqlite3.Connection, skip: int, limit: int, organization_id: str | None = None) -> list[MissionPlan]:
    """Return paginated EASY missions ordered chronologically descending."""

    if organization_id is None:
        cursor = conn.execute(
            """
            SELECT mission_plan_snapshot FROM missions
            ORDER BY datetime(created_at) DESC
            LIMIT ? OFFSET ?
            """,
            (limit, skip),
        )
    else:
        cursor = conn.execute(
            """
            SELECT mission_plan_snapshot FROM missions
            WHERE organization_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT ? OFFSET ?
            """,
            (organization_id, limit, skip),
        )

    return [
        MissionPlan.model_validate_json(r["mission_plan_snapshot"]) for r in cursor.fetchall()
    ]  # type: ignore[arg-type]
