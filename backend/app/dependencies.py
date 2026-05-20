"""Application-wide dependency injection wiring."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import config as runtime_config
from app.core.config import Settings
from app.db.database import sqlite_file_path
from app.domain.hdr.services import HDRService
from app.domain.user.models import UserRecord
from app.domain.user.repository import UserRepository
from app.domain.user.services import AuthService


def settings_dependency() -> Settings:
    """Provide settings for downstream injections."""

    return runtime_config.get_settings()


def database_dependency(
    settings: Settings = Depends(settings_dependency),
) -> Generator[sqlite3.Connection, None, None]:
    """Open SQLite connectivity with explicit transaction framing."""

    path = sqlite_file_path(settings.DATABASE_URL)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path.as_posix(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def hdr_service_dependency() -> HDRService:
    """Expose HDR cryptography helpers."""

    return HDRService()


mission_optional_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class MissionActor:
    """Runtime actor envelope bound to EASY mission routing."""

    organization_id: str
    user_id: str | None = None


def resolve_mission_actor(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(mission_optional_bearer)],
) -> MissionActor:
    """Return tenant-aware actor context enforcing optional EASY authentication gates."""

    settings = runtime_config.get_settings()

    if not settings.MISSION_ROUTES_REQUIRE_AUTH:
        return MissionActor(organization_id=settings.DEFAULT_ORGANIZATION_ID, user_id=None)

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais em falta.")

    auth_service: AuthService | None = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth indisponível.")

    payload = auth_service.decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.")

    subject = payload.get("sub")
    org_claim = payload.get("organization_id") or settings.DEFAULT_ORGANIZATION_ID
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem sujeito.")

    return MissionActor(organization_id=str(org_claim), user_id=str(subject))


strict_bearer = HTTPBearer(auto_error=True)


def get_current_user_record(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(database_dependency)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(strict_bearer)],
) -> UserRecord:
    """Resolve bearer subject to a hydrated ``UserRecord`` (ingestion and compliance gates)."""

    auth_service: AuthService | None = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth indisponível.")

    payload = auth_service.decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.")

    user_id = str(payload.get("sub") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem sujeito.")

    record = UserRepository().get_by_id(conn, user_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Operador desconhecido.")

    return record
