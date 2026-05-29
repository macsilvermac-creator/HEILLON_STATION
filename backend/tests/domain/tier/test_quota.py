"""F26 — Tier & Quota Foundation tests (in-memory SQLite)."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest


def _fresh_db():
    """Create a fresh isolated DB + initialize schema. Return (settings, conn-context-manager)."""
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmpdir}/quota_test.db"
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["ENVIRONMENT"] = "development"
    from app.core import config

    config._settings = None
    from app.core.config import get_settings
    from app.db.database import init_database

    settings = get_settings()
    init_database(settings)
    return settings


def _insert_hdrs(
    conn, *, organization_id: str, count: int, when: datetime | None = None
) -> None:
    """Insert N stub HDRs for quota testing."""
    iso = (when or datetime.now(timezone.utc)).isoformat()
    for i in range(count):
        conn.execute(
            """INSERT INTO hdrs (hdr_id, mission_id, previous_hdr, hdr_type,
                                  timestamp_iso, canonical_hash, payload,
                                  organization_id, created_at)
               VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)""",
            (
                f"hdr_q_{organization_id}_{i:04d}",
                "mis_q_test",
                "analysis",
                iso,
                "h" * 64,
                "{}",
                organization_id,
                iso,
            ),
        )


# ── PROBE 1: snapshot for default org returns tier=free with limit=50 ──────────


def test_default_org_starts_as_free_with_50_limit():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.models import Tier
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        snap = QuotaService.snapshot(conn, organization_id="org_default")
        assert snap.tier == Tier.FREE
        assert snap.monthly_hdr_limit == 50
        assert snap.used_in_period == 0
        assert snap.remaining == 50
        assert snap.is_exceeded is False
        assert snap.retention_days == 30
        assert snap.forensic_pdf_enabled is False


# ── PROBE 2: snapshot counts HDRs inserted in current period ───────────────────


def test_snapshot_counts_hdrs_in_period():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        _insert_hdrs(conn, organization_id="org_default", count=10)
        snap = QuotaService.snapshot(conn, organization_id="org_default")
        assert snap.used_in_period == 10
        assert snap.remaining == 40
        assert snap.is_exceeded is False


# ── PROBE 3: enforce raises QuotaExceededError when over limit ─────────────────


def test_enforce_raises_when_limit_exceeded():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.models import QuotaExceededError
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        _insert_hdrs(conn, organization_id="org_default", count=50)
        with pytest.raises(QuotaExceededError) as exc_info:
            QuotaService.enforce(conn, organization_id="org_default")
        snap = exc_info.value.snapshot
        assert snap.used_in_period == 50
        assert snap.is_exceeded is True


# ── PROBE 4: 49 HDRs is under limit; enforce returns snapshot ──────────────────


def test_enforce_passes_when_under_limit():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        _insert_hdrs(conn, organization_id="org_default", count=49)
        snap = QuotaService.enforce(conn, organization_id="org_default")
        assert snap.used_in_period == 49
        assert snap.remaining == 1
        assert snap.is_exceeded is False


# ── PROBE 5: upgrade to PRO removes the limit immediately ──────────────────────


def test_upgrade_to_pro_unblocks():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.models import Tier
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        _insert_hdrs(conn, organization_id="org_default", count=60)
        free_snap = QuotaService.snapshot(conn, organization_id="org_default")
        assert free_snap.is_exceeded is True

        pro_snap = QuotaService.apply_tier_change(
            conn, organization_id="org_default", new_tier=Tier.PRO
        )
        # After tier change: period resets so 60 prior HDRs are in OLD period
        assert pro_snap.tier == Tier.PRO
        assert pro_snap.monthly_hdr_limit is None
        assert pro_snap.is_exceeded is False
        assert pro_snap.remaining is None
        assert pro_snap.retention_days == 365


# ── PROBE 6: downgrade from PRO to FREE re-imposes limit ───────────────────────


def test_downgrade_to_free_imposes_limit():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.models import Tier
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        QuotaService.apply_tier_change(
            conn, organization_id="org_default", new_tier=Tier.PRO
        )
        back = QuotaService.apply_tier_change(
            conn, organization_id="org_default", new_tier=Tier.FREE
        )
        assert back.tier == Tier.FREE
        assert back.monthly_hdr_limit == 50


# ── PROBE 7: explicit period_end is honored ────────────────────────────────────


def test_apply_tier_change_with_explicit_period_end():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.models import Tier
    from app.domain.tier.services import QuotaService

    custom_end = datetime(2027, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    with open_connection(get_settings()) as conn:
        snap = QuotaService.apply_tier_change(
            conn,
            organization_id="org_default",
            new_tier=Tier.TEAM,
            period_end=custom_end,
        )
        assert snap.period_end == custom_end
        assert snap.tier == Tier.TEAM


# ── PROBE 8: unknown org raises ValueError ─────────────────────────────────────


def test_unknown_org_raises():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        with pytest.raises(ValueError, match="Organization not found"):
            QuotaService.snapshot(conn, organization_id="org_does_not_exist")


# ── PROBE 9: TierLimits.for_tier returns correct mapping ───────────────────────


def test_tier_limits_mapping():
    from app.domain.tier.models import Tier, TierLimits

    free = TierLimits.for_tier(Tier.FREE)
    assert free.monthly_hdr_limit == 50
    assert free.retention_days == 30
    assert free.max_users == 1
    assert free.forensic_pdf_enabled is False

    pro = TierLimits.for_tier(Tier.PRO)
    assert pro.monthly_hdr_limit is None
    assert pro.retention_days == 365
    assert pro.forensic_pdf_enabled is True

    team = TierLimits.for_tier(Tier.TEAM)
    assert team.max_users == 10
    assert team.retention_days == 1825

    ent = TierLimits.for_tier(Tier.ENTERPRISE)
    assert ent.monthly_hdr_limit is None
    assert ent.retention_days is None
    assert ent.max_users is None


# ── PROBE 10: usage_pct returns correct fraction ───────────────────────────────


def test_usage_pct_computation():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        _insert_hdrs(conn, organization_id="org_default", count=25)
        snap = QuotaService.snapshot(conn, organization_id="org_default")
        assert snap.usage_pct == pytest.approx(0.5)


# ── PROBE 11: webhook signature verification (correct sig accepted) ────────────


def test_webhook_signature_correct():
    import hashlib
    import hmac

    from app.domain.tier.api import _verify_webhook_signature

    secret = "x" * 64
    body = b'{"event":"tier_changed","organization_id":"org_test","tier":"pro"}'
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert _verify_webhook_signature(secret, body, expected) is True
    assert _verify_webhook_signature(secret, body, "sha256=" + expected) is True


# ── PROBE 12: webhook signature verification (bad sig rejected) ────────────────


def test_webhook_signature_bad():
    from app.domain.tier.api import _verify_webhook_signature

    secret = "x" * 64
    body = b'{"event":"tier_changed"}'
    assert _verify_webhook_signature(secret, body, "wrong_signature") is False
    assert _verify_webhook_signature(secret, body, None) is False
    assert _verify_webhook_signature(secret, body, "") is False


# ── PROBE 13: HDRs from other orgs don't count against this org's quota ────────


def test_tenant_isolation_in_quota():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.services import QuotaService
    from app.domain.user.repository import UserRepository

    with open_connection(get_settings()) as conn:
        UserRepository.ensure_organization(
            conn, organization_id="org_other", name="Outra Org"
        )
        _insert_hdrs(conn, organization_id="org_other", count=40)
        _insert_hdrs(conn, organization_id="org_default", count=10)
        snap_default = QuotaService.snapshot(conn, organization_id="org_default")
        snap_other = QuotaService.snapshot(conn, organization_id="org_other")
        assert snap_default.used_in_period == 10
        assert snap_other.used_in_period == 40
        assert snap_other.tier.value == "free"  # default tier for new orgs


# ── PROBE 14: HDRs created OUTSIDE current period not counted ──────────────────


def test_old_period_hdrs_excluded():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.services import QuotaService

    old_ts = datetime.now(timezone.utc) - timedelta(days=45)
    with open_connection(get_settings()) as conn:
        _insert_hdrs(conn, organization_id="org_default", count=30, when=old_ts)
        snap = QuotaService.snapshot(conn, organization_id="org_default")
        # Old HDRs are outside the period (period_start was just set by snapshot
        # or by org init); used should be 0
        assert snap.used_in_period == 0


# ── PROBE 15: rollover_period resets the counter for a new month ──────────────


def test_rollover_resets_counter():
    _fresh_db()
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.domain.tier.repository import TierRepository
    from app.domain.tier.services import QuotaService

    with open_connection(get_settings()) as conn:
        _insert_hdrs(conn, organization_id="org_default", count=40)
        snap_before = QuotaService.snapshot(conn, organization_id="org_default")
        assert snap_before.used_in_period == 40

        # Manually rollover (simulates passage of time past period_end)
        new_start = datetime.now(timezone.utc) + timedelta(seconds=1)
        TierRepository.rollover_period(
            conn, organization_id="org_default", new_period_start=new_start
        )
        snap_after = QuotaService.snapshot(conn, organization_id="org_default")
        assert snap_after.used_in_period == 0
        assert snap_after.remaining == 50
