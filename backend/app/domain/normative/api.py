"""Corpus Normativo inspection routers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.domain.normative.models import NormativeRule
from app.domain.normative.services import NormativeService

router = APIRouter(prefix="/normative", tags=["normative"])


def get_normative_service(request: Request) -> NormativeService:
    """Surface governance engine registered during lifespan."""

    svc = getattr(request.app.state, "normative_service", None)
    if svc is None:
        msg = "Normative Corpus not initialized."
        raise RuntimeError(msg)
    return svc


@router.get("/rules", response_model=list[NormativeRule])
def list_normative_rules(
    service: NormativeService = Depends(get_normative_service),
) -> list[NormativeRule]:
    """Return active normative rules sorted by EASY priority descending."""

    return service.get_active_rules()
