"""Phase 9 — regressions that prove critical security closures."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, _derive_fernet_key_from_auth



def test_stub_timestamp_forbidden_in_production_via_constructor():
    """Stub RFC3161 artefacts must not activate when ENVIRONMENT=production."""

    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", FORCE_STUB_TIMESTAMP=True)


def test_stub_timestamp_requires_production_collision_field_order():
    """Validator observes ENVIRONMENT + FORCE_STUB coupling."""

    relaxed = Settings(ENVIRONMENT="development", FORCE_STUB_TIMESTAMP=True)
    assert relaxed.FORCE_STUB_TIMESTAMP is True


def test_mission_routes_require_auth_default():
    defaults = Settings(ENVIRONMENT="development")
    assert defaults.MISSION_ROUTES_REQUIRE_AUTH is True


def test_derived_fernet_key_differs_from_jwt_material():
    s = Settings(ENVIRONMENT="development")
    assert s.AUTH_SECRET_KEY != s.FERNET_ENCRYPTION_KEY
    assert s.FERNET_ENCRYPTION_KEY == _derive_fernet_key_from_auth(s.AUTH_SECRET_KEY)


def test_production_requires_explicit_fernet():
    with pytest.raises(ValidationError, match="FERNET_ENCRYPTION_KEY is mandatory"):
        Settings(ENVIRONMENT="production", FERNET_ENCRYPTION_KEY="", AUTH_SECRET_KEY="x" * 40)
