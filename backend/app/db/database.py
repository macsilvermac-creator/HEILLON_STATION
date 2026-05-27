"""Database connectivity, schema provisioning, and HDR persistence primitives."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator, Iterable
from urllib.parse import unquote

from app.core import config as runtime_config
from app.core.config import Settings
from app.db.compat import CompatConnection, open_connection, resolve_dialect
from app.db.tenant_security import apply_rls_if_enabled
from app.db.dialect_sql import (
    mission_chain_order_clause,
    mission_list_order_clause,
    persist_mission_plan as upsert_mission_plan,
)
from app.domain.hdr.models import HDR
from app.domain.mission.models import MissionPlan

if TYPE_CHECKING:
    pass

POSTGRES_BOOTSTRAP_FILENAME = "20260521120000_heillon_legal_schema.sql"


def sqlite_file_path(database_url: str) -> Path:
    """Translate ``DATABASE_URL`` into on-disk SQLite path."""

    if not database_url.startswith("sqlite:///"):
        msg = "Only sqlite:/// URIs targeting local filesystem are supported."
        raise ValueError(msg)

    stripped = database_url.removeprefix("sqlite:///")
    return Path(unquote(stripped))


def _repo_root() -> Path:
    """Repo root (``backend/`` parent) where ``supabase/migrations`` lives."""

    backend_dir = Path(__file__).resolve().parents[2]
    return backend_dir.parent


def _postgres_bootstrap_path() -> Path:
    return _repo_root() / "supabase" / "migrations" / POSTGRES_BOOTSTRAP_FILENAME


@contextmanager
def db_connection(database_url: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Yield raw SQLite connection (legacy init paths)."""

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


def apply_migrations(conn: Any, migrations_dir: Path) -> None:
    """Execute sequential ``*.sql`` migrations guarded by bookkeeping table."""

    if not migrations_dir.exists():
        return

    migrations_dir.mkdir(parents=True, exist_ok=True)
    dialect = getattr(conn, "dialect", "sqlite")

    if dialect == "postgresql":
        conn.execute(
            """CREATE TABLE IF NOT EXISTS migration_history (
                    id BIGSERIAL PRIMARY KEY,
                    filename TEXT NOT NULL UNIQUE,
                    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )"""
        )
    else:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS migration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL UNIQUE,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )

    completed = {row["filename"] for row in conn.execute("SELECT filename FROM migration_history ORDER BY filename")}

    for sql_path in sorted(migrations_dir.glob("*.sql")):
        if sql_path.name in completed:
            continue

        ddl = sql_path.read_text(encoding="utf-8")
        conn.executescript(ddl)
        conn.execute("INSERT INTO migration_history (filename) VALUES (?)", (sql_path.name,))


def apply_postgres_bootstrap(conn: CompatConnection) -> None:
    """Apply consolidated Supabase schema when not yet recorded."""

    bootstrap = _postgres_bootstrap_path()
    if not bootstrap.is_file():
        msg = f"PostgreSQL bootstrap missing: {bootstrap}"
        raise FileNotFoundError(msg)

    try:
        row = conn.execute(
            "SELECT 1 FROM migration_history WHERE filename = ?",
            (POSTGRES_BOOTSTRAP_FILENAME,),
        ).fetchone()
        if row is not None:
            return
    except Exception:
        pass

    ddl = bootstrap.read_text(encoding="utf-8")
    conn.executescript(ddl)
    conn.execute(
        "INSERT INTO migration_history (filename) VALUES (?)",
        (POSTGRES_BOOTSTRAP_FILENAME,),
    )


def init_database(settings: Settings | None = None) -> None:
    """Bootstrap storage directory, DDL scripts, and normative corpus seed."""

    settings = settings or runtime_config.get_settings()
    migrations_path = Path(__file__).resolve().parent / "migrations"

    if resolve_dialect(settings) == "postgresql":
        with open_connection(settings) as conn:
            apply_postgres_bootstrap(conn)
            apply_rls_if_enabled(conn, enabled=settings.ENABLE_POSTGRES_RLS)
            _seed_corpus_if_needed(conn)
        return

    with db_connection(settings.DATABASE_URL) as conn:
        apply_migrations(conn, migrations_path)
        _seed_corpus_if_needed(conn)
        conn.commit()


def _seed_corpus_if_needed(conn: Any) -> None:
    """Seed normative corpus rules into FTS5 if the table is empty or outdated.

    Safe to call on every startup — the seed function uses upsert semantics
    so existing rules are updated in-place without duplicates.
    """
    try:
        from app.domain.normative.corpus_seed import CORPUS_VERSION, seed_normative_corpus

        # Check if corpus_meta table exists and version matches
        try:
            row = conn.execute(
                "SELECT value FROM corpus_meta WHERE key = 'version'"
            ).fetchone()
            if row is not None and row[0] == CORPUS_VERSION:
                return  # Already seeded with this version
        except Exception:
            pass  # Table doesn't exist yet — proceed with seed

        count = seed_normative_corpus(conn)

        # Persist version marker (best-effort — table may not exist in older DBs)
        try:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS corpus_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            conn.execute(
                """INSERT INTO corpus_meta (key, value) VALUES ('version', ?)
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                   updated_at = CURRENT_TIMESTAMP""",
                (CORPUS_VERSION,),
            )
        except Exception:
            pass  # Non-fatal if corpus_meta table can't be created

        import logging
        logging.getLogger("heillon.legal").info(
            "Normative corpus seeded: %d rules (v%s)", count, CORPUS_VERSION
        )
    except Exception as exc:
        import logging
        logging.getLogger("heillon.legal").warning(
            "Corpus seed skipped (non-fatal): %s", exc
        )


def insert_hdr(conn: Any, hdr: HDR, *, organization_id: str | None = None) -> None:
    """Insert immutable HDR enforcing primary key collisions.

    `created_at` is set server-side (UTC ISO-8601) for quota counting and
    retention purge. Distinct from `timestamp_iso` (HDR's own client-set ts).
    """

    from datetime import datetime, timezone

    tenant = organization_id or "org_default"
    payload = hdr.model_dump_json()
    server_created_at = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """INSERT INTO hdrs (
                   hdr_id, mission_id, previous_hdr,
                   hdr_type, timestamp_iso, canonical_hash,
                   payload, organization_id, created_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            server_created_at,
        ),
    )


def fetch_hdr(conn: Any, hdr_id: str) -> HDR | None:
    """Retrieve HDR by cryptographic identifier."""

    cursor = conn.execute("SELECT payload FROM hdrs WHERE hdr_id = ?", (hdr_id,))
    row = cursor.fetchone()
    if row is None:
        return None

    raw = row["payload"]
    if isinstance(raw, (dict, list)):
        return HDR.model_validate(raw)
    return HDR.model_validate_json(raw)  # type: ignore[arg-type]


def fetch_hdr_organization_id(conn: Any, hdr_id: str) -> str | None:
    """Resolve tenant column for multi-tenant custody validation."""

    cursor = conn.execute("SELECT organization_id FROM hdrs WHERE hdr_id = ?", (hdr_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return str(row["organization_id"])


def fetch_mission_chain(conn: Any, mission_id: str) -> list[HDR]:
    """Enumerate HDR artefacts for adjudication timelines."""

    order = mission_chain_order_clause(conn)
    cursor = conn.execute(
        f"SELECT payload FROM hdrs WHERE mission_id = ? {order}",
        (mission_id,),
    )
    results: Iterable[Any] = cursor.fetchall()
    decoded: list[HDR] = []
    for row in results:
        raw = row["payload"]
        if isinstance(raw, (dict, list)):
            decoded.append(HDR.model_validate(raw))
        else:
            decoded.append(HDR.model_validate_json(raw))
    return decoded


def persist_mission_plan(conn: Any, plan: MissionPlan) -> None:
    """Persist immutable mission dossiers keyed by EASY identifier."""

    upsert_mission_plan(conn, plan, json_module=json)


def fetch_mission_plan(conn: Any, mission_id: str) -> MissionPlan | None:
    """Hydrate EASY mission dossier from archival snapshot."""

    cursor = conn.execute(
        "SELECT mission_plan_snapshot FROM missions WHERE mission_id = ?",
        (mission_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    raw = row["mission_plan_snapshot"]
    if isinstance(raw, (dict, list)):
        return MissionPlan.model_validate(raw)
    return MissionPlan.model_validate_json(raw)  # type: ignore[arg-type]


def list_mission_plans(
    conn: Any,
    skip: int,
    limit: int,
    organization_id: str | None = None,
) -> list[MissionPlan]:
    """Return paginated EASY missions ordered chronologically descending."""

    order = mission_list_order_clause(conn)

    if organization_id is None:
        cursor = conn.execute(
            f"""
            SELECT mission_plan_snapshot FROM missions
            {order}
            LIMIT ? OFFSET ?
            """,
            (limit, skip),
        )
    else:
        cursor = conn.execute(
            f"""
            SELECT mission_plan_snapshot FROM missions
            WHERE organization_id = ?
            {order}
            LIMIT ? OFFSET ?
            """,
            (organization_id, limit, skip),
        )

    plans: list[MissionPlan] = []
    for r in cursor.fetchall():
        raw = r["mission_plan_snapshot"]
        if isinstance(raw, (dict, list)):
            plans.append(MissionPlan.model_validate(raw))
        else:
            plans.append(MissionPlan.model_validate_json(raw))
    return plans
