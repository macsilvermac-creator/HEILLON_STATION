"""F30B2 — DELETE /privacy/account (LGPD art. 18 VI) tests."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime

from fastapi.testclient import TestClient


def _fresh_app():
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/del_test.db"
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["FORCE_STUB_TIMESTAMP"] = "true"

    from app.core import config

    config._settings = None
    from app.core.config import get_settings
    from app.db.database import init_database
    from app.main import create_application

    settings = get_settings()
    init_database(settings)
    # Enter the TestClient context so the lifespan runs and wires the auth
    # service onto app.state (register/login depend on it). The client stays
    # open for the test's duration; the temp DB is discarded afterwards.
    client = TestClient(create_application())
    client.__enter__()
    return client, settings


def _bootstrap_user(client) -> tuple[str, dict]:
    """Register a user and return (user_id, cookie-bearing headers)."""
    email = f"del_test_{datetime.now().timestamp()}@x.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "Del Test",
            "password": "delete-me-please-987654321",
            "role": "advogado",
            "organization_id": f"org_del_{int(datetime.now().timestamp())}",
        },
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["user"]["user_id"]
    token = reg.json()["access_token"]
    return user_id, email, {"Authorization": f"Bearer {token}"}


def test_delete_account_requires_auth():
    client, _ = _fresh_app()
    r = client.request(
        "DELETE",
        "/api/v1/privacy/account",
        params={"confirm": "CONFIRMO_ELIMINACAO"},
    )
    assert r.status_code == 401


def test_delete_account_requires_confirm_token():
    client, settings = _fresh_app()
    _, _, headers = _bootstrap_user(client)
    # Without ?confirm param
    r = client.delete("/api/v1/privacy/account", headers=headers)
    assert r.status_code == 422

    # With wrong confirm value
    r = client.delete(
        "/api/v1/privacy/account?confirm=wrong",
        headers=headers,
    )
    assert r.status_code == 422


def test_delete_account_happy_path():
    client, settings = _fresh_app()
    user_id, email, headers = _bootstrap_user(client)

    r = client.delete(
        "/api/v1/privacy/account?confirm=CONFIRMO_ELIMINACAO",
        headers=headers,
    )
    assert r.status_code == 204
    assert r.content == b""

    # Verify user is anonymized + inactive
    from app.db.compat import open_connection

    with open_connection(settings) as conn:
        row = conn.execute(
            "SELECT email, name, is_active, hashed_password FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    assert row is not None
    assert row[0].startswith("deleted+")
    assert row[0].endswith("@heillon.local")
    assert row[1] == "[Conta eliminada]"
    assert bool(row[2]) is False  # is_active = 0
    assert row[3] == "deleted"


def test_delete_account_revokes_api_keys():
    client, settings = _fresh_app()
    user_id, _, headers = _bootstrap_user(client)

    # Create an API key first
    from app.db.compat import open_connection
    from app.domain.api_keys.services import ApiKeyService

    with open_connection(settings) as conn:
        ApiKeyService.mint(
            conn,
            organization_id="org_default",
            user_id=user_id,
            name="To be revoked",
        )
        active_before = conn.execute(
            "SELECT COUNT(*) FROM api_keys WHERE user_id = ? AND revoked_at IS NULL",
            (user_id,),
        ).fetchone()[0]
    assert active_before >= 1

    # Delete the account
    r = client.delete(
        "/api/v1/privacy/account?confirm=CONFIRMO_ELIMINACAO",
        headers=headers,
    )
    assert r.status_code == 204

    # All API keys for this user should now be revoked
    with open_connection(settings) as conn:
        active_after = conn.execute(
            "SELECT COUNT(*) FROM api_keys WHERE user_id = ? AND revoked_at IS NULL",
            (user_id,),
        ).fetchone()[0]
    assert active_after == 0


def test_delete_account_preserves_hdrs():
    """Cadeia probatória é imutável — HDRs NÃO podem ser apagados."""
    client, settings = _fresh_app()
    user_id, _, headers = _bootstrap_user(client)

    # Insert a HDR linked to user's org
    from datetime import timezone

    from app.db.compat import open_connection

    now_iso = datetime.now(timezone.utc).isoformat()
    with open_connection(settings) as conn:
        org_id_row = conn.execute(
            "SELECT organization_id FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        org_id = org_id_row[0]
        conn.execute(
            """INSERT INTO hdrs (hdr_id, mission_id, previous_hdr, hdr_type,
                                  timestamp_iso, canonical_hash, payload,
                                  organization_id, created_at)
               VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)""",
            (
                "del_hdr_001",
                "mis_del_test",
                "analysis",
                now_iso,
                "h" * 64,
                "{}",
                org_id,
                now_iso,
            ),
        )

    # Delete account
    r = client.delete(
        "/api/v1/privacy/account?confirm=CONFIRMO_ELIMINACAO",
        headers=headers,
    )
    assert r.status_code == 204

    # HDR must still exist (immutable chain of custody — LGPD art. 7 II
    # permits retention for legal/regulatory compliance)
    with open_connection(settings) as conn:
        hdr_count = conn.execute(
            "SELECT COUNT(*) FROM hdrs WHERE hdr_id = ?", ("del_hdr_001",)
        ).fetchone()[0]
    assert hdr_count == 1, "HDRs deveriam permanecer (cadeia probatória)"


def test_delete_account_subsequent_login_fails():
    """Após eliminação, novo login com mesma senha deve falhar (is_active=0)."""
    client, _ = _fresh_app()
    _, email, headers = _bootstrap_user(client)

    r = client.delete(
        "/api/v1/privacy/account?confirm=CONFIRMO_ELIMINACAO",
        headers=headers,
    )
    assert r.status_code == 204

    # Try to login with same credentials
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "delete-me-please-987654321"},
    )
    # User was anonymized; email não existe mais com aquele endereço
    assert login.status_code in (401, 404)
