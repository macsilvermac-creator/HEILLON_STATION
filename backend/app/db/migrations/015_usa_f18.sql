-- Migration 015 — USA regulatory compliance (Fase 18)
-- Covers: Colorado AI Act SB 205 (2024), CCPA/CPRA, ABA Model Rules, NIST AI RMF 1.0

-- Colorado AI Act SB 205 (effective Feb 2026)
-- High-risk AI systems in employment, education, financial, housing, insurance,
-- healthcare and criminal justice contexts
CREATE TABLE IF NOT EXISTS colorado_ai_records (
    record_id           TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    ai_system_name      TEXT NOT NULL,
    ai_system_version   TEXT NOT NULL DEFAULT '1.0',
    developer_name      TEXT NOT NULL DEFAULT '',
    deployer_name       TEXT NOT NULL DEFAULT '',

    -- Risk tier
    risk_tier           TEXT NOT NULL DEFAULT 'limited',
        -- high | limited
    high_risk_category  TEXT,
        -- employment | education | financial_services | housing | insurance
        -- healthcare | criminal_justice | legal_services | other

    -- Consequential decisions
    consequential_decision_desc TEXT NOT NULL DEFAULT '',

    -- Required assessments (high-risk)
    impact_assessment_done   INTEGER NOT NULL DEFAULT 0,
    impact_assessment_date   TEXT,
    impact_assessment_ref    TEXT,
    bias_audit_done          INTEGER NOT NULL DEFAULT 0,
    bias_audit_date          TEXT,
    bias_audit_provider      TEXT,

    -- Consumer rights
    consumer_notification_text  TEXT NOT NULL DEFAULT '',
    opt_out_mechanism           TEXT NOT NULL DEFAULT '',
    appeal_process_available    INTEGER NOT NULL DEFAULT 0,

    -- Post-deployment monitoring
    monitoring_plan         TEXT NOT NULL DEFAULT '',
    incident_log            TEXT NOT NULL DEFAULT '[]',  -- JSON array

    status                  TEXT NOT NULL DEFAULT 'active',
        -- active | retired | suspended
    created_by              TEXT NOT NULL,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_colorado_org
    ON colorado_ai_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_colorado_tier
    ON colorado_ai_records (risk_tier);

-- CCPA / CPRA consent management (California)
CREATE TABLE IF NOT EXISTS ccpa_consent_records (
    consent_id          TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    consumer_id         TEXT NOT NULL,
    consumer_email      TEXT NOT NULL,
    consumer_state      TEXT NOT NULL DEFAULT 'CA',  -- California or other state

    -- What data / purpose
    data_categories     TEXT NOT NULL DEFAULT '[]',   -- JSON list
    processing_purposes TEXT NOT NULL DEFAULT '[]',   -- JSON list

    consent_type        TEXT NOT NULL DEFAULT 'opt_in',
        -- opt_in | opt_out | do_not_sell | do_not_share | limit_sensitive

    -- CPRA-specific
    sensitive_data_consent         INTEGER NOT NULL DEFAULT 0,
    automated_decision_consent     INTEGER NOT NULL DEFAULT 0,
    sale_of_personal_info_consent  INTEGER NOT NULL DEFAULT 0,
    sharing_for_cross_context      INTEGER NOT NULL DEFAULT 0,

    -- Record
    consent_text        TEXT NOT NULL DEFAULT '',
    ip_address          TEXT,
    user_agent          TEXT,

    -- Lifecycle
    status              TEXT NOT NULL DEFAULT 'active',
        -- active | withdrawn | expired
    withdrawn_at        TEXT,
    withdrawal_reason   TEXT,
    expires_at          TEXT,

    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ccpa_org
    ON ccpa_consent_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ccpa_consumer
    ON ccpa_consent_records (consumer_id);

-- ABA Model Rules compliance log
-- Rule 1.1 Competence (tech competence), 1.6 Confidentiality,
-- 3.4 Fairness, 5.3 Supervision of non-lawyers / AI tools
CREATE TABLE IF NOT EXISTS aba_compliance_log (
    log_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    matter_ref          TEXT NOT NULL,
    attorney_id         TEXT NOT NULL,
    attorney_name       TEXT NOT NULL DEFAULT '',

    -- AI tool disclosure
    ai_tool_name        TEXT NOT NULL DEFAULT '',
    ai_tool_version     TEXT NOT NULL DEFAULT '',
    ai_tool_provider    TEXT NOT NULL DEFAULT '',

    -- Rules compliance flags
    rule_11_competence           INTEGER NOT NULL DEFAULT 0,  -- understood limitations
    rule_16_confidentiality      INTEGER NOT NULL DEFAULT 0,  -- data not exposed
    rule_34_fairness             INTEGER NOT NULL DEFAULT 0,  -- no misleading output
    rule_53_supervision          INTEGER NOT NULL DEFAULT 0,  -- reviewed AI output
    client_disclosure_made       INTEGER NOT NULL DEFAULT 0,  -- informed client

    -- State bar notes (varies by state)
    state_bar               TEXT NOT NULL DEFAULT 'CA',
    state_specific_rule_ref TEXT NOT NULL DEFAULT '',
    state_specific_notes    TEXT NOT NULL DEFAULT '',

    -- Output reviewed
    output_reviewed         INTEGER NOT NULL DEFAULT 0,
    review_notes            TEXT NOT NULL DEFAULT '',

    created_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_aba_org
    ON aba_compliance_log (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_aba_attorney
    ON aba_compliance_log (attorney_id);

-- NIST AI RMF 1.0 (2023) alignment records
-- Four core functions: GOVERN, MAP, MEASURE, MANAGE
CREATE TABLE IF NOT EXISTS nist_ai_rmf_records (
    rmf_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    ai_system_ref       TEXT NOT NULL,
    ai_system_name      TEXT NOT NULL DEFAULT '',
    ai_system_version   TEXT NOT NULL DEFAULT '1.0',

    -- GOVERN — culture, policies, accountability
    govern_policies_defined     INTEGER NOT NULL DEFAULT 0,
    govern_roles_assigned       INTEGER NOT NULL DEFAULT 0,
    govern_risk_tolerance_set   INTEGER NOT NULL DEFAULT 0,
    govern_training_completed   INTEGER NOT NULL DEFAULT 0,
    govern_notes                TEXT NOT NULL DEFAULT '',

    -- MAP — context, categorization, risk identification
    map_intended_use            TEXT NOT NULL DEFAULT '',
    map_context_established     INTEGER NOT NULL DEFAULT 0,
    map_risks_identified        TEXT NOT NULL DEFAULT '[]',  -- JSON
    map_stakeholders_consulted  INTEGER NOT NULL DEFAULT 0,
    map_notes                   TEXT NOT NULL DEFAULT '',

    -- MEASURE — analysis, testing, evaluation
    measure_metrics_defined     INTEGER NOT NULL DEFAULT 0,
    measure_testing_completed   INTEGER NOT NULL DEFAULT 0,
    measure_bias_evaluated      INTEGER NOT NULL DEFAULT 0,
    measure_performance_score   REAL,        -- 0.0-1.0
    measure_trustworthiness     INTEGER,     -- 1-5 (NIST AI Trustworthiness scale)
    measure_notes               TEXT NOT NULL DEFAULT '',

    -- MANAGE — prioritization, response, recovery
    manage_risk_responses       TEXT NOT NULL DEFAULT '[]',  -- JSON
    manage_residual_risks       TEXT NOT NULL DEFAULT '[]',  -- JSON
    manage_monitoring_plan      TEXT NOT NULL DEFAULT '',
    manage_incident_plan        TEXT NOT NULL DEFAULT '',
    manage_notes                TEXT NOT NULL DEFAULT '',

    -- Overall
    profile_tier                TEXT NOT NULL DEFAULT 'tier-2',
        -- tier-1 | tier-2 | tier-3 | tier-4 (NIST tiers)
    last_review_at              TEXT,
    next_review_at              TEXT,

    status                      TEXT NOT NULL DEFAULT 'active',
    created_by                  TEXT NOT NULL,
    created_at                  TEXT NOT NULL,
    updated_at                  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_nist_org
    ON nist_ai_rmf_records (organization_id, created_at DESC);

-- ESIGN Act audit log (21 CFR 11 + ESIGN 2000 + UETA 1999)
-- Mandatory audit trail for any electronic signature action
CREATE TABLE IF NOT EXISTS esign_audit_log (
    audit_id        TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',

    -- Link to document_signatures (optional)
    sig_id          TEXT,

    event_type      TEXT NOT NULL,
        -- document_created | invitation_sent | viewed | signed
        -- declined | delegated | voided | completed
    event_sequence  INTEGER NOT NULL DEFAULT 1,

    actor_id        TEXT NOT NULL,
    actor_name      TEXT NOT NULL DEFAULT '',
    actor_email     TEXT NOT NULL,
    actor_ip        TEXT,
    actor_user_agent TEXT,

    document_ref    TEXT NOT NULL DEFAULT '',
    document_hash   TEXT,

    -- Integrity
    event_hash      TEXT NOT NULL,  -- SHA-256 of event data
    event_data      TEXT NOT NULL DEFAULT '{}',  -- JSON

    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_esign_org
    ON esign_audit_log (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_esign_sig
    ON esign_audit_log (sig_id);
CREATE INDEX IF NOT EXISTS idx_esign_doc
    ON esign_audit_log (document_ref);
