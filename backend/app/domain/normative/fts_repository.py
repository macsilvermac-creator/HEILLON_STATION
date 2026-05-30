"""FTS5-backed normative corpus repository for full-text search.

The in-memory NormativeRepository remains the primary source for rule evaluation
(fast, no DB round-trip). This module handles persistence + FTS5 search only.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.normative.models import (
    NormativeCategory,
    NormativeRule,
    ViolationAction,
)


def _is_postgres(conn) -> bool:
    """True when running against PostgreSQL (CompatConnection carries dialect).

    FTS5 virtual tables and their MATCH/rebuild syntax are SQLite-only. On
    Postgres a failed FTS statement would also poison the whole transaction
    ("current transaction is aborted"), so callers must skip those paths and
    use the LIKE/ILIKE fallback instead.
    """

    return getattr(conn, "dialect", "sqlite") in ("postgresql", "postgres")


def seed_corpus(conn, rules: Sequence[NormativeRule]) -> None:
    """Upsert default rules into SQLite, rebuilding the FTS5 index."""

    for rule in rules:
        conn.execute(
            """
            INSERT INTO normative_rules
                (rule_id, name, description, category, condition_text,
                 action_on_violation, priority, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rule_id) DO UPDATE SET
                name                = excluded.name,
                description         = excluded.description,
                category            = excluded.category,
                condition_text      = excluded.condition_text,
                action_on_violation = excluded.action_on_violation,
                priority            = excluded.priority,
                enabled             = excluded.enabled
            """,
            (
                rule.rule_id,
                rule.name,
                rule.description,
                rule.category.value,
                rule.condition,
                rule.action_on_violation.value,
                rule.priority,
                int(rule.enabled),
            ),
        )

    _rebuild_fts(conn)


def search_rules(conn, query: str, *, limit: int = 20) -> list[NormativeRule]:
    """Full-text search across name, description and condition_text using FTS5.

    Returns rules ordered by relevance (BM25 rank).
    Falls back to LIKE search when the FTS table isn't available.
    """

    if not query or not query.strip():
        return _list_all(conn, limit=limit)

    clean = query.strip()

    # SQLite: try the FTS5 MATCH path first (BM25 relevance ranking).
    if not _is_postgres(conn):
        try:
            rows = conn.execute(
                """
                SELECT r.rule_id, r.name, r.description, r.category,
                       r.condition_text, r.action_on_violation, r.priority, r.enabled
                FROM normative_rules_fts f
                JOIN normative_rules r ON r.rule_id = f.rule_id
                WHERE normative_rules_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (clean, limit),
            ).fetchall()
            return [_row_to_rule(row) for row in rows]
        except Exception:
            pass  # FTS table unavailable — fall through to LIKE

    # Postgres (no FTS5) or SQLite fallback: case-insensitive substring search.
    op = "ILIKE" if _is_postgres(conn) else "LIKE"
    like = f"%{clean}%"
    rows = conn.execute(
        f"""
        SELECT rule_id, name, description, category,
               condition_text, action_on_violation, priority, enabled
        FROM normative_rules
        WHERE name {op} ? OR description {op} ? OR condition_text {op} ?
        LIMIT ?
        """,  # noqa: S608
        (like, like, like, limit),
    ).fetchall()

    return [_row_to_rule(row) for row in rows]


def _list_all(conn, *, limit: int = 100) -> list[NormativeRule]:
    rows = conn.execute(
        "SELECT rule_id, name, description, category, condition_text, "
        "action_on_violation, priority, enabled FROM normative_rules "
        "ORDER BY priority DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [_row_to_rule(row) for row in rows]


def _rebuild_fts(conn) -> None:
    # FTS5 is SQLite-only; on Postgres this statement would fail and poison the
    # surrounding transaction, silently rolling back the corpus seed.
    if _is_postgres(conn):
        return
    try:
        conn.execute(
            "INSERT INTO normative_rules_fts(normative_rules_fts) VALUES('rebuild')"
        )
    except Exception:
        pass


def _row_to_rule(row) -> NormativeRule:
    # Named access works for both sqlite3.Row and psycopg2 RealDictCursor;
    # positional access (row[0]) would raise on RealDictCursor (dict rows).
    return NormativeRule(
        rule_id=row["rule_id"],
        name=row["name"],
        description=row["description"],
        category=NormativeCategory(row["category"]),
        condition=row["condition_text"],
        action_on_violation=ViolationAction(row["action_on_violation"]),
        priority=row["priority"],
        enabled=bool(row["enabled"]),
    )
