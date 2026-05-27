"""Extension capture API — authenticated via X-Heillon-Api-Key header."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core import config as runtime_config
from app.dependencies import database_dependency, hdr_service_dependency
from app.domain.api_keys.dependencies import get_user_from_api_key
from app.domain.extension.models import (
    ExtensionCaptureQuota,
    ExtensionCaptureRequest,
    ExtensionCaptureResponse,
    ExtensionHealthResponse,
)
from app.domain.extension.services import build_capture_hdr
from app.domain.hdr.repository import HDRRepository
from app.domain.hdr.services import HDRService
from app.domain.normative.corpus_seed import CORPUS_VERSION
from app.domain.tier.models import QuotaExceededError, QuotaSnapshot
from app.domain.tier.services import QuotaService
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/extension", tags=["extension"])

_hdr_repository = HDRRepository()


def _to_extension_quota(snap: QuotaSnapshot) -> ExtensionCaptureQuota:
    """Trim QuotaSnapshot to the fields the extension needs."""
    return ExtensionCaptureQuota(
        used=snap.used_in_period,
        limit=snap.monthly_hdr_limit,
        remaining=snap.remaining,
        tier=snap.tier.value,
    )


@router.get("/health", response_model=ExtensionHealthResponse)
def extension_health(
    conn=Depends(database_dependency),
    user: UserRecord = Depends(get_user_from_api_key),
) -> ExtensionHealthResponse:
    """Verify the API key works + return current tier/quota.

    Called by the extension on startup AND periodically to refresh quota.
    """
    snap = QuotaService.snapshot(conn, organization_id=user.organization_id)
    return ExtensionHealthResponse(
        organization_id=user.organization_id,
        tier=snap.tier.value,
        quota=_to_extension_quota(snap),
        server_time=datetime.now(timezone.utc),
    )


@router.post(
    "/capture",
    response_model=ExtensionCaptureResponse,
    status_code=status.HTTP_201_CREATED,
)
def capture_ai_interaction(
    body: ExtensionCaptureRequest,
    conn=Depends(database_dependency),
    hdr_svc: HDRService = Depends(hdr_service_dependency),
    user: UserRecord = Depends(get_user_from_api_key),
) -> ExtensionCaptureResponse:
    """Receive an AI interaction from the browser extension; generate signed HDR.

    Quota: each successful capture counts as 1 HDR. Returns HTTP 402 when
    the org has hit its monthly limit (extension shows upgrade dialog).
    """
    # 1) Enforce quota BEFORE doing the (expensive) HDR generation
    try:
        QuotaService.enforce(conn, organization_id=user.organization_id)
    except QuotaExceededError as exc:
        snap = exc.snapshot
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "quota_exceeded",
                "message": (
                    f"Limite de {snap.monthly_hdr_limit} HDRs/mês atingido no plano "
                    f"{snap.tier.value}. Faça upgrade para continuar capturando."
                ),
                "tier": snap.tier.value,
                "used": snap.used_in_period,
                "limit": snap.monthly_hdr_limit,
                "period_end": snap.period_end.isoformat(),
            },
        ) from exc

    # 2) Build the HDR (this is what calls TSA + signs canonically)
    hdr = build_capture_hdr(
        hdr_svc,
        req=body,
        user_id=user.user_id,
        corpus_version=CORPUS_VERSION,
    )

    # 3) Persist with org isolation
    _hdr_repository.insert(conn, hdr, organization_id=user.organization_id)

    # 4) Refresh quota for response (now reflects this new HDR)
    snap_after = QuotaService.snapshot(conn, organization_id=user.organization_id)

    settings = runtime_config.get_settings()
    verification_url = f"{settings.VERIFICATION_PUBLIC_BASE.rstrip('/')}/verification/{hdr.hdr_id}"

    return ExtensionCaptureResponse(
        hdr_id=hdr.hdr_id,
        mission_id=hdr.mission_id,
        verification_url=verification_url,
        quota=_to_extension_quota(snap_after),
    )
