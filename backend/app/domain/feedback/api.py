"""Beta feedback REST surface.

POST /feedback        — authenticated beta user submits the usability survey.
GET  /feedback/summary — operator-only (X-Heillon-Admin-Token) aggregate read.

The summary reuses the admin-token dependency so it lives alongside the other
beta operator tooling without a second auth scheme.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.dependencies import database_dependency, get_current_user_record
from app.domain.admin.api import admin_auth
from app.domain.feedback.models import (
    FeedbackAck,
    FeedbackSubmission,
    FeedbackSummary,
)
from app.domain.feedback.services import FeedbackService
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/feedback", tags=["feedback"])

_service = FeedbackService()


def _role_str(user: UserRecord) -> str | None:
    role = getattr(user, "role", None)
    if role is None:
        return None
    return getattr(role, "value", None) or str(role)


@router.post("", response_model=FeedbackAck, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    body: FeedbackSubmission,
    conn=Depends(database_dependency),
    user: UserRecord = Depends(get_current_user_record),
) -> FeedbackAck:
    """Record a voluntary product feedback submission for the beta survey."""
    return _service.submit(
        conn,
        organization_id=user.organization_id,
        user_id=user.user_id,
        role=_role_str(user),
        submission=body,
    )


@router.get(
    "/summary",
    dependencies=[Depends(admin_auth)],
    response_model=FeedbackSummary,
)
def feedback_summary(conn=Depends(database_dependency)) -> FeedbackSummary:
    """De-identified aggregate of all feedback (averages, NPS, comments)."""
    return _service.summary(conn)
