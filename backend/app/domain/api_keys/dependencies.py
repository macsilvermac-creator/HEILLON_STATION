"""FastAPI dependency for API-key authentication (used by collectors).

Collectors (Browser Extension, MCP Gateway, custom integrations) authenticate
via the `X-Heillon-Api-Key` header — NOT JWT (no session cookie).

This dependency:
1. Reads X-Heillon-Api-Key header
2. Looks up active (non-revoked) API key by SHA-256 of plaintext
3. Updates last_used_at timestamp (best-effort, non-blocking)
4. Returns the API key's owning UserRecord
5. Raises 401 if missing/invalid/revoked
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.dependencies import database_dependency
from app.domain.api_keys.services import ApiKeyService
from app.domain.user.models import UserRecord
from app.domain.user.repository import UserRepository

logger = logging.getLogger("heillon.legal.api_keys.auth")


def get_user_from_api_key(
    conn=Depends(database_dependency),
    x_heillon_api_key: Annotated[str | None, Header(alias="X-Heillon-Api-Key")] = None,
) -> UserRecord:
    """Resolve API key to its owning UserRecord. Updates last_used_at as side effect."""
    if not x_heillon_api_key or not x_heillon_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key obrigatória no header X-Heillon-Api-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    record = ApiKeyService.find_active_by_plaintext(conn, x_heillon_api_key.strip())
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida ou revogada.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Best-effort touch (never block request on logging failure)
    try:
        ApiKeyService.touch_last_used(conn, record.api_key_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("touch_last_used failed for %s: %s", record.api_key_id, exc)

    user = UserRepository().get_by_id(conn, record.user_id)
    if user is None:
        # API key owner was deleted — orphan key
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operador da API key não encontrado.",
        )
    return user
