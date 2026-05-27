-- API Keys (Fase 27) — long-lived tokens for collectors (browser ext, MCP gw)
--
-- Plaintext key shown ONCE at creation; only SHA-256 hash persisted.
-- Format: heillon_live_<32 random url-safe chars>
-- The `prefix` column stores first 12 chars for visual identification in UI
-- (e.g. "heillon_live_aB3...") without exposing the secret.

BEGIN;

CREATE TABLE IF NOT EXISTS api_keys (
    api_key_id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    last_used_at TEXT,
    revoked_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

COMMIT;
