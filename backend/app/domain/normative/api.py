"""Corpus Normativo inspection routers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import database_dependency
from app.domain.normative.fts_repository import search_rules
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


@router.get("/search", response_model=list[NormativeRule])
def search_normative_rules(
    q: str = Query(
        default="", description="Full-text search query (FTS5 match syntax)."
    ),
    limit: int = Query(default=20, ge=1, le=100),
    conn=Depends(database_dependency),
) -> list[NormativeRule]:
    """Search the persisted normative corpus using FTS5.

    Supports FTS5 match syntax (e.g. ``q=LGPD AND transfer``).
    Returns rules ordered by relevance.
    """

    return search_rules(conn, q, limit=limit)
