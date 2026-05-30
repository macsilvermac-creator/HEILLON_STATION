"""Domain service for the beta feedback bounded context.

Keeps routers thin: handles id/timestamp minting on submit and assembles the
de-identified aggregate snapshot on read.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domain.feedback.models import (
    AxisAverages,
    FeedbackAck,
    FeedbackComment,
    FeedbackSubmission,
    FeedbackSummary,
    NpsSummary,
)
from app.domain.feedback.repository import FeedbackRepository


class FeedbackService:
    """Records survey submissions and builds operator summaries."""

    def __init__(self, repository: FeedbackRepository | None = None) -> None:
        self._repo = repository or FeedbackRepository()

    def submit(
        self,
        conn: Any,
        *,
        organization_id: str,
        user_id: str | None,
        role: str | None,
        submission: FeedbackSubmission,
    ) -> FeedbackAck:
        feedback_id = f"fb_{uuid.uuid4().hex}"
        created_at = datetime.now(timezone.utc).isoformat()
        self._repo.insert(
            conn,
            feedback_id=feedback_id,
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            created_at=created_at,
            submission=submission,
        )
        return FeedbackAck(id=feedback_id, created_at=created_at)

    def summary(self, conn: Any, *, comment_limit: int = 25) -> FeedbackSummary:
        now = datetime.now(timezone.utc).isoformat()
        averages = self._repo.axis_averages(conn)
        nps_raw = self._repo.nps_breakdown(conn)

        responses = nps_raw["responses"]
        score: float | None = None
        if responses > 0:
            score = round(
                (nps_raw["promoters"] - nps_raw["detractors"]) / responses * 100, 1
            )

        comments = [
            FeedbackComment(**row)
            for row in self._repo.recent_comments(conn, limit=comment_limit)
        ]

        return FeedbackSummary(
            snapshot_at=now,
            response_count=self._repo.response_count(conn),
            averages=AxisAverages(**averages),
            nps=NpsSummary(
                responses=responses,
                promoters=nps_raw["promoters"],
                passives=nps_raw["passives"],
                detractors=nps_raw["detractors"],
                score=score,
            ),
            adopt_breakdown=self._repo.adopt_breakdown(conn),
            contact_optins=self._repo.contact_optins(conn),
            recent_comments=comments,
        )
