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
    FORENSICS_PACKAGE_DIR: Path = Field(default_factory=lambda: Path("data/forensic_packages"))
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
    OPENAI_API_KEY: str | None = Field(default=None, description="When set, analysis-agent binds to Chat Completions API.")
    OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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
    def ensure_fernet_encryption_key(self) -> Settings:
        """Require an explicit Fernet key in production; derive a separate dev key otherwise."""

        key_in = self.FERNET_ENCRYPTION_KEY.strip()
        auth = self.AUTH_SECRET_KEY.strip()
        if key_in:
            if key_in == auth:
                msg = "FERNET_ENCRYPTION_KEY must not equal AUTH_SECRET_KEY"
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
