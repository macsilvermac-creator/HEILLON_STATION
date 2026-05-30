"""Mechanically translate SQLite migrations 010-022 into PostgreSQL DDL.

Output is appended-ready: plain statements separated by single ';', no
BEGIN/COMMIT, no FTS5 virtual tables, no triggers (Postgres uses LIKE/ILIKE
fallback in app code). Conservative type mapping preserves app behaviour
(TEXT/INTEGER kept as-is; repos write ISO strings + int flags via ?-params).
"""

from __future__ import annotations

import re
from pathlib import Path

MIG = Path(__file__).resolve().parent.parent / "backend" / "app" / "db" / "migrations"
OUT = (
    Path(__file__).resolve().parent.parent
    / "supabase"
    / "migrations"
    / "_pg_parity_010_022.sql"
)

FILES = [
    "010_privacy_f14.sql",
    "011_icp_f15.sql",
    "012_governance_f16.sql",
    "013_euaiact_f17.sql",
    "014_signatures.sql",
    "015_usa_f18.sql",
    "016_uae_f19.sql",
    "017_iso42001_fria_f20.sql",
    "018_legal_evidence_f20.sql",
    "019_apac_global_f20.sql",
    "020_malpractice_f20.sql",
    "021_freemium_tiers.sql",
    "022_api_keys.sql",
]

# Matches strftime(...) with or without an outer wrapping paren; we emit the
# Postgres equivalent without outer parens (extra surrounding parens are fine).
STRFTIME = re.compile(
    r"strftime\('%Y-%m-%dT%H:%M:%SZ',\s*'now'\)", re.IGNORECASE
)
PG_NOW = "to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"')"


def strip_blocks(sql: str) -> str:
    """Remove FTS5 virtual tables, trigger blocks and BEGIN/COMMIT (SQLite-only)."""
    # Strip comments FIRST: line comments often contain ';' which would corrupt
    # the naive ';' statement split (leaking comment text into the next stmt).
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", "", sql)
    # Standalone transaction control — Postgres bootstrap runs autocommit.
    sql = re.sub(r"(?im)^\s*BEGIN\s*;\s*$", "", sql)
    sql = re.sub(r"(?im)^\s*COMMIT\s*;\s*$", "", sql)
    # Triggers: CREATE TRIGGER ... END;  (contain inner ';')
    sql = re.sub(
        r"CREATE\s+TRIGGER\b.*?END\s*;",
        "",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # Virtual (FTS5) tables: CREATE VIRTUAL TABLE ... );
    sql = re.sub(
        r"CREATE\s+VIRTUAL\s+TABLE\b.*?\)\s*;",
        "",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return sql


def transform_stmt(stmt: str) -> str | None:
    s = stmt.strip()
    if not s:
        return None
    up = s.upper()
    if up in ("BEGIN", "COMMIT") or up.startswith("BEGIN ") or up.startswith("PRAGMA"):
        return None
    # Drop data-backfill UPDATEs (legacy-row fixups); irrelevant on a fresh
    # Postgres DB and they assume SQLite TEXT timestamp columns.
    if up.startswith("UPDATE "):
        return None
    # Drop any leftover FTS/trigger fragments defensively.
    if "FTS5" in up or "VIRTUAL TABLE" in up or up.startswith("CREATE TRIGGER"):
        return None

    # AUTOINCREMENT -> BIGSERIAL
    s = re.sub(
        r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
        "BIGSERIAL PRIMARY KEY",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(r"\s+AUTOINCREMENT", "", s, flags=re.IGNORECASE)

    # strftime(...) -> Postgres now() ISO text (defaults and UPDATE backfills)
    s = STRFTIME.sub(PG_NOW, s)

    # IF NOT EXISTS guards
    s = re.sub(
        r"CREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)",
        "CREATE TABLE IF NOT EXISTS ",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?!IF\s+NOT\s+EXISTS)",
        lambda m: f"CREATE {m.group(1) or ''}INDEX IF NOT EXISTS ",
        s,
        flags=re.IGNORECASE,
    )
    # ALTER TABLE ADD COLUMN -> IF NOT EXISTS
    s = re.sub(
        r"ADD\s+COLUMN\s+(?!IF\s+NOT\s+EXISTS)",
        "ADD COLUMN IF NOT EXISTS ",
        s,
        flags=re.IGNORECASE,
    )
    # INSERT OR IGNORE -> INSERT ... ON CONFLICT DO NOTHING
    conflict = False
    if re.match(r"INSERT\s+OR\s+IGNORE", s, flags=re.IGNORECASE):
        s = re.sub(r"INSERT\s+OR\s+IGNORE", "INSERT", s, flags=re.IGNORECASE)
        conflict = "ON CONFLICT" not in up
    if conflict:
        s = s + "\nON CONFLICT DO NOTHING"
    return s + ";"


def main() -> None:
    out: list[str] = [
        "-- =====================================================================",
        "-- PARIDADE Postgres das migracoes SQLite 010-022 (gerado por script).",
        "-- FTS5/triggers omitidos (Postgres usa fallback LIKE/ILIKE no app).",
        "-- Tipos conservadores: TEXT/INTEGER preservados (timestamps ISO em TEXT).",
        "-- =====================================================================",
        "",
    ]
    tables: list[str] = []
    for fname in FILES:
        path = MIG / fname
        raw = strip_blocks(path.read_text(encoding="utf-8"))
        out.append(f"-- ===== {fname} =====")
        for chunk in raw.split(";"):
            stmt = transform_stmt(chunk)
            if stmt is None:
                continue
            m = re.search(
                r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z_][\w]*)", stmt, re.IGNORECASE
            )
            if m:
                tables.append(m.group(1))
            out.append(stmt)
        out.append("")

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"WROTE {OUT}  ({len(out)} lines)")
    print(f"TABLES ({len(tables)}): " + ", ".join(tables))


if __name__ == "__main__":
    main()
