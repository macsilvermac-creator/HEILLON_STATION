-- Migration 012: Fase 16 — CNJ Res. 615/2025 + OAB Rec. 001/2024 AI Governance
-- AI risk classification, human approval gates, audit decisions, disclosure records

-- ─── AI Risk Classification ──────────────────────────────────────────────────
-- Per CNJ 615/2025 Art. 4: classify IA systems by risk level before deployment
CREATE TABLE IF NOT EXISTS ai_risk_classifications (
    classification_id   TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    -- System being classified
    system_name         TEXT NOT NULL,
    system_version      TEXT NOT NULL DEFAULT '1.0',
    system_description  TEXT NOT NULL DEFAULT '',
    -- CNJ 615/2025 risk levels: low | medium | high | prohibited
    risk_level          TEXT NOT NULL DEFAULT 'low',
    risk_justification  TEXT NOT NULL DEFAULT '',
    -- OAB Rec. 001/2024 impact areas (comma-separated)
    impact_areas        TEXT NOT NULL DEFAULT '',
    -- Annex mapping (EU AI Act / CNJ cross-reference)
    regulatory_refs     TEXT NOT NULL DEFAULT '[]',  -- JSON array of norms
    -- Lifecycle
    classified_by       TEXT NOT NULL,
    classified_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    reviewed_at         TEXT,
    review_due_at       TEXT,  -- classifications expire after 1 year
    status              TEXT NOT NULL DEFAULT 'active',  -- 'active' | 'superseded' | 'retired'
    -- Metadata
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_ai_risk_org ON ai_risk_classifications(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_risk_level ON ai_risk_classifications(risk_level);
CREATE INDEX IF NOT EXISTS idx_ai_risk_status ON ai_risk_classifications(status);

-- ─── AI Decision Audit Log ────────────────────────────────────────────────────
-- Immutable log of every AI-assisted decision per CNJ 615/2025 Art. 8
CREATE TABLE IF NOT EXISTS ai_decision_logs (
    decision_id         TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    -- Context
    hdr_id              TEXT,   -- linked HDR if applicable
    mission_id          TEXT,
    classification_id   TEXT,   -- linked risk classification
    -- Decision
    decision_type       TEXT NOT NULL,  -- 'analysis' | 'recommendation' | 'classification' | 'generation'
    decision_summary    TEXT NOT NULL DEFAULT '',
    ai_model            TEXT NOT NULL DEFAULT '',
    ai_provider         TEXT NOT NULL DEFAULT '',
    -- Human oversight (CNJ 615/2025 Art. 6: human in the loop)
    human_reviewed      INTEGER NOT NULL DEFAULT 0,  -- 1 = reviewed by human
    human_reviewer_id   TEXT,
    human_decision      TEXT,   -- 'approved' | 'rejected' | 'modified'
    human_notes         TEXT,
    reviewed_at         TEXT,
    -- Disclosure (OAB Rec. 001/2024 Rule 1.6: AI disclosure to client)
    disclosed_to_client INTEGER NOT NULL DEFAULT 0,
    disclosure_method   TEXT,   -- 'written' | 'verbal' | 'automated'
    disclosed_at        TEXT,
    -- Timestamps
    decided_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_ai_decision_org ON ai_decision_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_decision_hdr ON ai_decision_logs(hdr_id);
CREATE INDEX IF NOT EXISTS idx_ai_decision_mission ON ai_decision_logs(mission_id);
CREATE INDEX IF NOT EXISTS idx_ai_decision_reviewed ON ai_decision_logs(human_reviewed);

-- ─── Human Approval Gates ─────────────────────────────────────────────────────
-- Mandatory human review gate for high-risk AI decisions (CNJ 615/2025 Art. 6)
CREATE TABLE IF NOT EXISTS human_approval_gates (
    gate_id             TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    -- Context
    decision_id         TEXT NOT NULL,  -- ai_decision_logs.decision_id
    -- Gate configuration
    gate_type           TEXT NOT NULL DEFAULT 'mandatory',   -- 'mandatory' | 'advisory'
    risk_level          TEXT NOT NULL DEFAULT 'high',
    required_role       TEXT NOT NULL DEFAULT 'advogado',    -- role required to approve
    -- Deadline (CNJ 615/2025: reasonable time — default 48h)
    expires_at          TEXT NOT NULL,
    -- Resolution
    status              TEXT NOT NULL DEFAULT 'pending',     -- 'pending' | 'approved' | 'rejected' | 'expired'
    resolved_by         TEXT,
    resolution_notes    TEXT,
    resolved_at         TEXT,
    -- Metadata
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_gate_org ON human_approval_gates(organization_id);
CREATE INDEX IF NOT EXISTS idx_gate_status ON human_approval_gates(status);
CREATE INDEX IF NOT EXISTS idx_gate_decision ON human_approval_gates(decision_id);

-- ─── AI Disclosure Records ────────────────────────────────────────────────────
-- OAB Rec. 001/2024: lawyers must disclose AI use to clients (Rules 1.1, 1.6, 5.3)
CREATE TABLE IF NOT EXISTS ai_disclosures (
    disclosure_id       TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    -- Who
    lawyer_id           TEXT NOT NULL,
    client_identifier   TEXT NOT NULL,  -- client ref (may be pseudonymised)
    -- What
    ai_systems_used     TEXT NOT NULL DEFAULT '[]',  -- JSON array of system names
    mission_ids         TEXT NOT NULL DEFAULT '[]',  -- JSON array
    disclosure_text     TEXT NOT NULL DEFAULT '',
    -- How
    method              TEXT NOT NULL DEFAULT 'written',  -- 'written' | 'verbal' | 'automated'
    channel             TEXT NOT NULL DEFAULT 'email',    -- 'email' | 'portal' | 'document'
    -- Consent
    client_acknowledged INTEGER NOT NULL DEFAULT 0,
    acknowledged_at     TEXT,
    -- Timestamps
    disclosed_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_disclosure_org ON ai_disclosures(organization_id);
CREATE INDEX IF NOT EXISTS idx_disclosure_lawyer ON ai_disclosures(lawyer_id);
