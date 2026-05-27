"""HTTP surface for tier visibility (/me/quota) and billing integration (/billing/webhook).

Security:
- /me/quota requires authenticated user (any tier can read their own).
- /billing/webhook requires HMAC-SHA256 signature in `X-Heillon-Signature` header
  computed with `BILLING_WEBHOOK_SECRET` over the raw request body.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core import config as runtime_config
from app.dependencies import database_dependency, get_current_user_record
from app.domain.tier.models import (
    BillingWebhookEvent,
    BillingWebhookPayload,
    QuotaSnapshot,
    Tier,
)
from app.domain.tier.services import QuotaService
from app.domain.user.models import UserRecord

logger = logging.getLogger("heillon.legal.tier.api")

router_quota = APIRouter(prefix="/me", tags=["quota"])
router_billing = APIRouter(prefix="/billing", tags=["billing"])


@router_quota.get("/quota", response_model=QuotaSnapshot)
def get_my_quota(
    conn=Depends(database_dependency),
    user: UserRecord = Depends(get_current_user_record),
) -> QuotaSnapshot:
    """Return real-time quota state for the authenticated user's organization.

    Consumed by:
    - Heillon Console (banner + /conta/quota page)
    - Browser Extension (block at limit, show progress)
    - MCP Gateway (reject request when exceeded)
    """
    try:
        return QuotaService.snapshot(conn, organization_id=user.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _verify_webhook_signature(secret: str, raw_body: bytes, signature_header: str | None) -> bool:
    """Constant-time HMAC verification of webhook payload."""
    if not signature_header:
        return False
    # Strip optional "sha256=" prefix (Stripe-style)
    candidate = signature_header.split("=", 1)[-1] if "=" in signature_header else signature_header
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(candidate, expected)


@router_billing.post("/webhook", status_code=status.HTTP_200_OK)
async def billing_webhook(
    request: Request,
    x_heillon_signature: Annotated[str | None, Header(alias="X-Heillon-Signature")] = None,
    conn=Depends(database_dependency),
) -> JSONResponse:
    """Receive tier_changed / cancelled events from the external billing site.

    HMAC-SHA256 over the raw body. Returns 401 on bad signature, 400 on
    malformed payload, 404 if org unknown, 200 on success.
    """
    settings = runtime_config.get_settings()
    secret = (settings.BILLING_WEBHOOK_SECRET or "").strip()
    if not secret:
        # Webhook intentionally disabled when no secret configured (dev default)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing webhook not configured.",
        )

    raw_body = await request.body()
    if not _verify_webhook_signature(secret, raw_body, x_heillon_signature):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature.",
        )

    try:
        payload_dict = json.loads(raw_body.decode("utf-8"))
        payload = BillingWebhookPayload.model_validate(payload_dict)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed payload: {exc}",
        ) from exc

    # Branch on event semantics
    if payload.event == BillingWebhookEvent.SUBSCRIPTION_CANCELLED:
        target_tier = Tier.FREE
    elif payload.event == BillingWebhookEvent.PAYMENT_FAILED:
        target_tier = Tier.FREE  # graceful fallback (don't lock out completely)
    else:
        target_tier = payload.tier

    try:
        snapshot = QuotaService.apply_tier_change(
            conn,
            organization_id=payload.organization_id,
            new_tier=target_tier,
            period_end=payload.period_end,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return JSONResponse(
        content={
            "ok": True,
            "organization_id": payload.organization_id,
            "tier": snapshot.tier.value,
            "event": payload.event.value,
        }
    )
