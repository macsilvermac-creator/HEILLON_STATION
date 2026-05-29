"""Gateway HTTP surface: OpenAI-compatible + Anthropic-compatible proxies."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.dependencies import database_dependency, hdr_service_dependency
from app.domain.api_keys.dependencies import get_user_from_api_key
from app.domain.extension.models import (
    AiProvider,
    ExtensionCaptureRequest,
)
from app.domain.extension.services import build_capture_hdr
from app.domain.gateway.dependencies import (
    get_anthropic_upstream_config,
    get_upstream_config,
)
from app.domain.gateway.models import (
    ChatCompletionRequest,
    GatewayUpstreamConfig,
)
from app.domain.gateway.services import (
    DEFAULT_ANTHROPIC_VERSION,
    StreamAccumulator,
    UpstreamError,
    extract_anthropic_prompt_text,
    extract_anthropic_response_text,
    extract_prompt_text,
    extract_response_text,
    forward_anthropic_messages,
    forward_anthropic_messages_stream,
    forward_chat_completion,
    forward_chat_completion_stream,
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
            hdr.hdr_id,
            provider.value,
            model,
            user.user_id,
        )
        return hdr.hdr_id
    except Exception as exc:  # noqa: BLE001
        logger.error("Gateway HDR persistence failed: %s", exc, exc_info=True)
        return None


async def _handle_streaming(
    *,
    conn,  # used only for synchronous phase, not the stream generator
    hdr_svc: HDRService,
    user: UserRecord,
    upstream: GatewayUpstreamConfig,
    body: ChatCompletionRequest,
) -> StreamingResponse:
    """Stream upstream SSE to the client while accumulating for HDR.

    Heillon metadata is emitted as SSE comments (prefix `:`) AFTER the upstream
    stream completes. Spec-ignored by standard parsers; Heillon-aware clients
    can parse `: heillon-hdr-id=...` lines.

    IMPORTANT: FastAPI tears down request-scoped dependencies (incl. DB conn)
    AS SOON AS the endpoint function returns. With StreamingResponse the
    generator keeps running after that, so we MUST open a fresh DB connection
    inside the generator for the post-stream HDR persistence.
    """
    accumulator = StreamAccumulator()
    provider_enum = _provider_for(upstream.upstream_provider)
    prompt_text = extract_prompt_text(body)
    request_body = body.model_dump(exclude_none=True, mode="json")
    organization_id = user.organization_id

    # Capture immutable settings + user data BEFORE the generator (dependencies
    # may be released before the generator's first call to `conn`).
    from app.core import config as runtime_config
    from app.db.compat import open_connection

    settings_snapshot = runtime_config.get_settings()

    async def event_generator():
        # Phase 1: stream upstream chunks verbatim while accumulating
        async for chunk in forward_chat_completion_stream(
            request_body=request_body,
            upstream=upstream,
            accumulator=accumulator,
        ):
            yield chunk

        # Phase 2: upstream ended. Skip HDR on error (don't bill quota).
        if accumulator.had_error:
            return

        synthetic_source = (
            f"https://gateway.heillon.local/{upstream.upstream_provider}/"
            f"{body.model.replace('/', '_')}"
        )

        # Open a FRESH connection — the request's conn was closed when the
        # endpoint function returned the StreamingResponse object.
        try:
            with open_connection(settings_snapshot) as fresh_conn:
                hdr_id = _persist_hdr_for_capture(
                    conn=fresh_conn,
                    hdr_svc=hdr_svc,
                    user=user,
                    prompt_text=prompt_text,
                    response_text=accumulator.text,
                    model=body.model,
                    provider=provider_enum,
                    source_url=synthetic_source,
                )
                # Phase 3: emit Heillon metadata as SSE comments (spec-ignored)
                if hdr_id:
                    try:
                        snap = QuotaService.snapshot(
                            fresh_conn, organization_id=organization_id
                        )
                        limit_str = (
                            str(snap.monthly_hdr_limit)
                            if snap.monthly_hdr_limit is not None
                            else "unlimited"
                        )
                        meta = (
                            f": heillon-hdr-id={hdr_id}\n"
                            f": heillon-quota-used={snap.used_in_period}\n"
                            f": heillon-quota-limit={limit_str}\n"
                            f": heillon-quota-tier={snap.tier.value}\n\n"
                        )
                    except Exception:  # noqa: BLE001
                        meta = f": heillon-hdr-id={hdr_id}\n\n"
                    yield meta.encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            # Persistence failure: log but don't bubble up — the stream
            # already delivered the response to the user. They'd just see
            # no `heillon-hdr-id` comment, which is the right signal.
            logger.error("Streaming HDR persistence failed: %s", exc, exc_info=True)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            # Disable proxy buffering (Nginx, Cloudflare, etc.) so chunks
            # arrive at the client as soon as we yield them.
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


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
    # 1) Enforce quota BEFORE upstream call (so we don't burn user's upstream
    # quota if Heillon is at limit). Quota errors return 402 in non-streaming
    # mode. For streaming mode we still check upfront (the 402 path doesn't
    # need to be SSE since the stream hasn't started yet).
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

    # 2) Branch: streaming vs synchronous
    if body.stream:
        return await _handle_streaming(
            conn=conn,
            hdr_svc=hdr_svc,
            user=user,
            upstream=upstream,
            body=body,
        )

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
            "X-Heillon-Quota-Limit": str(snap_after.monthly_hdr_limit)
            if snap_after.monthly_hdr_limit
            else "unlimited",
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


# ── Anthropic Messages compat (F31.2) ────────────────────────────────────────


async def _handle_anthropic_streaming(
    *,
    hdr_svc: HDRService,
    user: UserRecord,
    upstream: GatewayUpstreamConfig,
    request_body: dict[str, Any],
    anthropic_version: str,
) -> StreamingResponse:
    """Stream Anthropic SSE to the client while accumulating for HDR.

    Same lifecycle pattern as OpenAI streaming — open a fresh DB connection
    inside the generator (FastAPI tears down the request's conn before the
    generator finishes). Heillon metadata emitted as SSE comments after
    the upstream stream completes.
    """
    accumulator = StreamAccumulator()
    prompt_text = extract_anthropic_prompt_text(request_body)
    model_name = str(request_body.get("model") or "claude-unknown")
    organization_id = user.organization_id

    from app.core import config as runtime_config
    from app.db.compat import open_connection

    settings_snapshot = runtime_config.get_settings()

    async def event_generator():
        async for chunk in forward_anthropic_messages_stream(
            request_body=request_body,
            upstream=upstream,
            accumulator=accumulator,
            anthropic_version=anthropic_version,
        ):
            yield chunk

        if accumulator.had_error:
            return

        synthetic_source = (
            f"https://gateway.heillon.local/anthropic/{model_name.replace('/', '_')}"
        )

        try:
            with open_connection(settings_snapshot) as fresh_conn:
                hdr_id = _persist_hdr_for_capture(
                    conn=fresh_conn,
                    hdr_svc=hdr_svc,
                    user=user,
                    prompt_text=prompt_text,
                    response_text=accumulator.text,
                    model=model_name,
                    provider=AiProvider.ANTHROPIC,
                    source_url=synthetic_source,
                )
                if hdr_id:
                    try:
                        snap = QuotaService.snapshot(
                            fresh_conn, organization_id=organization_id
                        )
                        limit_str = (
                            str(snap.monthly_hdr_limit)
                            if snap.monthly_hdr_limit is not None
                            else "unlimited"
                        )
                        meta = (
                            f": heillon-hdr-id={hdr_id}\n"
                            f": heillon-quota-used={snap.used_in_period}\n"
                            f": heillon-quota-limit={limit_str}\n"
                            f": heillon-quota-tier={snap.tier.value}\n\n"
                        )
                    except Exception:  # noqa: BLE001
                        meta = f": heillon-hdr-id={hdr_id}\n\n"
                    yield meta.encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Streaming Anthropic HDR persistence failed: %s", exc, exc_info=True
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/anthropic/v1/messages",
    summary="Drop-in Anthropic Messages proxy with HDR audit",
)
async def anthropic_messages(
    request: Request,
    conn=Depends(database_dependency),
    hdr_svc: HDRService = Depends(hdr_service_dependency),
    user: UserRecord = Depends(get_user_from_api_key),
    upstream: GatewayUpstreamConfig = Depends(get_anthropic_upstream_config),
    anthropic_version: Annotated[
        str, Header(alias="anthropic-version")
    ] = DEFAULT_ANTHROPIC_VERSION,
) -> JSONResponse:
    """Anthropic-compatible endpoint for `client.messages.create(...)` SDK calls.

    Headers (all required for upstream):
      - X-Heillon-Api-Key — your Heillon API key
      - X-Upstream-Api-Key — your Anthropic API key (sk-ant-...)
      - X-Heillon-Upstream-Url (optional) — defaults to https://api.anthropic.com
      - anthropic-version (optional) — defaults to "2023-06-01"

    Returns the upstream JSON response verbatim PLUS:
      - X-Heillon-Hdr-Id, X-Heillon-Quota-Used/-Limit/-Tier on success

    For streaming (`stream: true`): returns text/event-stream with verbatim
    Anthropic events. Heillon metadata emitted as SSE comments after [DONE].

    Body validation: lenient (Anthropic schema is large + evolving). Required
    fields (model, messages, max_tokens) are enforced by upstream.
    """
    # Parse body permissively — anthropic-python sends many optional fields
    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON body: {exc}",
        ) from exc

    if not isinstance(body, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Body must be a JSON object",
        )
    if not body.get("model"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required field: 'model'",
        )
    if not body.get("messages"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required field: 'messages'",
        )

    # Quota enforce BEFORE upstream call
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

    if body.get("stream"):
        return await _handle_anthropic_streaming(
            hdr_svc=hdr_svc,
            user=user,
            upstream=upstream,
            request_body=body,
            anthropic_version=anthropic_version,
        )

    # Synchronous path
    try:
        upstream_response = await forward_anthropic_messages(
            request_body=body,
            upstream=upstream,
            anthropic_version=anthropic_version,
        )
    except UpstreamError as exc:
        return JSONResponse(status_code=exc.status_code, content=exc.body)

    prompt_text = extract_anthropic_prompt_text(body)
    response_text = extract_anthropic_response_text(upstream_response)
    model_name = str(body.get("model") or "claude-unknown")
    synthetic_source = (
        f"https://gateway.heillon.local/anthropic/{model_name.replace('/', '_')}"
    )
    hdr_id = _persist_hdr_for_capture(
        conn=conn,
        hdr_svc=hdr_svc,
        user=user,
        prompt_text=prompt_text,
        response_text=response_text,
        model=model_name,
        provider=AiProvider.ANTHROPIC,
        source_url=synthetic_source,
    )

    try:
        snap_after = QuotaService.snapshot(conn, organization_id=user.organization_id)
        quota_headers = {
            "X-Heillon-Quota-Used": str(snap_after.used_in_period),
            "X-Heillon-Quota-Limit": (
                str(snap_after.monthly_hdr_limit)
                if snap_after.monthly_hdr_limit
                else "unlimited"
            ),
            "X-Heillon-Quota-Tier": snap_after.tier.value,
        }
    except Exception:  # noqa: BLE001
        quota_headers = {}

    return JSONResponse(
        content=upstream_response,
        headers={"X-Heillon-Hdr-Id": hdr_id or "", **quota_headers},
    )
