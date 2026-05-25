-- Migration 019 — APAC + Global Privacy (UK / Canada / Singapore / Australia)
-- UK GDPR + AI Code of Practice (2026)
-- Canada PIPEDA + Bill C-27 (AIDA + CPPA)
-- Singapore PDPA 2012 + PDPC Agentic AI Framework (Jan 2026)
-- Australia Privacy Act 1988 + automated decision amendments (Dec 2026)

-- ── UK GDPR Compliance Records ────────────────────────────────────────────────
-- UK retained GDPR post-Brexit + AI Code of Practice Regulations 2026
CREATE TABLE IF NOT EXISTS uk_gdpr_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    -- UK ICO Registration
    ico_reference   TEXT NOT NULL DEFAULT '',
    ico_registered  INTEGER NOT NULL DEFAULT 0,
    data_protection_fee_paid INTEGER NOT NULL DEFAULT 0,

    -- Lawful Basis (UK GDPR Art. 6)
    lawful_basis    TEXT NOT NULL DEFAULT '',
        -- consent | contract | legal_obligation | vital_interests | public_task | legitimate_interests
    legitimate_interests_assessment TEXT NOT NULL DEFAULT '',

    -- AI-Specific (UK AI Code of Practice 2026)
    ai_code_applicable INTEGER NOT NULL DEFAULT 0,
    transparency_notice_published INTEGER NOT NULL DEFAULT 0,
    human_review_available INTEGER NOT NULL DEFAULT 0,
    profiling_used  INTEGER NOT NULL DEFAULT 0,
    profiling_basis TEXT NOT NULL DEFAULT '',

    -- Data Subject Rights (UK GDPR Chapter III)
    right_access_process    TEXT NOT NULL DEFAULT '',  -- Art. 15 SAR process
    right_erasure_process   TEXT NOT NULL DEFAULT '',  -- Art. 17 right to forget
    right_portability_process TEXT NOT NULL DEFAULT '', -- Art. 20
    right_object_ai         TEXT NOT NULL DEFAULT '',  -- Art. 22 automated decisions

    -- DPO / Representative
    dpo_required    INTEGER NOT NULL DEFAULT 0,
    dpo_name        TEXT NOT NULL DEFAULT '',
    uk_rep_appointed INTEGER NOT NULL DEFAULT 0,
    uk_rep_name     TEXT NOT NULL DEFAULT '',

    -- Transfers (Post-Brexit Adequacy/SCCs)
    eu_transfer_mechanism TEXT NOT NULL DEFAULT '',
        -- adequacy | idta | bcr | derogations | none
    international_transfers TEXT NOT NULL DEFAULT '{}', -- JSON: country→mechanism

    -- DPIA (UK GDPR Art. 35)
    dpia_conducted  INTEGER NOT NULL DEFAULT 0,
    dpia_ref        TEXT,

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_uk_gdpr_org
    ON uk_gdpr_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uk_gdpr_ico
    ON uk_gdpr_records (ico_reference);

-- ── Canada PIPEDA / Bill C-27 (CPPA + AIDA) Records ─────────────────────────
-- PIPEDA: current law. Bill C-27: CPPA (replaces PIPEDA) + AIDA (AI Act)
-- AIDA: High-impact AI systems → impact assessment, mitigation, record-keeping
CREATE TABLE IF NOT EXISTS canada_privacy_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    -- Jurisdiction
    provincial_law  TEXT NOT NULL DEFAULT 'federal',
        -- federal (PIPEDA) | quebec (Law 25) | alberta (PIPA) | bc (PIPA)
    law_25_quebec   INTEGER NOT NULL DEFAULT 0,

    -- PIPEDA / CPPA Consent
    consent_obtained        INTEGER NOT NULL DEFAULT 0,
    consent_form            TEXT NOT NULL DEFAULT '',
    implied_consent_basis   TEXT NOT NULL DEFAULT '',
    withdrawal_mechanism    TEXT NOT NULL DEFAULT '',

    -- Bill C-27 AIDA — Artificial Intelligence and Data Act
    aida_applicable         INTEGER NOT NULL DEFAULT 0,
    high_impact_system      INTEGER NOT NULL DEFAULT 0,
    high_impact_categories  TEXT NOT NULL DEFAULT '[]',  -- JSON: employment/credit/housing/health/justice/etc.
    impact_assessment_done  INTEGER NOT NULL DEFAULT 0,
    impact_assessment_ref   TEXT,
    mitigation_measures     TEXT NOT NULL DEFAULT '[]',  -- JSON list
    incident_reporting_process TEXT NOT NULL DEFAULT '',

    -- Quebec Law 25 (most stringent in Canada)
    q25_privacy_officer     TEXT NOT NULL DEFAULT '',
    q25_privacy_policy_published INTEGER NOT NULL DEFAULT 0,
    q25_pia_required        INTEGER NOT NULL DEFAULT 0,
    q25_pia_done            INTEGER NOT NULL DEFAULT 0,
    q25_72h_breach_report   INTEGER NOT NULL DEFAULT 0,
    q25_portability_enabled INTEGER NOT NULL DEFAULT 0,

    -- OPC Registration / Breach Reporting
    breach_reported_to_opc  INTEGER NOT NULL DEFAULT 0,
    opc_file_number         TEXT,

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_canada_org
    ON canada_privacy_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_canada_aida
    ON canada_privacy_records (aida_applicable, high_impact_system);

-- ── Singapore PDPA + Agentic AI Framework ─────────────────────────────────────
-- PDPA 2012 (amended 2021): consent, notification, access, correction, portability
-- PDPC Model AI Governance Framework 2.0 (2020)
-- PDPC Advisory Guidelines for Agentic AI Systems (Jan 2026)
CREATE TABLE IF NOT EXISTS singapore_pdpa_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    -- PDPA Obligations
    pdpa_dpo_designated     INTEGER NOT NULL DEFAULT 0,
    pdpa_dpo_name           TEXT NOT NULL DEFAULT '',
    pdpa_dpo_registered     INTEGER NOT NULL DEFAULT 0,  -- PDPC registration
    data_protection_policy_published INTEGER NOT NULL DEFAULT 0,
    do_not_call_compliant   INTEGER NOT NULL DEFAULT 0,

    -- Consent & Notification (PDPA Part III + IV)
    consent_purpose_specific INTEGER NOT NULL DEFAULT 0,
    notification_given      INTEGER NOT NULL DEFAULT 0,
    deemed_consent_applied  INTEGER NOT NULL DEFAULT 0,  -- legitimate interests basis

    -- Agentic AI Framework (Jan 2026) — 5 key obligations
    agentic_ai_applicable   INTEGER NOT NULL DEFAULT 0,
    -- 1. Accountability: human oversight mechanisms
    agentic_human_oversight INTEGER NOT NULL DEFAULT 0,
    agentic_oversight_desc  TEXT NOT NULL DEFAULT '',
    -- 2. Transparency: AI agent disclosure to users
    agentic_disclosure      INTEGER NOT NULL DEFAULT 0,
    agentic_disclosure_text TEXT NOT NULL DEFAULT '',
    -- 3. Consent: for autonomous data processing
    agentic_consent_scope   TEXT NOT NULL DEFAULT '',
    -- 4. Data Minimisation: limit agent data access
    agentic_data_minimised  INTEGER NOT NULL DEFAULT 0,
    -- 5. Incident Response: for autonomous agent failures
    agentic_incident_plan   TEXT NOT NULL DEFAULT '',

    -- PDPC Advisory: AI ethics alignment
    pdpc_model_governance_aligned INTEGER NOT NULL DEFAULT 0,
    explainability_implemented INTEGER NOT NULL DEFAULT 0,
    bias_testing_done       INTEGER NOT NULL DEFAULT 0,

    -- Cross-Border Transfers (PDPA Part IX)
    cbdt_countries          TEXT NOT NULL DEFAULT '[]',  -- JSON
    cbdt_contractual_clauses INTEGER NOT NULL DEFAULT 0,
    cbdt_binding_corporate_rules INTEGER NOT NULL DEFAULT 0,
    cbdt_adequacy_applicable INTEGER NOT NULL DEFAULT 0,

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sg_pdpa_org
    ON singapore_pdpa_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sg_agentic
    ON singapore_pdpa_records (agentic_ai_applicable);

-- ── Australia Privacy Act 1988 + AI Amendments ────────────────────────────────
-- Privacy Act 1988 + Privacy Legislation Amendment (Enforcement and Other Measures) 2022
-- Privacy Act Review 2023 — automated decision-making amendments (expected Dec 2026)
-- APPs 1-13 (Australian Privacy Principles)
CREATE TABLE IF NOT EXISTS australia_privacy_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    -- Privacy Act Threshold
    annual_turnover_aud     REAL,   -- threshold AUD 3M for mandatory coverage
    health_service_provider INTEGER NOT NULL DEFAULT 0,  -- always covered
    acts_covered            INTEGER NOT NULL DEFAULT 0,

    -- Australian Privacy Principles (APPs)
    -- APP 1: Open/transparent management
    app1_privacy_policy     INTEGER NOT NULL DEFAULT 0,
    -- APP 5: Notification of collection
    app5_collection_notice  INTEGER NOT NULL DEFAULT 0,
    -- APP 6: Use/disclosure
    app6_primary_purpose_only INTEGER NOT NULL DEFAULT 0,
    -- APP 11: Security
    app11_security_measures TEXT NOT NULL DEFAULT '',
    -- APP 12: Access
    app12_access_process    TEXT NOT NULL DEFAULT '',
    -- APP 13: Correction
    app13_correction_process TEXT NOT NULL DEFAULT '',

    -- AI / Automated Decision-Making (Proposed Amendments Dec 2026)
    adm_used                INTEGER NOT NULL DEFAULT 0,
    adm_description         TEXT NOT NULL DEFAULT '',
    adm_explanation_available INTEGER NOT NULL DEFAULT 0,  -- right to explanation
    adm_human_review_available INTEGER NOT NULL DEFAULT 0,
    adm_opt_out_available   INTEGER NOT NULL DEFAULT 0,
    adm_meaningful_impact   INTEGER NOT NULL DEFAULT 0,    -- triggers obligations

    -- Mandatory Breach Notification (NDB Scheme)
    ndb_scheme_applicable   INTEGER NOT NULL DEFAULT 1,
    breach_assessment_process TEXT NOT NULL DEFAULT '',
    oaic_notification_process TEXT NOT NULL DEFAULT '',   -- 30-day target

    -- Office of the Australian Information Commissioner
    oaic_complaint_process  TEXT NOT NULL DEFAULT '',
    privacy_impact_assessment_done INTEGER NOT NULL DEFAULT 0,

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_au_privacy_org
    ON australia_privacy_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_au_adm
    ON australia_privacy_records (adm_used, adm_meaningful_impact);

-- ── APAC Regional Compliance Dashboard ───────────────────────────────────────
-- Aggregate view of APAC compliance posture per AI system
CREATE TABLE IF NOT EXISTS apac_compliance_summary (
    summary_id      TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    -- Coverage (FK to each national record)
    uk_record_id    TEXT REFERENCES uk_gdpr_records(record_id),
    canada_record_id TEXT REFERENCES canada_privacy_records(record_id),
    singapore_record_id TEXT REFERENCES singapore_pdpa_records(record_id),
    australia_record_id TEXT REFERENCES australia_privacy_records(record_id),

    -- Scores (0-100 per jurisdiction)
    uk_score        INTEGER,
    canada_score    INTEGER,
    singapore_score INTEGER,
    australia_score INTEGER,
    global_score    INTEGER,  -- weighted average

    -- Gaps
    open_gaps       TEXT NOT NULL DEFAULT '[]',   -- JSON list of gap descriptions
    critical_gaps   INTEGER NOT NULL DEFAULT 0,

    last_assessed_at TEXT,
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_apac_summary_org
    ON apac_compliance_summary (organization_id);
