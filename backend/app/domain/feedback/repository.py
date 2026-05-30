"""Persistence for the beta feedback bounded context.

Aggregates use ALIASED columns and NAMED row access so they work on both
sqlite3.Row and psycopg2 RealDictCursor (positional access raises on dict rows).
"""

from __future__ import annotations

from typing import Any

from app.domain.feedback.models import FeedbackSubmission


def _val(row: Any, key: str) -> Any:
    if row is None:
        return None
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


class FeedbackRepository:
    """Insert + read-only aggregate queries for the feedback survey."""

    def insert(
        self,
        conn: Any,
        *,
        feedback_id: str,
        organization_id: str,
        user_id: str | None,
        role: str | None,
        created_at: str,
        submission: FeedbackSubmission,
    ) -> None:
        conn.execute(
            """INSERT INTO beta_feedback (
                    id, organization_id, user_id, role,
                    usability_score, experience_score, functionality_score,
                    delivers_score, nps, adopt,
                    most_valuable, frictions, improvements,
                    contact_ok, created_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id,
                organization_id,
                user_id,
                role,
                submission.usability,
                submission.experience,
                submission.functionality,
                submission.delivers,
                submission.nps,
                submission.adopt,
                submission.most_valuable,
                submission.frictions,
                submission.improvements,
                1 if submission.contact_ok else 0,
                created_at,
            ),
        )

    def response_count(self, conn: Any) -> int:
        return self._scalar(conn, "SELECT COUNT(*) AS cnt FROM beta_feedback")

    def axis_averages(self, conn: Any) -> dict[str, float | None]:
        row = conn.execute(
            """SELECT AVG(usability_score)     AS usability,
                      AVG(experience_score)    AS experience,
                      AVG(functionality_score) AS functionality,
                      AVG(delivers_score)      AS delivers
                 FROM beta_feedback"""
        ).fetchone()
        return {
            "usability": self._round(_val(row, "usability")),
            "experience": self._round(_val(row, "experience")),
            "functionality": self._round(_val(row, "functionality")),
            "delivers": self._round(_val(row, "delivers")),
        }

    def nps_breakdown(self, conn: Any) -> dict[str, int]:
        row = conn.execute(
            """SELECT
                   COUNT(*)                                          AS responses,
                   SUM(CASE WHEN nps >= 9 THEN 1 ELSE 0 END)         AS promoters,
                   SUM(CASE WHEN nps BETWEEN 7 AND 8 THEN 1 ELSE 0 END) AS passives,
                   SUM(CASE WHEN nps BETWEEN 0 AND 6 THEN 1 ELSE 0 END) AS detractors
                 FROM beta_feedback
                WHERE nps IS NOT NULL"""
        ).fetchone()
        return {
            "responses": int(_val(row, "responses") or 0),
            "promoters": int(_val(row, "promoters") or 0),
            "passives": int(_val(row, "passives") or 0),
            "detractors": int(_val(row, "detractors") or 0),
        }

    def adopt_breakdown(self, conn: Any) -> dict[str, int]:
        rows = conn.execute(
            """SELECT adopt, COUNT(*) AS cnt
                 FROM beta_feedback
                WHERE adopt IS NOT NULL AND adopt <> ''
                GROUP BY adopt
                ORDER BY adopt"""
        ).fetchall()
        return {str(_val(r, "adopt")): int(_val(r, "cnt") or 0) for r in rows}

    def contact_optins(self, conn: Any) -> int:
        return self._scalar(
            conn, "SELECT COUNT(*) AS cnt FROM beta_feedback WHERE contact_ok = 1"
        )

    def recent_comments(self, conn: Any, *, limit: int) -> list[dict[str, Any]]:
        """De-identified free-text only — no user_id/org joined out."""
        rows = conn.execute(
            """SELECT created_at, most_valuable, frictions, improvements
                 FROM beta_feedback
                WHERE (most_valuable IS NOT NULL AND most_valuable <> '')
                   OR (frictions IS NOT NULL AND frictions <> '')
                   OR (improvements IS NOT NULL AND improvements <> '')
                ORDER BY created_at DESC
                LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {
                "created_at": str(_val(r, "created_at")),
                "most_valuable": _val(r, "most_valuable"),
                "frictions": _val(r, "frictions"),
                "improvements": _val(r, "improvements"),
            }
            for r in rows
        ]

    # ── private ─────────────────────────────────────────────────────────────
    def _scalar(self, conn: Any, sql: str, params: tuple[Any, ...] = ()) -> int:
        row = conn.execute(sql, params).fetchone()
        return int(_val(row, "cnt") or 0)

    @staticmethod
    def _round(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return None
