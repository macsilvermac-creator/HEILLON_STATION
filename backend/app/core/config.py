"""Application configuration using environment variables."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _derive_fernet_key_from_auth(auth_secret: str) -> str:
    """Derive a deterministic Fernet-capable key separate from the raw JWT secret."""

    digest = hashlib.sha256((auth_secret + "::heillon-fernet-v1").encode()).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")


class Settings(BaseSettings):
    """Runtime settings sourced from environment variables."""

    DATABASE_URL: str = "sqlite:///./data/heillon.db"
    DATABASE_TYPE: str = Field(
        default="",
        description="sqlite | postgresql — vazio = inferir de DATABASE_URL.",
    )
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "heillon"
    POSTGRES_USER: str = "heillon"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SSL_MODE: str = "prefer"
    REDIS_URL: str = "redis://localhost:6379/0"
    ENABLE_POSTGRES_RLS: bool = False
    EVIDENCE_DIR: Path = Field(default_factory=lambda: Path("data/evidence"))
    TSA_URL: str = "https://freetsa.org/tsr"
    TSA_PROVIDER: str = Field(
        default="freetsa",
        description="certisign | serpro | freetsa | stub — preferred ICP-Brasil TSA provider.",
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="development | staging | production — gates stub timestamps and Fernet defaults.",
    )
    FORCE_STUB_TIMESTAMP: bool = Field(
        default=False,
        description="Emit deterministic RFC3161 stub tokens offline (never enable in prod).",
    )
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    CORS_ORIGIN_REGEX: str = Field(
        default=r"^chrome-extension://[a-z]{32}$|^moz-extension://[0-9a-f-]{36}$",
        description=(
            "Regex for additional allowed origins (browser extensions). "
            "Default permits Chrome (32-char IDs) and Firefox (UUID-like) extension origins."
        ),
    )
    FORENSICS_PACKAGE_DIR: Path = Field(
        default_factory=lambda: Path("data/forensic_packages")
    )
    VERIFICATION_PUBLIC_BASE: str = "http://127.0.0.1:8000"

    DEFAULT_ORGANIZATION_ID: str = "org_default"
    AUTH_SECRET_KEY: str = Field(
        default="dev-insecure-heillon-secret-change-in-production-min-32-characters-long",
        description="Symmetric secret for JWT signing.",
    )
    FERNET_ENCRYPTION_KEY: str = Field(
        default="",
        description="URL-safe base64 Fernet key for agent API material; must differ from JWT secret.",
    )
    FERNET_ENCRYPTION_KEY_LEGACY: str = Field(
        default="",
        description=(
            "Optional comma-separated list of LEGACY Fernet keys for rotation. "
            "MultiFernet tries each key on decrypt; new ciphertext always uses "
            "FERNET_ENCRYPTION_KEY (the active key). Rotate by: (1) generate new active key, "
            "(2) move old key to LEGACY, (3) re-encrypt records over time, (4) drop LEGACY."
        ),
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=10080)
    MISSION_ROUTES_REQUIRE_AUTH: bool = Field(
        default=True,
        description="When true, mission dossier routes mandate bearer tokens scoped by organization.",
    )
    FORENSICS_USE_STUB_PDF: bool = Field(
        default=False,
        description="When true, forensic executive exports remain plaintext stubs (backward compatibility).",
    )
    FORENSICS_SIGNATURE_PRIVATE_KEY_HEX: str | None = Field(
        default=None,
        description="Optional hex-encoded raw Ed25519 seed (64 hex chars); generates ephemeral signing when unset.",
    )
    DISABLE_RATE_LIMIT: bool = Field(
        default=False,
        description="Bypass rate limiting (never enable in production).",
    )
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="When set, analysis-agent binds to Chat Completions API.",
    )
    OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    # LGPD Fase 14 — DPO settings
    DPO_NAME: str = Field(
        default="Encarregado de Dados", description="Nome do DPO (LGPD art. 41)"
    )
    DPO_EMAIL: str = Field(
        default="dpo@heillon.com", description="E-mail público do DPO (LGPD art. 41)"
    )
    # ICP-Brasil Fase 15 — A1 soft-certificate signing
    ICP_CERT_PATH: str | None = Field(
        default=None,
        description="Path to PKCS#12 (.p12/.pfx) ICP-Brasil A1 certificate file.",
    )
    ICP_CERT_PASSWORD: str = Field(
        default="",
        description="Password for the PKCS#12 ICP-Brasil A1 certificate (empty = no password).",
    )
    # Freemium Fase 26 — billing webhook from external marketing site
    BILLING_WEBHOOK_SECRET: str = Field(
        default="",
        description=(
            "HMAC-SHA256 secret for /api/v1/billing/webhook. When empty, the "
            "webhook endpoint returns 503 (disabled). Set in production."
        ),
    )
    # Admin Fase 30 — beta metrics token (separate from user JWT/API keys)
    HEILLON_ADMIN_TOKEN: str = Field(
        default="",
        description=(
            "Shared-secret token for /api/v1/admin/* endpoints. Min 24 chars "
            "recommended. When empty, admin endpoints return 503 (disabled)."
        ),
    )
    # Observability Fase 30B3 — Sentry (opcional; vazio = desativado)
    SENTRY_DSN: str = Field(
        default="",
        description=(
            "Sentry DSN para captura de erros. Vazio = SDK não inicializado "
            "(zero overhead). Recomendado em produção."
        ),
    )
    SENTRY_TRACES_SAMPLE_RATE: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Taxa de amostragem de performance tracing (0.0–1.0).",
    )
    # E-mail transacional Fase 30B3 — Postmark (opcional; vazio = modo log/stub)
    POSTMARK_SERVER_TOKEN: str = Field(
        default="",
        description=(
            "Token do servidor Postmark para e-mail transacional. Vazio = "
            "EmailService opera em modo stub (apenas loga, não envia)."
        ),
    )
    EMAIL_FROM: str = Field(
        default="nao-responda@heillon.local",
        description="Remetente padrão dos e-mails transacionais.",
    )
    # Mission executors — cache opt-in de cognição EASY (dedup por hash de input)
    MISSION_EXECUTOR_CACHE_TTL_SECONDS: int = Field(
        default=0,
        ge=0,
        description=(
            "TTL (segundos) do cache em processo das cognições EASY, com chave "
            "pelo hash determinístico do prompt (provider:model:input_hash). "
            "Prompts idênticos dentro do TTL reutilizam a resposta do upstream, "
            "reduzindo tokens em re-execuções. 0 = DESATIVADO (padrão), de modo "
            "que cada HDR reflete uma chamada real ao upstream — preservando a "
            "fidelidade forense. Ative apenas conscientemente."
        ),
    )
    # Gateway Fase 31 — teto de tokens de completude (controle de custo)
    GATEWAY_MAX_COMPLETION_TOKENS: int = Field(
        default=4096,
        ge=0,
        description=(
            "Teto de max_tokens repassado ao upstream pelo gateway proxy. "
            "Requisições acima são limitadas a este valor; quando o cliente "
            "omite max_tokens (caminho OpenAI), este teto é injetado para "
            "evitar completudes ilimitadas. 0 = sem teto (repasse verbatim)."
        ),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    _INSECURE_AUTH_DEFAULTS: frozenset[str] = frozenset(
        {
            "dev-insecure-heillon-secret-change-in-production-min-32-characters-long",
            "change-me-min-32-chars-for-jwt-signing",
            "changeme",
            "secret",
        }
    )

    @field_validator("FORCE_STUB_TIMESTAMP")
    @classmethod
    def validate_stub_timestamp(cls, v: bool, info: ValidationInfo) -> bool:
        """Prevent stub timestamps when ENVIRONMENT is production."""

        data = info.data or {}
        env = str(data.get("ENVIRONMENT") or os.getenv("ENVIRONMENT", "development"))
        if v and env == "production":
            msg = "FORCE_STUB_TIMESTAMP cannot be True in production environment"
            raise ValueError(msg)
        return v

    @property
    def resolved_database_type(self) -> str:
        explicit = (self.DATABASE_TYPE or "").strip().lower()
        if explicit in ("postgresql", "postgres"):
            return "postgresql"
        if explicit == "sqlite":
            return "sqlite"
        if self.DATABASE_URL.lower().startswith(("postgresql://", "postgres://")):
            return "postgresql"
        return "sqlite"

    @property
    def effective_database_url(self) -> str:
        if self.resolved_database_type == "postgresql":
            user = quote_plus(self.POSTGRES_USER)
            password = quote_plus(self.POSTGRES_PASSWORD)
            host = self.POSTGRES_HOST
            port = self.POSTGRES_PORT
            db = self.POSTGRES_DB
            ssl = self.POSTGRES_SSL_MODE
            return f"postgresql://{user}:{password}@{host}:{port}/{db}?sslmode={ssl}"
        return self.DATABASE_URL

    @model_validator(mode="after")
    def enforce_production_security(self) -> Settings:
        """Block known-insecure configuration in production before the app starts."""

        if self.ENVIRONMENT != "production":
            return self
        if self.AUTH_SECRET_KEY.strip() in self._INSECURE_AUTH_DEFAULTS:
            msg = "AUTH_SECRET_KEY must be changed from the insecure default in production"
            raise ValueError(msg)
        if not self.MISSION_ROUTES_REQUIRE_AUTH:
            msg = "MISSION_ROUTES_REQUIRE_AUTH must be True in production"
            raise ValueError(msg)
        if self.DISABLE_RATE_LIMIT:
            msg = "DISABLE_RATE_LIMIT cannot be enabled in production"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def ensure_fernet_encryption_key(self) -> Settings:
        """Require an explicit Fernet key in production; derive a separate dev key otherwise."""

        key_in = self.FERNET_ENCRYPTION_KEY.strip()
        auth = self.AUTH_SECRET_KEY.strip()
        if key_in:
            if key_in == auth:
                msg = "FERNET_ENCRYPTION_KEY must not equal AUTH_SECRET_KEY"
                raise ValueError(msg)
            # Reject overlap between active key and legacy ring
            if self.FERNET_ENCRYPTION_KEY_LEGACY.strip():
                legacy_keys = {
                    k.strip()
                    for k in self.FERNET_ENCRYPTION_KEY_LEGACY.split(",")
                    if k.strip()
                }
                if key_in in legacy_keys:
                    msg = (
                        "FERNET_ENCRYPTION_KEY (active) must not appear in "
                        "FERNET_ENCRYPTION_KEY_LEGACY — rotate properly"
                    )
                    raise ValueError(msg)
            return self
        if self.ENVIRONMENT == "production":
            msg = "FERNET_ENCRYPTION_KEY is mandatory in production"
            raise ValueError(msg)
        derived = _derive_fernet_key_from_auth(auth)
        object.__setattr__(self, "FERNET_ENCRYPTION_KEY", derived)
        return self


def get_settings() -> Settings:
    """Load settings ensuring local data directories exist."""

    Path("data").mkdir(parents=True, exist_ok=True)
    settings = Settings()
    settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    settings.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    return settings
