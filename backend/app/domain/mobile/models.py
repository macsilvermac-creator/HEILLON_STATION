"""Pydantic contracts for Phase 8 mobile payloads."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.mission.models import MissionPlan


class PushTokenRegisterRequest(BaseModel):
    """opaque Web Push subscription envelope (browser JSON.stringify(subscription))."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subscription_json: str = Field(min_length=8, description="JSON describing PushSubscription")


class PushTokenRegisterResponse(BaseModel):
    """Acknowledgement façade."""

    stored: bool = True


class MobileQuickStats(BaseModel):
    """Condensed judiciary tiles tuned for handset dashboards."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_missions: int
    pending_approvals: int
    completed: int
    failed: int


class PendingApprovalsEnvelope(BaseModel):
    """Pending human approval gate missions for compact mobile lists."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total: int
    missions: list[MissionPlan]
