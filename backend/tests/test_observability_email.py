"""F30B3 — Sentry init + EmailService stub-mode tests."""

from __future__ import annotations

import os
import tempfile


def _settings(**overrides):
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/obs_test.db"
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["ENVIRONMENT"] = "development"
    for k, v in overrides.items():
        os.environ[k] = v

    from app.core import config

    config._settings = None
    from app.core.config import get_settings

    return get_settings()


def test_sentry_disabled_when_no_dsn():
    settings = _settings(SENTRY_DSN="")
    from app.core.observability import init_sentry

    assert init_sentry(settings) is False


def test_email_stub_mode_when_no_token():
    settings = _settings(POSTMARK_SERVER_TOKEN="")
    from app.core.email import EmailService

    svc = EmailService(settings)
    assert svc.enabled is False

    result = svc.send(
        to="advogado@exemplo.com",
        subject="Convite beta Heillon",
        text_body="Bem-vindo ao beta.",
    )
    assert result.sent is False
    assert result.stubbed is True


def test_email_service_uses_configured_from():
    settings = _settings(POSTMARK_SERVER_TOKEN="", EMAIL_FROM="custom@heillon.local")
    from app.core.email import EmailService

    svc = EmailService(settings)
    assert svc._from == "custom@heillon.local"


def test_app_boots_with_observability_settings():
    """create_application não deve quebrar com settings de observability."""
    _settings(SENTRY_DSN="", POSTMARK_SERVER_TOKEN="")
    from app.main import create_application

    app = create_application()
    assert app is not None
