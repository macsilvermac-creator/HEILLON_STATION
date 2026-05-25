-- Migration 020 — Malpractice Insurance + Compliance Scoring + Colorado SB 26-189
-- Malpractice insurance risk scoring based on AI governance compliance
-- AI compliance certificates for law firms
-- Colorado AI Act SB 26-189 (rewritten May 2026 — replaces SB 205 implementation)
-- CCPA ADMT Regulations (finalized Jul 2025, effective Jan 1, 2027)

-- ── Colorado AI Act SB 26-189 Records ─────────────────────────────────────────
-- Replaces colorado_ai_records from F18 migration 015
-- SB 26-189 signed May 2026: REMOVED duty of care / impact assessment mandate
-- KEPT: consequential decision disclosures, rights to explanation/correct/human review
CREATE TABLE IF NOT EXISTS colorado_sb26189_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',
    ai_system_version TEXT NOT NULL DEFAULT '1.0',

    -- Scope: High-risk AI in consequential decisions
    consequential_decision_type TEXT NOT NULL DEFAULT '',
        -- employment | education | financial_services | housing | insurance
        -- | healthcare | criminal_justice | legal_services | other
    consumers_affected_count INTEGER NOT NULL DEFAULT 0,

    -- Consumer Rights (retained from SB 205, now the core)
    -- 1. Right to know (disclosure before consequential decision)
    disclosure_provided     INTEGER NOT NULL DEFAULT 0,
    disclosure_timing       TEXT NOT NULL DEFAULT '',  -- before/during/after decision
    disclosure_method       TEXT NOT NULL DEFAULT '',  -- email/letter/in-app/etc.

    -- 2. Right to explanation (Art. 9 of SB 26-189)
    explanation_available   INTEGER NOT NULL DEFAULT 0,
    explanation_process     TEXT NOT NULL DEFAULT '',
    explanation_response_days INTEGER NOT NULL DEFAULT 30,

    -- 3. Right to correct data (Art. 10)
    data_correction_available INTEGER NOT NULL DEFAULT 0,
    data_correction_process TEXT NOT NULL DEFAULT '',

    -- 4. Right to human review (Art. 11)
    human_review_available  INTEGER NOT NULL DEFAULT 0,
    human_review_process    TEXT NOT NULL DEFAULT '',
    human_review_response_days INTEGER NOT NULL DEFAULT 30,

    -- 5. Right to opt out (limited to certain categories)
    opt_out_available       INTEGER NOT NULL DEFAULT 0,
    opt_out_categories      TEXT NOT NULL DEFAULT '[]',  -- JSON

    -- Cure Period (90 days from notice before AG enforcement)
    cure_period_days        INTEGER NOT NULL DEFAULT 90,
    ag_notice_received      INTEGER NOT NULL DEFAULT 0,
    ag_notice_date          TEXT,
    cure_completed          INTEGER NOT NULL DEFAULT 0,
    cure_completion_date    TEXT,

    -- Exemptions (SB 26-189 expanded exemptions vs SB 205)
    small_business_exempt   INTEGER NOT NULL DEFAULT 0,  -- <$10M revenue
    open_source_exempt      INTEGER NOT NULL DEFAULT 0,
    national_security_exempt INTEGER NOT NULL DEFAULT 0,

    -- No longer required under SB 26-189 (kept for tracking only)
    legacy_sb205_impact_assessment TEXT,   -- if previously done
    legacy_sb205_bias_audit TEXT,          -- if previously done

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_co_sb26189_org
    ON colorado_sb26189_records (organization_id);
CREATE INDEX IF NOT EXISTS idx_co_sb26189_type
    ON colorado_sb26189_records (consequential_decision_type);

-- ── CCPA ADMT Regulations ─────────────────────────────────────────────────────
-- Automated Decision-Making Technology (ADMT) Regulations
-- Finalized July 24, 2025; effective January 1, 2027
-- CPA §1798.185(a)(16): opt-out + access rights for ADMT
CREATE TABLE IF NOT EXISTS ccpa_admt_records (
    admt_id         TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    -- ADMT Definition Scope
    admt_purpose    TEXT NOT NULL DEFAULT '',
        -- profiling | employment_decisions | credit | housing | insurance
        -- | healthcare | education | legal | public_accommodation | other
    significant_decisions INTEGER NOT NULL DEFAULT 0,  -- Art. 11(e) threshold
    personal_data_used    INTEGER NOT NULL DEFAULT 0,
    california_consumers  INTEGER NOT NULL DEFAULT 0,

    -- Pre-Use Notice (required before ADMT deployment)
    pre_use_notice_provided INTEGER NOT NULL DEFAULT 0,
    pre_use_notice_content  TEXT NOT NULL DEFAULT '',
    notice_delivery_method  TEXT NOT NULL DEFAULT '',

    -- Right to Opt Out (§1798.121 + ADMT Regs)
    opt_out_available       INTEGER NOT NULL DEFAULT 0,
    opt_out_mechanism       TEXT NOT NULL DEFAULT '',
    opt_out_response_days   INTEGER NOT NULL DEFAULT 15,
    global_opt_out_honored  INTEGER NOT NULL DEFAULT 0,  -- GPC signal

    -- Right to Access (§1798.100)
    access_to_admt_logic    INTEGER NOT NULL DEFAULT 0,
    access_process          TEXT NOT NULL DEFAULT '',

    -- Right to Human Review (Art. 11 ADMT Regs)
    human_review_available  INTEGER NOT NULL DEFAULT 0,
    human_review_process    TEXT NOT NULL DEFAULT '',
    human_review_timing     TEXT NOT NULL DEFAULT '',

    -- Risk Assessment (required for certain ADMT uses, Art. 22 Regs)
    risk_assessment_required INTEGER NOT NULL DEFAULT 0,
    risk_assessment_done    INTEGER NOT NULL DEFAULT 0,
    risk_assessment_ref     TEXT,
    cppa_submission_required INTEGER NOT NULL DEFAULT 0,  -- CPPA audit

    -- Contractor/Vendor Agreements
    admt_vendor_agreements  TEXT NOT NULL DEFAULT '[]',  -- JSON list

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ccpa_admt_org
    ON ccpa_admt_records (organization_id);
CREATE INDEX IF NOT EXISTS idx_ccpa_admt_purpose
    ON ccpa_admt_records (admt_purpose, significant_decisions);

-- ── Malpractice Insurance Risk Records ───────────────────────────────────────
-- Insurers are adopting AI compliance scores in premium pricing
-- This table enables Heillon to partner with insurers as compliance attestation
CREATE TABLE IF NOT EXISTS malpractice_insurance_records (
    insurance_id    TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    law_firm_name   TEXT NOT NULL DEFAULT '',
    bar_jurisdiction TEXT NOT NULL DEFAULT '',   -- e.g. CA, NY, federal, global

    -- Policy Details
    insurer_name    TEXT NOT NULL DEFAULT '',
    policy_number   TEXT NOT NULL DEFAULT '',
    policy_start    TEXT,
    policy_end      TEXT,
    coverage_limit_usd REAL,
    current_premium_usd REAL,

    -- AI Risk Factors (used for premium calculation)
    ai_tools_used           INTEGER NOT NULL DEFAULT 0,
    ai_tools_list           TEXT NOT NULL DEFAULT '[]',  -- JSON list
    ai_outputs_filed_in_court INTEGER NOT NULL DEFAULT 0,
    citation_verification_process INTEGER NOT NULL DEFAULT 0,
    hallucination_incidents_12mo INTEGER NOT NULL DEFAULT 0,
    ai_competence_certified INTEGER NOT NULL DEFAULT 0,  -- ABA 1.1 training

    -- Heillon Compliance Score (0-100)
    -- Aggregated from: HDR coverage, citation verification rate, hallucination rate,
    --                  regulatory compliance (GDPR/LGPD/etc.), attorney competence
    heillon_compliance_score INTEGER,
    score_breakdown         TEXT NOT NULL DEFAULT '{}',  -- JSON component scores
    score_date              TEXT,
    score_certified_by      TEXT,   -- Heillon attestation ref

    -- Premium Calculation
    base_risk_factor        REAL,    -- 1.0 = normal; <1.0 = discount; >1.0 = surcharge
    ai_risk_adjustment      REAL,    -- e.g. -0.15 = 15% discount for high compliance
    estimated_discount_pct  REAL,    -- estimated premium reduction %
    insurer_accepted_score  INTEGER NOT NULL DEFAULT 0,

    -- Claims History (AI-related)
    ai_related_claims_count INTEGER NOT NULL DEFAULT 0,
    ai_related_claims_usd   REAL NOT NULL DEFAULT 0,
    last_claim_date         TEXT,

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_malpractice_org
    ON malpractice_insurance_records (organization_id);
CREATE INDEX IF NOT EXISTS idx_malpractice_score
    ON malpractice_insurance_records (heillon_compliance_score);

-- ── Heillon Global Compliance Score ──────────────────────────────────────────
-- Master compliance score across all regulatory frameworks per AI system
-- This is the "trust score" Heillon sells to insurers, auditors, enterprise clients
CREATE TABLE IF NOT EXISTS heillon_compliance_scores (
    score_id        TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    -- Component Scores (0-100 each)
    score_hdr_coverage      INTEGER NOT NULL DEFAULT 0,  -- % decisions with HDR
    score_citation_accuracy INTEGER NOT NULL DEFAULT 0,  -- verified citations %
    score_hallucination     INTEGER NOT NULL DEFAULT 0,  -- inverse of incident rate
    score_lgpd              INTEGER NOT NULL DEFAULT 0,  -- Brazil
    score_gdpr_eu           INTEGER NOT NULL DEFAULT 0,  -- EU
    score_gdpr_uk           INTEGER NOT NULL DEFAULT 0,  -- UK
    score_ccpa              INTEGER NOT NULL DEFAULT 0,  -- California
    score_colorado          INTEGER NOT NULL DEFAULT 0,  -- Colorado
    score_pdpl_uae          INTEGER NOT NULL DEFAULT 0,  -- UAE
    score_pdpa_sg           INTEGER NOT NULL DEFAULT 0,  -- Singapore
    score_privacy_au        INTEGER NOT NULL DEFAULT 0,  -- Australia
    score_pipeda_ca         INTEGER NOT NULL DEFAULT 0,  -- Canada
    score_iso42001          INTEGER NOT NULL DEFAULT 0,  -- AIMS certification
    score_iso27001          INTEGER NOT NULL DEFAULT 0,  -- ISMS
    score_nist_rmf          INTEGER NOT NULL DEFAULT 0,  -- NIST AI RMF
    score_euai_act          INTEGER NOT NULL DEFAULT 0,  -- EU AI Act
    score_attorney_competence INTEGER NOT NULL DEFAULT 0, -- ABA compliance

    -- Weighted Total (0-100)
    total_score             INTEGER NOT NULL DEFAULT 0,
    certification_tier      TEXT NOT NULL DEFAULT 'unrated',
        -- unrated | bronze (<50) | silver (50-74) | gold (75-89) | platinum (90+)

    -- Evidence References
    evidence_bundle         TEXT NOT NULL DEFAULT '{}',  -- JSON: component→evidence_id

    computed_at             TEXT NOT NULL,
    valid_until             TEXT,       -- scores expire after 90 days
    computed_by             TEXT NOT NULL DEFAULT 'system',
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_heillon_score_org
    ON heillon_compliance_scores (organization_id, computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_heillon_score_tier
    ON heillon_compliance_scores (certification_tier);
