BEGIN;

CREATE TABLE IF NOT EXISTS agent_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    source TEXT NOT NULL DEFAULT 'stub',
    model_name TEXT,
    api_key_encrypted TEXT,
    api_base_url TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE (agent_id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_configs_org ON agent_configs (organization_id);

COMMIT;
