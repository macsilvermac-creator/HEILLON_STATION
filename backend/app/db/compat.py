"""Dual-backend database connection (SQLite dev/test, PostgreSQL produção)."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Literal

from app.core.config import Settings, get_settings

DbDialect = Literal["sqlite", "postgresql"]


def resolve_dialect(settings: Settings | None = None) -> DbDialect:
    settings = settings or get_settings()
    explicit = (getattr(settings, "DATABASE_TYPE", None) or "").strip().lower()
    if explicit in ("postgresql", "postgres"):
        return "postgresql"
    if explicit == "sqlite":
        return "sqlite"
    url = settings.DATABASE_URL.lower()
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        return "postgresql"
    return "sqlite"


def _adapt_placeholders(sql: str, dialect: DbDialect) -> str:
    if dialect == "sqlite":
        return sql
    parts = re.split(r"(\?)", sql)
    out: list[str] = []
    for part in parts:
        if part == "?":
            out.append("%s")
        else:
            out.append(part)
    return "".join(out)


class CompatConnection:
    """Thin wrapper unificando sqlite3 e psycopg2 para repositórios existentes."""

    dialect: DbDialect

    def __init__(self, raw: Any, dialect: DbDialect) -> None:
        self._raw = raw
        self.dialect = dialect

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] | None = None):
        params = params or ()
        sql = _adapt_placeholders(sql, self.dialect)
        if self.dialect == "postgresql":
            import psycopg2.extras

            cur = self._raw.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            return cur
        return self._raw.execute(sql, params)

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def close(self) -> None:
        self._raw.close()

    def executescript(self, script: str) -> None:
        if self.dialect == "sqlite":
            self._raw.executescript(script)
            return

        import psycopg2.extensions as pg_ext

        # Strip SQL comments UP-FRONT, before splitting on ';'. A ';' inside a
        # comment (e.g. "-- base table; FTS5 omitido") would otherwise corrupt
        # the naive split and feed a syntax-error fragment to psycopg2; a
        # comment-only fragment makes it raise "can't execute an empty query".
        # The bootstrap DDL has no string literals containing '--', '/* */' or
        # ';', so whole-script comment removal is safe here.
        clean = re.sub(r"/\*.*?\*/", "", script, flags=re.DOTALL)
        clean = re.sub(r"--[^\n]*", "", clean)

        prev_isolation = self._raw.isolation_level
        self._raw.set_isolation_level(pg_ext.ISOLATION_LEVEL_AUTOCOMMIT)
        try:
            statements = [s.strip() for s in clean.split(";") if s.strip()]
            for stmt in statements:
                upper = stmt.upper()
                if upper.startswith("BEGIN") or upper.startswith("COMMIT"):
                    continue
                cur = self._raw.cursor()
                try:
                    cur.execute(stmt)
                finally:
                    cur.close()
        finally:
            self._raw.set_isolation_level(prev_isolation)


@contextmanager
def open_connection(
    settings: Settings | None = None,
) -> Generator[CompatConnection, None, None]:
    settings = settings or get_settings()
    dialect = resolve_dialect(settings)

    if dialect == "postgresql":
        import psycopg2

        conn = psycopg2.connect(settings.effective_database_url)
        wrapped = CompatConnection(conn, dialect)
        try:
            yield wrapped
            wrapped.commit()
        except Exception:
            wrapped.rollback()
            raise
        finally:
            wrapped.close()
        return

    from app.db.database import sqlite_file_path

    path = sqlite_file_path(settings.DATABASE_URL)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = sqlite3.connect(path.as_posix(), check_same_thread=False)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA journal_mode=WAL")
    raw.execute("PRAGMA foreign_keys=ON")
    raw.execute("PRAGMA synchronous=NORMAL")
    wrapped = CompatConnection(raw, dialect)
    try:
        yield wrapped
        wrapped.commit()
    except Exception:
        wrapped.rollback()
        raise
    finally:
        wrapped.close()
