-- Freemium tiers + quota infrastructure (Fase 26)
--
-- SQLite ALTER TABLE ADD COLUMN does NOT support CURRENT_TIMESTAMP as default,
-- so we use a fixed sentinel ('1970-01-01T00:00:00Z') and let the application
-- layer (TierRepository.get_tier_state) backfill on first read.

BEGIN;

-- 1) organizations: tier metadata
ALTER TABLE organizations ADD COLUMN tier TEXT NOT NULL DEFAULT 'free';
ALTER TABLE organizations ADD COLUMN tier_period_start TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z';
ALTER TABLE organizations ADD COLUMN tier_period_end TEXT;
ALTER TABLE organizations ADD COLUMN tier_updated_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z';

CREATE INDEX IF NOT EXISTS idx_orgs_tier ON organizations(tier);

-- Backfill existing rows with current UTC timestamp (SQLite-compatible expression).
UPDATE organizations
SET tier_period_start = strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
    tier_updated_at   = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
WHERE tier_period_start = '1970-01-01T00:00:00Z';

-- 2) hdrs: server-side created_at for quota counting and retention purge.
--    timestamp_iso remains the HDR's own authoritative timestamp (client-set).
ALTER TABLE hdrs ADD COLUMN created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z';

-- Backfill existing HDRs so retention/quota counts don't break legacy rows.
UPDATE hdrs
SET created_at = COALESCE(NULLIF(timestamp_iso, ''), strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
WHERE created_at = '1970-01-01T00:00:00Z';

CREATE INDEX IF NOT EXISTS idx_hdr_created_at ON hdrs(created_at);
CREATE INDEX IF NOT EXISTS idx_hdr_org_created ON hdrs(organization_id, created_at);

COMMIT;
