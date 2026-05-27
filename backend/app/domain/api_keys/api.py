"""API keys REST surface — under /me/api-keys for the authenticated user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import database_dependency, get_current_user_record
from app.domain.api_keys.models import ApiKeyCreate, ApiKeyMintResponse, ApiKeyPublic
from app.domain.api_keys.services import ApiKeyService
from app.domain.user.models import UserRecord

router = APIRouter(prefix="/me/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyPublic])
def list_my_keys(
    conn=Depends(database_dependency),
    user: UserRecord = Depends(get_current_user_record),
) -> list[ApiKeyPublic]:
    """List all API keys for the authenticated user's organization."""
    return ApiKeyService.list_by_org(conn, organization_id=user.organization_id)


@router.post("", response_model=ApiKeyMintResponse, status_code=status.HTTP_201_CREATED)
def mint_key(
    body: ApiKeyCreate,
    conn=Depends(database_dependency),
    user: UserRecord = Depends(get_current_user_record),
) -> ApiKeyMintResponse:
    """Mint a new API key. Plaintext returned ONCE — show in UI then forget."""
    return ApiKeyService.mint(
        conn,
        organization_id=user.organization_id,
        user_id=user.user_id,
        name=body.name,
    )


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def revoke_key(
    api_key_id: str,
    conn=Depends(database_dependency),
    user: UserRecord = Depends(get_current_user_record),
) -> Response:
    """Mark an API key as revoked. Idempotent: 404 if not found or already revoked."""
    ok = ApiKeyService.revoke(
        conn,
        api_key_id=api_key_id,
        organization_id=user.organization_id,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key não encontrada ou já revogada.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
