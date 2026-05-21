"""Authentication façade for judiciary operators."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies import AUTH_COOKIE_NAME, database_dependency, settings_dependency
from app.core.config import Settings
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


def _attach_session_cookie(response: JSONResponse, *, settings: Settings, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/register", response_model=None)
def register_operator(
    body: UserCreate,
    conn=Depends(database_dependency),
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(settings_dependency),
) -> JSONResponse:
    """Onboard EASY operators with bcrypt digests."""

    repo = UserRepository()
    conflict = repo.get_by_email(conn, str(body.email))
    if conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já registado.")

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

    payload = TokenResponse(
        access_token=token, token_type="bearer", user=persona.model_dump(mode="json")
    ).model_dump(mode="json")
    response = JSONResponse(content=payload, status_code=status.HTTP_200_OK)
    _attach_session_cookie(response, settings=settings, token=token)
    return response


@router.post("/login", response_model=None)
def login_operator(
    body: UserLogin,
    conn=Depends(database_dependency),
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(settings_dependency),
) -> JSONResponse:
    """Authenticate returning HS256 artefacts + HttpOnly session cookie."""

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

    payload = TokenResponse(
        access_token=token, token_type="bearer", user=persona.model_dump(mode="json")
    ).model_dump(mode="json")
    response = JSONResponse(content=payload, status_code=status.HTTP_200_OK)
    _attach_session_cookie(response, settings=settings, token=token)
    return response


@router.post("/logout")
def logout_operator() -> JSONResponse:
    """Clear HttpOnly session cookie (JSON body remains compatible with proxies)."""

    response = JSONResponse(content={"detail": "Sessão terminada."}, status_code=status.HTTP_200_OK)
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    return response


@router.get("/me", response_model=UserPublic)
def current_operator_snapshot(
    request: Request,
    conn=Depends(database_dependency),
    auth_service: AuthService = Depends(get_auth_service),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_credentials),
) -> UserPublic:
    """Return sanitized operator dossier anchored to bearer subject or session cookie."""

    token: str | None = None
    if credentials is not None:
        token = credentials.credentials
    if token is None:
        token = request.cookies.get(AUTH_COOKIE_NAME)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais em falta.")

    payload = auth_service.decode_token(token)
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
