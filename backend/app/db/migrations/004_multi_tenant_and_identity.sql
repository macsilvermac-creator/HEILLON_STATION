BEGIN;

ALTER TABLE missions ADD COLUMN organization_id TEXT NOT NULL DEFAULT 'org_default';

ALTER TABLE hdrs ADD COLUMN organization_id TEXT NOT NULL DEFAULT 'org_default';

CREATE INDEX IF NOT EXISTS idx_missions_organization ON missions(organization_id);

CREATE INDEX IF NOT EXISTS idx_hdr_organization ON hdrs(organization_id);

CREATE TABLE IF NOT EXISTS organizations (
    organization_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    settings_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);

INSERT OR IGNORE INTO organizations (organization_id, name, settings_json, created_at)
VALUES ('org_default', 'Organização Demo', '{}', CURRENT_TIMESTAMP);

COMMIT;
