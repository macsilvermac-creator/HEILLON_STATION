"""FastAPI application entry establishing Heillon Legal custody rails."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import config as runtime_config
from app.api.health import router as health_router
from app.core.logging_config import configure_logging
from app.core.rate_limit import rate_limit_middleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.compat import open_connection
from app.db.database import init_database, sqlite_file_path
from app.domain.evidence.api import router as evidence_router
from app.domain.forensic.api import router as forensic_router
from app.domain.forensic.services import ForensicPackageService
from app.domain.hdr.api import router as hdr_verification_router
from app.domain.mission.api import router as mission_router
from app.domain.mission.agent_registry_setup import build_agent_registry
from app.domain.mission.services import OrchestrationEngine
from app.domain.normative.api import router as normative_router
from app.domain.normative.anchoring_service import NormativeAnchoringService
from app.domain.normative.compliance_api import router as compliance_router
from app.domain.normative.fts_repository import seed_corpus
from app.domain.normative.lgpd_br import LGPD_FRAMEWORK
from app.domain.normative.repository import NormativeRepository
from app.domain.normative.services import DEFAULT_LEGAL_RULES, NormativeService
from app.domain.hdr.services import HDRService
from app.domain.mission.agent_config_api import router as agent_config_router
from app.domain.mission.agent_config_service import AgentConfigService
from app.domain.mobile.api import router as mobile_router
from app.domain.privacy.api import router as privacy_router
from app.domain.governance.api import router as governance_router
from app.domain.euaiact.api import router as euaiact_router
from app.domain.user.api import router as identity_router
from app.domain.user.services import AuthService

logger = logging.getLogger("heillon.legal")

# Configure structured logging before anything else runs.
# This will be overridden once settings are loaded in lifespan, but gives
# sensible defaults for import-time warnings.
configure_logging(environment="development")


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize persistence plus governance singletons."""

    settings = runtime_config.get_settings()
    configure_logging(environment=settings.ENVIRONMENT)

    if settings.FORCE_STUB_TIMESTAMP:
        if settings.ENVIRONMENT == "production":
            msg = "FORCE_STUB_TIMESTAMP=True in production is FORBIDDEN. HDR timestamps would lack probative value."
            raise RuntimeError(msg)
        logger.warning(
            "FORCE_STUB_TIMESTAMP=True — RFC3161 artefacts are deterministic stubs. Use only in development/testing."
        )

    sqlite_path = sqlite_file_path(settings.DATABASE_URL).resolve()
    application.state.sqlite_path = str(sqlite_path)

    init_database(settings)

    normative_repository = NormativeRepository(list(DEFAULT_LEGAL_RULES))
    normative_service = NormativeService(repository=normative_repository)

    # Seed FTS5 corpus (safe to re-run; uses UPSERT internally)
    with open_connection(settings) as seed_conn:
        try:
            seed_corpus(seed_conn, list(DEFAULT_LEGAL_RULES))
        except Exception as _seed_err:
            logger.warning("FTS5 corpus seed skipped: %s", _seed_err)

    hdr_singleton = HDRService()

    agent_config_binding = AgentConfigService(settings=settings, database_path=sqlite_path)

    orchestration_registry = build_agent_registry(settings)
    orchestration_engine = OrchestrationEngine(
        normative_service,
        hdr_singleton,
        orchestration_registry,
        agent_config_service=agent_config_binding,
    )

    forensic_service = ForensicPackageService()

    auth_bundle = AuthService(
        secret_key=settings.AUTH_SECRET_KEY,
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    anchoring_service = NormativeAnchoringService()
    anchoring_service.register_framework(LGPD_FRAMEWORK)

    application.state.normative_service = normative_service
    application.state.orchestration_engine = orchestration_engine
    application.state.hdr_singleton = hdr_singleton
    application.state.forensic_service = forensic_service
    application.state.auth_service = auth_bundle
    application.state.agent_config_service = agent_config_binding
    application.state.anchoring_service = anchoring_service

    yield


def create_application() -> FastAPI:
    """Application factory simplifying hypervisor tests."""

    settings = runtime_config.get_settings()

    is_production = settings.ENVIRONMENT == "production"
    application = FastAPI(
        title="Heillon Legal — HDR Ledger Service",
        version="0.4.0-mvp",
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers — added first so they wrap every response.
    application.add_middleware(SecurityHeadersMiddleware, is_production=is_production)

    class RateLimitHttpMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[override]
            return await rate_limit_middleware(request, call_next)

    application.add_middleware(RateLimitHttpMiddleware)

    api_prefix = settings.API_V1_PREFIX
    application.include_router(evidence_router, prefix=api_prefix)
    application.include_router(hdr_verification_router, prefix=api_prefix)
    application.include_router(mission_router, prefix=api_prefix)
    application.include_router(normative_router, prefix=api_prefix)
    application.include_router(compliance_router, prefix=api_prefix)
    application.include_router(forensic_router, prefix=api_prefix)
    application.include_router(identity_router, prefix=api_prefix)
    application.include_router(agent_config_router, prefix=api_prefix)
    application.include_router(mobile_router, prefix=api_prefix)
    application.include_router(privacy_router, prefix=api_prefix)
    application.include_router(governance_router, prefix=api_prefix)
    application.include_router(euaiact_router, prefix=api_prefix)
    application.include_router(health_router)
    application.include_router(health_router, prefix=api_prefix)

    return application


app = create_application()
