"""FastAPI dependency for HDR quota enforcement.

Endpoints that CREATE HDRs declare `Depends(enforce_hdr_quota)` to be
automatically rejected with HTTP 402 when the org has hit its monthly limit.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.dependencies import database_dependency, get_current_user_record
from app.domain.tier.models import QuotaExceededError, QuotaSnapshot
from app.domain.tier.services import QuotaService
from app.domain.user.models import UserRecord


def enforce_hdr_quota(
    conn=Depends(database_dependency),
    user: UserRecord = Depends(get_current_user_record),
) -> QuotaSnapshot:
    """Check quota BEFORE the endpoint runs; return 402 if exceeded.

    Returns the snapshot on success so the endpoint can log usage if needed.
    Uses the same DB connection as the rest of the request (same transaction).
    """
    try:
        return QuotaService.enforce(conn, organization_id=user.organization_id)
    except QuotaExceededError as exc:
        snap = exc.snapshot
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "quota_exceeded",
                "message": (
                    f"Limite de {snap.monthly_hdr_limit} HDRs/mês atingido "
                    f"no plano {snap.tier.value}. Faça upgrade para continuar."
                ),
                "tier": snap.tier.value,
                "used": snap.used_in_period,
                "limit": snap.monthly_hdr_limit,
                "period_end": snap.period_end.isoformat(),
            },
        ) from exc
