"""F30B2 — RetentionService (auto-purge HDR por tier) tests."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone


def _fresh_settings():
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/retention_test.db"
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["ENVIRONMENT"] = "development"

    from app.core import config

    config._settings = None
    from app.core.config import get_settings
    from app.db.database import init_database

    settings = get_settings()
    init_database(settings)
    return settings


def _mk_org(conn, org_id: str, tier: str) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO organizations (organization_id, name, tier,
                                       tier_period_start, tier_period_end,
                                       tier_updated_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (org_id, f"Org {org_id}", tier, now_iso, now_iso, now_iso, now_iso),
    )


def _mk_hdr(conn, hdr_id: str, org_id: str, created_at: datetime) -> None:
    iso = created_at.isoformat()
    conn.execute(
        """INSERT INTO hdrs (hdr_id, mission_id, previous_hdr, hdr_type,
                              timestamp_iso, canonical_hash, payload,
                              organization_id, created_at)
           VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)""",
        (hdr_id, "mis_ret", "analysis", iso, "h" * 64, "{}", org_id, iso),
    )


def _count_hdrs(conn, org_id: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM hdrs WHERE organization_id = ?", (org_id,)
    ).fetchone()[0]


def test_free_tier_purges_after_30d():
    settings = _fresh_settings()
    from app.db.compat import open_connection
    from app.domain.tier.retention import RetentionService

    now = datetime.now(timezone.utc)
    with open_connection(settings) as conn:
        _mk_org(conn, "org_free", "free")
        # Recent (kept) + old (purged)
        _mk_hdr(conn, "free_recent", "org_free", now - timedelta(days=5))
        _mk_hdr(conn, "free_old", "org_free", now - timedelta(days=45))

    with open_connection(settings) as conn:
        result = RetentionService.purge_all(conn, now=now)

    assert result.total_hdrs_purged == 1
    with open_connection(settings) as conn:
        assert _count_hdrs(conn, "org_free") == 1
        remaining = conn.execute(
            "SELECT hdr_id FROM hdrs WHERE organization_id = ?", ("org_free",)
        ).fetchone()[0]
    assert remaining == "free_recent"


def test_pro_tier_keeps_within_365d():
    settings = _fresh_settings()
    from app.db.compat import open_connection
    from app.domain.tier.retention import RetentionService

    now = datetime.now(timezone.utc)
    with open_connection(settings) as conn:
        _mk_org(conn, "org_pro", "pro")
        _mk_hdr(conn, "pro_200d", "org_pro", now - timedelta(days=200))
        _mk_hdr(conn, "pro_400d", "org_pro", now - timedelta(days=400))

    with open_connection(settings) as conn:
        result = RetentionService.purge_all(conn, now=now)

    # Only the 400d one exceeds the 365d window
    assert result.total_hdrs_purged == 1
    with open_connection(settings) as conn:
        assert _count_hdrs(conn, "org_pro") == 1


def test_enterprise_never_purges():
    settings = _fresh_settings()
    from app.db.compat import open_connection
    from app.domain.tier.retention import RetentionService

    now = datetime.now(timezone.utc)
    with open_connection(settings) as conn:
        _mk_org(conn, "org_ent", "enterprise")
        _mk_hdr(conn, "ent_ancient", "org_ent", now - timedelta(days=4000))

    with open_connection(settings) as conn:
        result = RetentionService.purge_all(conn, now=now)

    assert result.total_hdrs_purged == 0
    with open_connection(settings) as conn:
        assert _count_hdrs(conn, "org_ent") == 1


def test_purge_is_idempotent():
    settings = _fresh_settings()
    from app.db.compat import open_connection
    from app.domain.tier.retention import RetentionService

    now = datetime.now(timezone.utc)
    with open_connection(settings) as conn:
        _mk_org(conn, "org_free2", "free")
        _mk_hdr(conn, "old1", "org_free2", now - timedelta(days=60))

    with open_connection(settings) as conn:
        r1 = RetentionService.purge_all(conn, now=now)
    with open_connection(settings) as conn:
        r2 = RetentionService.purge_all(conn, now=now)

    assert r1.total_hdrs_purged == 1
    assert r2.total_hdrs_purged == 0


def test_multi_org_mixed_tiers():
    settings = _fresh_settings()
    from app.db.compat import open_connection
    from app.domain.tier.retention import RetentionService

    now = datetime.now(timezone.utc)
    with open_connection(settings) as conn:
        _mk_org(conn, "o_free", "free")
        _mk_org(conn, "o_ent", "enterprise")
        _mk_hdr(conn, "f_old", "o_free", now - timedelta(days=90))
        _mk_hdr(conn, "e_old", "o_ent", now - timedelta(days=90))

    with open_connection(settings) as conn:
        result = RetentionService.purge_all(conn, now=now)

    assert result.total_hdrs_purged == 1  # only free org's HDR
    assert result.organizations_purged == 1
    with open_connection(settings) as conn:
        assert _count_hdrs(conn, "o_free") == 0
        assert _count_hdrs(conn, "o_ent") == 1
