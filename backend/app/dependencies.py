"""Application-wide dependency injection wiring."""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import config as runtime_config
from app.core.config import Settings
from app.db.compat import CompatConnection, open_connection
from app.db.tenant_security import set_tenant_context
from app.domain.hdr.services import HDRService
from app.domain.user.models import UserRecord
from app.domain.user.repository import UserRepository
from app.domain.user.services import AuthService


def settings_dependency() -> Settings:
    """Provide settings for downstream injections."""

    return runtime_config.get_settings()


def database_dependency(
    settings: Settings = Depends(settings_dependency),
) -> Generator[CompatConnection, None, None]:
    """Open database connectivity with explicit transaction framing."""

    with open_connection(settings) as conn:
        yield conn


def hdr_service_dependency() -> HDRService:
    """Expose HDR cryptography helpers."""

    return HDRService()


mission_optional_bearer = HTTPBearer(auto_error=False)

AUTH_COOKIE_NAME = "heillon_token"


def _access_token_from_request(
    request: Request, credentials: HTTPAuthorizationCredentials | None
) -> str | None:
    if credentials is not None:
        return credentials.credentials
    return request.cookies.get(AUTH_COOKIE_NAME)


@dataclass(frozen=True)
class MissionActor:
    """Runtime actor envelope bound to EASY mission routing."""

    organization_id: str
    user_id: str | None = None


def resolve_mission_actor(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(mission_optional_bearer)
    ],
) -> MissionActor:
    """Return tenant-aware actor context enforcing optional EASY authentication gates."""

    settings = runtime_config.get_settings()

    if not settings.MISSION_ROUTES_REQUIRE_AUTH:
        return MissionActor(
            organization_id=settings.DEFAULT_ORGANIZATION_ID, user_id=None
        )

    token = _access_token_from_request(request, credentials)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais em falta."
        )

    auth_service: AuthService | None = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth indisponível.",
        )

    payload = auth_service.decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida."
        )

    subject = payload.get("sub")
    org_claim = payload.get("organization_id") or settings.DEFAULT_ORGANIZATION_ID
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem sujeito."
        )

    return MissionActor(organization_id=str(org_claim), user_id=str(subject))


def tenant_database_dependency(
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    actor: Annotated[MissionActor, Depends(resolve_mission_actor)],
    settings: Settings = Depends(settings_dependency),
) -> CompatConnection:
    """Open connection scoped to the authenticated actor's organization (RLS-aware)."""

    if settings.ENABLE_POSTGRES_RLS and settings.resolved_database_type == "postgresql":
        set_tenant_context(conn, actor.organization_id)
    return conn


optional_auth_bearer = HTTPBearer(auto_error=False)


def get_current_user_record(
    request: Request,
    conn: Annotated[CompatConnection, Depends(database_dependency)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(optional_auth_bearer)
    ],
) -> UserRecord:
    """Resolve bearer subject to a hydrated ``UserRecord`` (ingestion and compliance gates)."""

    auth_service: AuthService | None = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth indisponível.",
        )

    token = _access_token_from_request(request, credentials)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais em falta."
        )

    payload = auth_service.decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida."
        )

    user_id = str(payload.get("sub") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem sujeito."
        )

    record = UserRepository().get_by_id(conn, user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Operador desconhecido."
        )

    return record
