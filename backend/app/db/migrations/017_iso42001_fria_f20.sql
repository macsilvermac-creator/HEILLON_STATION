-- Migration 017 — ISO 42001:2023 (AIMS) + EU AI Act FRIA (Fase 20)
-- ISO/IEC 42001:2023: AI Management System — first global AIMS standard
-- FRIA: Fundamental Rights Impact Assessment (EU AI Act Art. 27)

-- ── ISO 42001 AIMS Records ─────────────────────────────────────────────────
-- Models the 9 clauses of ISO 42001:2023
CREATE TABLE IF NOT EXISTS iso42001_aims_records (
    aims_id         TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',
    ai_system_version TEXT NOT NULL DEFAULT '1.0',

    -- Clause 4: Context of the Organization
    c4_internal_issues      TEXT NOT NULL DEFAULT '',   -- key internal issues
    c4_external_issues      TEXT NOT NULL DEFAULT '',   -- key external issues
    c4_interested_parties   TEXT NOT NULL DEFAULT '[]', -- JSON list
    c4_aims_scope           TEXT NOT NULL DEFAULT '',   -- AIMS scope statement
    c4_ai_policy_defined    INTEGER NOT NULL DEFAULT 0,

    -- Clause 5: Leadership
    c5_top_mgmt_commitment  INTEGER NOT NULL DEFAULT 0,
    c5_ai_policy_text       TEXT NOT NULL DEFAULT '',
    c5_roles_defined        INTEGER NOT NULL DEFAULT 0,
    c5_dpo_appointed        INTEGER NOT NULL DEFAULT 0,

    -- Clause 6: Planning
    c6_risks_assessed       INTEGER NOT NULL DEFAULT 0,
    c6_opportunities_noted  INTEGER NOT NULL DEFAULT 0,
    c6_objectives_set       TEXT NOT NULL DEFAULT '[]', -- JSON list
    c6_action_plans         TEXT NOT NULL DEFAULT '[]', -- JSON list

    -- Clause 7: Support
    c7_resources_allocated  INTEGER NOT NULL DEFAULT 0,
    c7_competence_verified  INTEGER NOT NULL DEFAULT 0,
    c7_awareness_training   INTEGER NOT NULL DEFAULT 0,
    c7_documentation_maintained INTEGER NOT NULL DEFAULT 0,

    -- Clause 8: Operation
    c8_operational_controls INTEGER NOT NULL DEFAULT 0,
    c8_ai_system_lifecycle  TEXT NOT NULL DEFAULT '',   -- design→deploy→retire
    c8_data_quality_assured INTEGER NOT NULL DEFAULT 0,
    c8_human_oversight_active INTEGER NOT NULL DEFAULT 0,
    c8_incident_response_plan TEXT NOT NULL DEFAULT '',

    -- Clause 9: Performance Evaluation
    c9_monitoring_metrics   TEXT NOT NULL DEFAULT '{}', -- JSON
    c9_internal_audit_done  INTEGER NOT NULL DEFAULT 0,
    c9_mgmt_review_done     INTEGER NOT NULL DEFAULT 0,
    c9_last_audit_date      TEXT,

    -- Clause 10: Improvement
    c10_nonconformities     TEXT NOT NULL DEFAULT '[]', -- JSON list
    c10_corrective_actions  TEXT NOT NULL DEFAULT '[]', -- JSON list
    c10_continual_improvement_plan TEXT NOT NULL DEFAULT '',

    -- Annex A Controls (selected key controls)
    -- A.2 Policies for AI system development
    annex_a2_dev_policy     INTEGER NOT NULL DEFAULT 0,
    -- A.3 Internal audit function
    annex_a3_internal_audit INTEGER NOT NULL DEFAULT 0,
    -- A.4 AI system impact assessment
    annex_a4_impact_assess  INTEGER NOT NULL DEFAULT 0,
    -- A.5 AI system life cycle
    annex_a5_lifecycle_mgmt INTEGER NOT NULL DEFAULT 0,
    -- A.6 Data management
    annex_a6_data_mgmt      INTEGER NOT NULL DEFAULT 0,
    -- A.7 Data for AI systems
    annex_a7_training_data  INTEGER NOT NULL DEFAULT 0,
    -- A.8 AI system information
    annex_a8_documentation  INTEGER NOT NULL DEFAULT 0,
    -- A.9 Logging
    annex_a9_logging        INTEGER NOT NULL DEFAULT 0,

    -- Certification status
    certification_body      TEXT,
    certification_date      TEXT,
    certificate_number      TEXT,
    certificate_expires_at  TEXT,
    certification_status    TEXT NOT NULL DEFAULT 'not_started',
        -- not_started | gap_analysis | stage1_audit | stage2_audit | certified | surveillance

    -- Overall
    conformity_score        INTEGER,  -- 0-100 computed
    status                  TEXT NOT NULL DEFAULT 'active',
    created_by              TEXT NOT NULL,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_iso42001_org
    ON iso42001_aims_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_iso42001_cert
    ON iso42001_aims_records (certification_status);

-- ISO 42001 Control Implementation Log
CREATE TABLE IF NOT EXISTS iso42001_control_log (
    log_id          TEXT PRIMARY KEY,
    aims_id         TEXT NOT NULL REFERENCES iso42001_aims_records(aims_id),
    control_ref     TEXT NOT NULL,   -- A.2, A.3, ... A.9
    control_name    TEXT NOT NULL DEFAULT '',
    evidence        TEXT NOT NULL DEFAULT '',   -- evidence of implementation
    status          TEXT NOT NULL DEFAULT 'planned',
        -- planned | in_progress | implemented | verified | not_applicable
    verified_by     TEXT,
    verified_at     TEXT,
    created_at      TEXT NOT NULL
);

-- ── EU AI Act FRIA ─────────────────────────────────────────────────────────
-- Fundamental Rights Impact Assessment (Art. 27 + Annex VIII EU AI Act)
-- Required for high-risk AI systems before deployment
CREATE TABLE IF NOT EXISTS fria_assessments (
    fria_id         TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    -- Step 1: Describe the intended purpose and foreseeable uses
    intended_purpose        TEXT NOT NULL DEFAULT '',
    foreseeable_misuse      TEXT NOT NULL DEFAULT '',
    geographic_scope        TEXT NOT NULL DEFAULT '',  -- countries/regions
    population_affected     TEXT NOT NULL DEFAULT '',  -- who is affected

    -- Step 2: Identify relevant fundamental rights under EU Charter
    right_dignity           INTEGER NOT NULL DEFAULT 0,  -- Art. 1 Human dignity
    right_privacy           INTEGER NOT NULL DEFAULT 0,  -- Art. 7-8 Privacy/data
    right_nondiscrimination INTEGER NOT NULL DEFAULT 0,  -- Art. 21 Non-discrimination
    right_fair_trial        INTEGER NOT NULL DEFAULT 0,  -- Art. 47 Effective remedy
    right_presumption       INTEGER NOT NULL DEFAULT 0,  -- Art. 48 Presumption of innocence
    right_labour            INTEGER NOT NULL DEFAULT 0,  -- Art. 31 Fair working conditions
    right_education         INTEGER NOT NULL DEFAULT 0,  -- Art. 14 Education
    right_property          INTEGER NOT NULL DEFAULT 0,  -- Art. 17 Property
    other_rights            TEXT NOT NULL DEFAULT '',

    -- Step 3: Assess impact on identified rights
    impact_severity         TEXT NOT NULL DEFAULT 'low',
        -- low | medium | high | very_high
    impact_likelihood       TEXT NOT NULL DEFAULT 'low',
        -- low | medium | high | certain
    impact_description      TEXT NOT NULL DEFAULT '',
    vulnerable_groups_affected INTEGER NOT NULL DEFAULT 0,
    vulnerable_groups_desc  TEXT NOT NULL DEFAULT '',

    -- Step 4: Mitigation measures
    technical_measures      TEXT NOT NULL DEFAULT '[]',  -- JSON list
    organisational_measures TEXT NOT NULL DEFAULT '[]',  -- JSON list
    transparency_measures   TEXT NOT NULL DEFAULT '[]',  -- JSON list
    human_oversight_measures TEXT NOT NULL DEFAULT '[]', -- JSON list
    residual_risk_level     TEXT NOT NULL DEFAULT 'low',
        -- low | medium | high | unacceptable

    -- Step 5: Conclusion
    deployment_approved     INTEGER NOT NULL DEFAULT 0,
    deployment_conditions   TEXT NOT NULL DEFAULT '',
    review_frequency        TEXT NOT NULL DEFAULT 'annual',
        -- monthly | quarterly | semi_annual | annual

    -- Governance
    assessor_id             TEXT NOT NULL,
    assessor_name           TEXT NOT NULL DEFAULT '',
    dpo_consulted           INTEGER NOT NULL DEFAULT 0,
    legal_reviewed          INTEGER NOT NULL DEFAULT 0,
    approved_by             TEXT,
    approved_at             TEXT,

    status                  TEXT NOT NULL DEFAULT 'draft',
        -- draft | under_review | approved | rejected | archived
    version                 INTEGER NOT NULL DEFAULT 1,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fria_org
    ON fria_assessments (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fria_status
    ON fria_assessments (status);
CREATE INDEX IF NOT EXISTS idx_fria_severity
    ON fria_assessments (impact_severity);
