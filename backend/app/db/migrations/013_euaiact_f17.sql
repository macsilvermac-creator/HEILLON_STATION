-- Migration 013: Fase 17 — EU AI Act 2024/1689 + eIDAS 2.0 + ISO 27001 Foundation
-- Technical documentation (Annex IV), GDPR DPIA, QES records, ISMS risk register

-- ─── EU AI Act Technical Documentation (Annex IV) ────────────────────────────
-- Per EU AI Act Art. 11 + Annex IV: High-risk AI systems require technical documentation
CREATE TABLE IF NOT EXISTS euai_technical_docs (
    doc_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    -- System identification
    system_name         TEXT NOT NULL,
    system_version      TEXT NOT NULL DEFAULT '1.0',
    system_description  TEXT NOT NULL DEFAULT '',
    -- EU AI Act classification
    risk_category       TEXT NOT NULL DEFAULT 'high',  -- 'unacceptable' | 'high' | 'limited' | 'minimal'
    annex_iii_category  TEXT,       -- Annex III category (e.g., 'administration_justice')
    intended_purpose    TEXT NOT NULL DEFAULT '',
    -- Annex IV sections (structured data)
    general_description TEXT NOT NULL DEFAULT '{}',   -- JSON: {capabilities, limitations, ...}
    training_data       TEXT NOT NULL DEFAULT '{}',   -- JSON: {sources, preprocessing, ...}
    testing_validation  TEXT NOT NULL DEFAULT '{}',   -- JSON: {accuracy, robustness, bias...}
    performance_metrics TEXT NOT NULL DEFAULT '{}',   -- JSON: {precision, recall, F1...}
    human_oversight     TEXT NOT NULL DEFAULT '{}',   -- JSON: {measures, roles, procedures}
    cybersecurity       TEXT NOT NULL DEFAULT '{}',   -- JSON: {standards, controls}
    -- QMS
    conformity_assessed INTEGER NOT NULL DEFAULT 0,
    conformity_date     TEXT,
    notified_body       TEXT,   -- EU notified body if applicable
    -- Lifecycle
    status              TEXT NOT NULL DEFAULT 'draft',  -- 'draft' | 'active' | 'archived'
    created_by          TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_euai_doc_org ON euai_technical_docs(organization_id);
CREATE INDEX IF NOT EXISTS idx_euai_doc_status ON euai_technical_docs(status);

-- ─── GDPR / LGPD DPIA Records ─────────────────────────────────────────────────
-- Data Protection Impact Assessment per GDPR Art. 35 + LGPD Art. 38
CREATE TABLE IF NOT EXISTS dpia_records (
    dpia_id             TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    -- Processing activity
    processing_name     TEXT NOT NULL,
    processing_purpose  TEXT NOT NULL DEFAULT '',
    legal_basis         TEXT NOT NULL DEFAULT 'legitimate_interest',
    data_categories     TEXT NOT NULL DEFAULT '[]',  -- JSON array
    data_subjects       TEXT NOT NULL DEFAULT '[]',  -- JSON array
    -- Risk assessment
    necessity_assessment    TEXT NOT NULL DEFAULT '',
    proportionality_check   TEXT NOT NULL DEFAULT '',
    risks_identified    TEXT NOT NULL DEFAULT '[]',  -- JSON array [{risk, likelihood, impact}]
    mitigations         TEXT NOT NULL DEFAULT '[]',  -- JSON array [{measure, residual_risk}]
    -- DPO consultation
    dpo_consulted       INTEGER NOT NULL DEFAULT 0,
    dpo_opinion         TEXT,
    dpo_consulted_at    TEXT,
    -- Prior consultation with supervisory authority
    prior_consultation  INTEGER NOT NULL DEFAULT 0,
    supervisory_authority TEXT,
    consultation_ref    TEXT,
    -- Status
    status              TEXT NOT NULL DEFAULT 'draft',  -- 'draft' | 'approved' | 'archived'
    approved_by         TEXT,
    approved_at         TEXT,
    review_due_at       TEXT,  -- annual review
    -- Timestamps
    created_by          TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_dpia_org ON dpia_records(organization_id);
CREATE INDEX IF NOT EXISTS idx_dpia_status ON dpia_records(status);

-- ─── eIDAS 2.0 QES Records ────────────────────────────────────────────────────
-- Qualified Electronic Signature tracking per Reg. 2024/1183 (eIDAS 2.0)
CREATE TABLE IF NOT EXISTS eidas_qes_records (
    qes_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    -- Document
    document_type       TEXT NOT NULL,  -- 'contract' | 'court_submission' | 'expert_report' | 'disclosure'
    document_ref        TEXT NOT NULL,  -- internal document ID
    document_hash       TEXT NOT NULL,  -- SHA-256 of signed document
    -- QES details
    signatory_name      TEXT NOT NULL,
    signatory_email     TEXT NOT NULL,
    qtsp_provider       TEXT NOT NULL DEFAULT '',  -- Qualified Trust Service Provider name
    qtsp_country        TEXT NOT NULL DEFAULT 'EU',
    signature_format    TEXT NOT NULL DEFAULT 'PAdES-LTA',  -- 'PAdES-LTA' | 'CAdES-LTA' | 'XAdES-LTA'
    signature_level     TEXT NOT NULL DEFAULT 'QES',  -- 'QES' | 'AES' | 'SES'
    -- EUDI Wallet (eIDAS 2.0 Art. 5a)
    eudi_wallet_used    INTEGER NOT NULL DEFAULT 0,
    eudi_pid_verified   INTEGER NOT NULL DEFAULT 0,  -- PID = Person Identification Data
    -- Timestamp
    signature_timestamp TEXT NOT NULL,
    tsa_provider        TEXT,
    -- Status
    status              TEXT NOT NULL DEFAULT 'valid',  -- 'valid' | 'revoked' | 'expired'
    revocation_reason   TEXT,
    -- Audit
    verified_at         TEXT,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_qes_org ON eidas_qes_records(organization_id);
CREATE INDEX IF NOT EXISTS idx_qes_doc_ref ON eidas_qes_records(document_ref);

-- ─── ISO 27001 ISMS Risk Register ────────────────────────────────────────────
-- Information Security Risk per ISO 27001:2022 Clause 6.1.2
CREATE TABLE IF NOT EXISTS isms_risks (
    risk_id             TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    -- Risk identification
    asset               TEXT NOT NULL,   -- Information asset at risk
    threat              TEXT NOT NULL,   -- Threat description
    vulnerability       TEXT NOT NULL DEFAULT '',
    -- Risk assessment (ISO 27005 likelihood × impact)
    likelihood          INTEGER NOT NULL DEFAULT 2,  -- 1=Rare, 2=Unlikely, 3=Possible, 4=Likely, 5=Almost Certain
    impact              INTEGER NOT NULL DEFAULT 2,  -- 1=Negligible, 2=Minor, 3=Moderate, 4=Major, 5=Catastrophic
    risk_score          INTEGER GENERATED ALWAYS AS (likelihood * impact) STORED,
    risk_level          TEXT NOT NULL DEFAULT 'medium',  -- 'low' | 'medium' | 'high' | 'critical'
    -- ISO 27001:2022 Annex A control reference
    control_ref         TEXT,  -- e.g. 'A.8.1' = Asset Management
    control_description TEXT NOT NULL DEFAULT '',
    treatment_option    TEXT NOT NULL DEFAULT 'mitigate',  -- 'mitigate' | 'accept' | 'transfer' | 'avoid'
    residual_risk       TEXT,
    -- Ownership
    risk_owner          TEXT NOT NULL,
    review_due_at       TEXT,
    status              TEXT NOT NULL DEFAULT 'open',  -- 'open' | 'treated' | 'accepted' | 'closed'
    -- Timestamps
    identified_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_isms_risk_org ON isms_risks(organization_id);
CREATE INDEX IF NOT EXISTS idx_isms_risk_level ON isms_risks(risk_level);
CREATE INDEX IF NOT EXISTS idx_isms_risk_status ON isms_risks(status);
