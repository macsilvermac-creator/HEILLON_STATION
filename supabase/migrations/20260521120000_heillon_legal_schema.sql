-- Heillon Legal — schema Postgres (equivalente às migrações SQLite 001–007)
-- Aplicar com: supabase db push (projeto ligado) ou SQL Editor no dashboard

-- Histórico de migrações (espelha apply_migrations local)
CREATE TABLE IF NOT EXISTS migration_history (
    id BIGSERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 001 — HDR ledger
CREATE TABLE IF NOT EXISTS hdrs (
    hdr_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    previous_hdr TEXT,
    hdr_type TEXT NOT NULL,
    timestamp_iso TIMESTAMPTZ NOT NULL,
    canonical_hash TEXT NOT NULL,
    payload JSONB NOT NULL,
    organization_id TEXT NOT NULL DEFAULT 'org_default'
);

CREATE INDEX IF NOT EXISTS idx_hdr_mission ON hdrs (mission_id);
CREATE INDEX IF NOT EXISTS idx_hdr_previous ON hdrs (previous_hdr);
CREATE INDEX IF NOT EXISTS idx_hdr_type ON hdrs (hdr_type);
CREATE INDEX IF NOT EXISTS idx_hdr_ts ON hdrs (timestamp_iso);
CREATE INDEX IF NOT EXISTS idx_hdr_organization ON hdrs (organization_id);

-- 002 — Missões EASY
CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    authorized_agents_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    dag_json JSONB NOT NULL,
    normative_json JSONB,
    status TEXT NOT NULL DEFAULT 'pending',
    estimated_cost_gas DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    approved_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    hdrs_generated_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    mission_plan_snapshot JSONB NOT NULL,
    organization_id TEXT NOT NULL DEFAULT 'org_default'
);

CREATE INDEX IF NOT EXISTS idx_missions_created ON missions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions (status);
CREATE INDEX IF NOT EXISTS idx_missions_organization ON missions (organization_id);

-- 004 — Multi-tenant + identidade
CREATE TABLE IF NOT EXISTS organizations (
    organization_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    organization_id TEXT NOT NULL REFERENCES organizations (organization_id),
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_org ON users (organization_id);

INSERT INTO organizations (organization_id, name, settings_json, created_at)
VALUES ('org_default', 'Organização Demo', '{}'::jsonb, NOW())
ON CONFLICT (organization_id) DO NOTHING;

-- 003 + 005 — Pacotes forenses
CREATE TABLE IF NOT EXISTS forensic_packages (
    package_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    status TEXT NOT NULL,
    manifest_json JSONB NOT NULL,
    integrity_hash TEXT NOT NULL,
    pdf_path TEXT NOT NULL,
    json_chain_path TEXT NOT NULL,
    pdf_checksum TEXT NOT NULL,
    json_chain_checksum TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by TEXT NOT NULL,
    verification_url_snapshot TEXT NOT NULL,
    signature_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_forensic_pkg_mission ON forensic_packages (mission_id);

-- 006 — Agent configs (soberania de modelos)
CREATE TABLE IF NOT EXISTS agent_configs (
    id BIGSERIAL PRIMARY KEY,
    agent_id TEXT NOT NULL,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    source TEXT NOT NULL DEFAULT 'stub',
    model_name TEXT,
    api_key_encrypted TEXT,
    api_base_url TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (agent_id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_configs_org ON agent_configs (organization_id);

-- 007 — Push tokens (PWA)
CREATE TABLE IF NOT EXISTS mobile_push_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    subscription_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS: activar numa fase posterior com políticas por organization_id
-- (o backend MVP usa a connection string postgres = bypass RLS)

COMMENT ON SCHEMA public IS 'Heillon Legal MVP — Postgres via Supabase';
