BEGIN;

ALTER TABLE forensic_packages ADD COLUMN organization_id TEXT NOT NULL DEFAULT 'org_default';

CREATE INDEX IF NOT EXISTS idx_forensic_pkg_org ON forensic_packages(organization_id);

COMMIT;
