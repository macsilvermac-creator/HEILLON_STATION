"""Authentication façade for judiciary operators."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies import database_dependency
from app.core import config as runtime_config
from app.domain.user.models import TokenResponse, UserCreate, UserLogin, UserPublic
from app.domain.user.repository import UserRepository
from app.domain.user.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

auth_scheme = HTTPBearer(auto_error=False)


def get_auth_service(request: Request) -> AuthService:
    """Resolve cryptography helpers registered during lifespan wiring."""

    service = getattr(request.app.state, "auth_service", None)
    if service is None:
        msg = "Auth service not wired — application startup incomplete."
        raise RuntimeError(msg)
    return service


def bearer_credentials(
    authorization: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> HTTPAuthorizationCredentials | None:
    return authorization


@router.post("/register", response_model=TokenResponse)
def register_operator(
    body: UserCreate,
    conn=Depends(database_dependency),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Onboard EASY operators with bcrypt digests."""

    repo = UserRepository()
    conflict = repo.get_by_email(conn, str(body.email))
    if conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já registado.")

    settings = runtime_config.get_settings()
    organization_target = body.organization_id or settings.DEFAULT_ORGANIZATION_ID
    org_name = f"Organização {organization_target}"

    repo.ensure_organization(conn, organization_id=organization_target, name=org_name)

    record = repo.create_user(
        conn,
        email=str(body.email),
        name=body.name,
        hashed_password=auth_service.hash_password(body.password),
        role=body.role,
        organization_id=organization_target,
    )

    token = auth_service.create_access_token(
        subject=record.user_id,
        claims={"organization_id": record.organization_id, "role": record.role.value},
    )

    persona = UserPublic(
        user_id=record.user_id,
        email=record.email,
        name=record.name,
        role=record.role,
        organization_id=record.organization_id,
        is_active=record.is_active,
    )

    return TokenResponse(access_token=token, token_type="bearer", user=persona.model_dump(mode="json"))


@router.post("/login", response_model=TokenResponse)
def login_operator(
    body: UserLogin,
    conn=Depends(database_dependency),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate returning HS256 artefacts."""

    repo = UserRepository()
    record = repo.get_by_email(conn, str(body.email))
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
    if not record.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operador inativo.")
    if not auth_service.verify_password(body.password, record.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    token = auth_service.create_access_token(
        subject=record.user_id,
        claims={"organization_id": record.organization_id, "role": record.role.value},
    )
    persona = UserPublic(
        user_id=record.user_id,
        email=record.email,
        name=record.name,
        role=record.role,
        organization_id=record.organization_id,
        is_active=record.is_active,
    )

    return TokenResponse(access_token=token, token_type="bearer", user=persona.model_dump(mode="json"))


@router.get("/me", response_model=UserPublic)
def current_operator_snapshot(
    conn=Depends(database_dependency),
    auth_service: AuthService = Depends(get_auth_service),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_credentials),
) -> UserPublic:
    """Return sanitized operator dossier anchored to bearer subject."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais em falta.")
    payload = auth_service.decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.")

    user_id = str(payload["sub"])
    record = UserRepository().get_by_id(conn, user_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Operador desconhecido.")

    return UserPublic(
        user_id=record.user_id,
        email=record.email,
        name=record.name,
        role=record.role,
        organization_id=record.organization_id,
        is_active=record.is_active,
    )
