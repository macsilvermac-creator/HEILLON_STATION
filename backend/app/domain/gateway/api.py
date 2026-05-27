"""Gateway HTTP surface: OpenAI-compatible /v1/chat/completions proxy."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.dependencies import database_dependency, hdr_service_dependency
from app.domain.api_keys.dependencies import get_user_from_api_key
from app.domain.extension.models import (
    AiProvider,
    ExtensionCaptureRequest,
)
from app.domain.extension.services import build_capture_hdr
from app.domain.gateway.dependencies import get_upstream_config
from app.domain.gateway.models import (
    ChatCompletionRequest,
    GatewayUpstreamConfig,
)
from app.domain.gateway.services import (
    UpstreamError,
    extract_prompt_text,
    extract_response_text,
    forward_chat_completion,
)
from app.domain.hdr.repository import HDRRepository
from app.domain.hdr.services import HDRService
from app.domain.normative.corpus_seed import CORPUS_VERSION
from app.domain.tier.models import QuotaExceededError
from app.domain.tier.services import QuotaService
from app.domain.user.models import UserRecord

logger = logging.getLogger("heillon.legal.gateway.api")

router = APIRouter(prefix="/gateway", tags=["gateway"])

_hdr_repository = HDRRepository()

# Map upstream_provider string → AiProvider enum used by HDR capture
_PROVIDER_MAP = {
    "openai": AiProvider.OPENAI,
    "anthropic": AiProvider.ANTHROPIC,
    "google": AiProvider.GOOGLE,
    "mistral": AiProvider.MISTRAL,
    "deepseek": AiProvider.DEEPSEEK,
    "meta": AiProvider.META,
    "perplexity": AiProvider.PERPLEXITY,
}


def _provider_for(label: str) -> AiProvider:
    return _PROVIDER_MAP.get(label.lower(), AiProvider.OTHER)


def _persist_hdr_for_capture(
    *,
    conn,
    hdr_svc: HDRService,
    user: UserRecord,
    prompt_text: str,
    response_text: str,
    model: str,
    provider: AiProvider,
    source_url: str,
) -> str | None:
    """Persist the HDR using the request's open connection.

    Synchronous (inside the request) so X-Heillon-Hdr-Id can be returned in
    response headers. Failures here MUST NOT bubble up — upstream call already
    succeeded; we log and return None instead.
    """
    try:
        capture = ExtensionCaptureRequest(
            provider=provider,
            model=model,
            prompt=prompt_text[:64_000],  # respect MAX_PROMPT_CHARS
            response=response_text[:256_000],
            source_url=source_url,
            captured_at=datetime.now(timezone.utc),
            ai_session_id=None,
            extension_version="gateway_v1",
            page_title="Heillon Gateway",
        )
        hdr = build_capture_hdr(
            hdr_svc,
            req=capture,
            user_id=user.user_id,
            corpus_version=CORPUS_VERSION,
        )
        _hdr_repository.insert(conn, hdr, organization_id=user.organization_id)
        logger.info(
            "Gateway HDR created: %s provider=%s model=%s user=%s",
            hdr.hdr_id, provider.value, model, user.user_id,
        )
        return hdr.hdr_id
    except Exception as exc:  # noqa: BLE001
        logger.error("Gateway HDR persistence failed: %s", exc, exc_info=True)
        return None


@router.post(
    "/v1/chat/completions",
    summary="Drop-in OpenAI Chat Completions proxy with HDR audit",
)
async def openai_chat_completions(
    body: ChatCompletionRequest,
    conn=Depends(database_dependency),
    hdr_svc: HDRService = Depends(hdr_service_dependency),
    user: UserRecord = Depends(get_user_from_api_key),
    upstream: GatewayUpstreamConfig = Depends(get_upstream_config),
) -> JSONResponse:
    """OpenAI-compatible endpoint that forwards to upstream and audits in background.

    Headers:
      - X-Heillon-Api-Key (required) — your Heillon API key
      - X-Upstream-Api-Key (required) — your OpenAI/Together/etc API key
      - X-Heillon-Upstream-Url (optional) — defaults to https://api.openai.com
      - X-Heillon-Upstream-Provider (optional) — defaults to "openai"

    Returns the upstream response verbatim PLUS extra response headers:
      - X-Heillon-Hdr-Id: the HDR that was generated for this call (may be empty
        if persistence failed — call still succeeds for the client)
      - X-Heillon-Quota-Used / -Limit / -Tier
    """
    # 1) Reject streaming for MVP
    if body.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stream=true not supported in MVP — use synchronous calls.",
        )

    # 2) Enforce quota BEFORE upstream call (so we don't burn user's upstream quota
    # if Heillon is at limit). Quota errors return 402.
    try:
        QuotaService.enforce(conn, organization_id=user.organization_id)
    except QuotaExceededError as exc:
        snap = exc.snapshot
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "quota_exceeded",
                "message": (
                    f"Heillon: limite de {snap.monthly_hdr_limit} HDRs/mês "
                    f"atingido no plano {snap.tier.value}."
                ),
                "tier": snap.tier.value,
                "used": snap.used_in_period,
                "limit": snap.monthly_hdr_limit,
                "period_end": snap.period_end.isoformat(),
            },
        ) from exc

    # 3) Forward to upstream
    try:
        upstream_response = await forward_chat_completion(
            request=body,
            upstream=upstream,
        )
    except UpstreamError as exc:
        # Proxy upstream errors verbatim (preserves provider's error format)
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.body,
        )

    # 4) Persist HDR synchronously (we want the hdr_id in response headers).
    #    Use a fresh connection (don't depend on FastAPI background tasks for
    #    this so the user sees immediate confirmation via X-Heillon-Hdr-Id).
    prompt_text = extract_prompt_text(body)
    response_text = extract_response_text(upstream_response)
    provider_enum = _provider_for(upstream.upstream_provider)
    # Synthetic but valid HTTPS URL so HttpUrl validation passes; encodes the
    # gateway provenance for human inspection in the verification UI.
    synthetic_source = (
        f"https://gateway.heillon.local/{upstream.upstream_provider}/"
        f"{body.model.replace('/', '_')}"
    )
    hdr_id = _persist_hdr_for_capture(
        conn=conn,
        hdr_svc=hdr_svc,
        user=user,
        prompt_text=prompt_text,
        response_text=response_text,
        model=body.model,
        provider=provider_enum,
        source_url=synthetic_source,
    )

    # 5) Refresh quota for response headers (best-effort)
    try:
        snap_after = QuotaService.snapshot(conn, organization_id=user.organization_id)
        quota_headers = {
            "X-Heillon-Quota-Used": str(snap_after.used_in_period),
            "X-Heillon-Quota-Limit": str(snap_after.monthly_hdr_limit) if snap_after.monthly_hdr_limit else "unlimited",
            "X-Heillon-Quota-Tier": snap_after.tier.value,
        }
    except Exception:  # noqa: BLE001
        quota_headers = {}

    response_headers = {
        "X-Heillon-Hdr-Id": hdr_id or "",
        **quota_headers,
    }

    return JSONResponse(
        content=upstream_response.model_dump(mode="json"),
        headers=response_headers,
    )


@router.get("/v1/models", summary="Compatibility shim — lists upstream's models")
async def list_models(
    user: UserRecord = Depends(get_user_from_api_key),
    upstream: GatewayUpstreamConfig = Depends(get_upstream_config),
) -> JSONResponse:
    """Pass-through to upstream's /v1/models (clients often probe this).

    No HDR created — listing isn't an inference event.
    """
    import httpx

    url = f"{upstream.upstream_base_url}/v1/models"
    headers = {"Authorization": f"Bearer {upstream.upstream_api_key}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Upstream unreachable: {exc}",
            ) from exc

    try:
        body = r.json()
    except Exception:  # noqa: BLE001
        body = {"error": {"message": r.text[:500]}}
    return JSONResponse(status_code=r.status_code, content=body)
