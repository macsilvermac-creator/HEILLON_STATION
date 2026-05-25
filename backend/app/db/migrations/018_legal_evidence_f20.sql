-- Migration 018 — Legal Evidence AI (Federal Rule 707 + Hallucination Detection)
-- USA: Federal Rules of Evidence proposed Rule 707 (AI-generated evidence)
-- Global: Citation verification, hallucination detection log, AI competence records

-- ── Federal Rule 707 — AI-Generated Evidence Records ─────────────────────────
-- Proposed FRE Rule 707: AI-generated evidence treated as expert testimony
-- Must disclose AI system, training data, validation, limitations
CREATE TABLE IF NOT EXISTS fre707_evidence_records (
    evidence_id     TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    case_ref        TEXT NOT NULL,        -- case number / matter ref
    court           TEXT NOT NULL DEFAULT '',
    jurisdiction    TEXT NOT NULL DEFAULT 'federal',
        -- federal | state | arbitration | international
    document_ref    TEXT NOT NULL,        -- the AI-generated document
    document_type   TEXT NOT NULL DEFAULT '',
        -- brief | memo | contract | analysis | prediction | other

    -- AI System Disclosure (FRE 702 standard applied to AI)
    ai_system_name  TEXT NOT NULL DEFAULT '',
    ai_system_version TEXT NOT NULL DEFAULT '',
    ai_provider     TEXT NOT NULL DEFAULT '',  -- OpenAI, Anthropic, etc.
    ai_model_id     TEXT NOT NULL DEFAULT '',
    training_data_cutoff TEXT,
    training_data_description TEXT NOT NULL DEFAULT '',

    -- Expert Qualification Analogue (FRE 702(a-d))
    methodology_disclosed    INTEGER NOT NULL DEFAULT 0,   -- (a) sufficient facts
    reliable_principles      INTEGER NOT NULL DEFAULT 0,   -- (b) reliable principles
    principles_applied       INTEGER NOT NULL DEFAULT 0,   -- (c) applied to facts
    opinion_not_speculative  INTEGER NOT NULL DEFAULT 0,   -- (d) not merely speculative

    -- Validation & Testing
    validation_method       TEXT NOT NULL DEFAULT '',
    error_rate_known        INTEGER NOT NULL DEFAULT 0,
    error_rate_value        REAL,           -- e.g. 0.03 = 3%
    peer_reviewed           INTEGER NOT NULL DEFAULT 0,
    human_attorney_reviewed INTEGER NOT NULL DEFAULT 0,
    human_reviewer_id       TEXT,

    -- Admissibility Assessment
    daubert_analysis        TEXT NOT NULL DEFAULT '',   -- Daubert/Kumho analysis
    admissibility_opinion   TEXT NOT NULL DEFAULT 'pending',
        -- pending | admissible | conditional | inadmissible
    admissibility_conditions TEXT NOT NULL DEFAULT '',
    opposing_counsel_notified INTEGER NOT NULL DEFAULT 0,
    court_ruling            TEXT,

    -- Chain of Custody
    hdr_id                  TEXT,   -- Heillon Decision Record
    generation_timestamp    TEXT NOT NULL,
    hash_sha256             TEXT NOT NULL DEFAULT '',
    chain_of_custody_intact INTEGER NOT NULL DEFAULT 1,

    status                  TEXT NOT NULL DEFAULT 'draft',
        -- draft | submitted | admitted | excluded | withdrawn
    created_by              TEXT NOT NULL,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fre707_org
    ON fre707_evidence_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fre707_case
    ON fre707_evidence_records (case_ref, court);
CREATE INDEX IF NOT EXISTS idx_fre707_admissibility
    ON fre707_evidence_records (admissibility_opinion);

-- ── Citation Verification Records ────────────────────────────────────────────
-- Track AI citation accuracy — critical after hallucination scandals
-- Mata v. Avianca (2023): $5K fine; multiple cases since
CREATE TABLE IF NOT EXISTS citation_verifications (
    citation_id     TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    document_ref    TEXT NOT NULL,          -- parent document
    case_ref        TEXT NOT NULL DEFAULT '',

    -- Citation Details
    citation_text   TEXT NOT NULL DEFAULT '',   -- full citation as AI wrote it
    citation_type   TEXT NOT NULL DEFAULT 'case',
        -- case | statute | regulation | treatise | article | secondary
    cited_court     TEXT NOT NULL DEFAULT '',
    cited_year      TEXT NOT NULL DEFAULT '',
    reporter        TEXT NOT NULL DEFAULT '',   -- F.3d, S.Ct., etc.
    volume          TEXT NOT NULL DEFAULT '',
    page_start      TEXT NOT NULL DEFAULT '',
    url             TEXT NOT NULL DEFAULT '',

    -- Verification Process
    verified_by     TEXT NOT NULL,          -- attorney / paralegal
    verification_method TEXT NOT NULL DEFAULT 'manual',
        -- manual | westlaw | lexisnexis | fastcase | google_scholar | casetext
    verification_db TEXT NOT NULL DEFAULT '',  -- database used
    verification_date TEXT NOT NULL,

    -- Result
    citation_exists INTEGER NOT NULL DEFAULT 0,   -- does the case exist at all?
    proposition_accurate INTEGER NOT NULL DEFAULT 0, -- does it say what AI claimed?
    quote_accurate  INTEGER NOT NULL DEFAULT 0,   -- is a quoted passage accurate?
    case_still_good_law INTEGER NOT NULL DEFAULT 1, -- not overruled/distinguished?

    -- Hallucination Assessment
    is_hallucination        INTEGER NOT NULL DEFAULT 0,
    hallucination_type      TEXT,
        -- fabricated_citation | wrong_holding | wrong_quote | wrong_year | reversed_outcome
    hallucination_severity  TEXT NOT NULL DEFAULT 'none',
        -- none | minor | significant | critical
    hallucination_notes     TEXT NOT NULL DEFAULT '',

    -- Risk
    filed_with_court        INTEGER NOT NULL DEFAULT 0,
    corrective_action_taken INTEGER NOT NULL DEFAULT 0,
    corrective_action_desc  TEXT NOT NULL DEFAULT '',
    bar_complaint_risk      TEXT NOT NULL DEFAULT 'none',
        -- none | low | medium | high

    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_citation_org
    ON citation_verifications (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_citation_doc
    ON citation_verifications (document_ref);
CREATE INDEX IF NOT EXISTS idx_citation_hallucination
    ON citation_verifications (is_hallucination, hallucination_severity);

-- ── AI Hallucination Incident Log ─────────────────────────────────────────────
-- Global log of AI hallucination incidents — feeds risk analytics
CREATE TABLE IF NOT EXISTS hallucination_incidents (
    incident_id     TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    citation_id     TEXT REFERENCES citation_verifications(citation_id),
    document_ref    TEXT NOT NULL DEFAULT '',
    case_ref        TEXT NOT NULL DEFAULT '',

    -- Incident Details
    incident_type   TEXT NOT NULL DEFAULT 'citation',
        -- citation | fact | statute | ruling | date | party_name | other
    ai_system       TEXT NOT NULL DEFAULT '',
    ai_model        TEXT NOT NULL DEFAULT '',
    original_output TEXT NOT NULL DEFAULT '',   -- what AI said
    correct_info    TEXT NOT NULL DEFAULT '',   -- what is actually true

    -- Impact
    severity        TEXT NOT NULL DEFAULT 'medium',
        -- low | medium | high | critical
    filed_with_court INTEGER NOT NULL DEFAULT 0,
    court_sanction  TEXT,   -- description of any sanction
    financial_impact REAL,  -- USD amount of fine/sanction
    client_notified INTEGER NOT NULL DEFAULT 0,
    bar_reported    INTEGER NOT NULL DEFAULT 0,

    -- Root Cause
    root_cause      TEXT NOT NULL DEFAULT '',
    prevention_measure TEXT NOT NULL DEFAULT '',
    workflow_updated INTEGER NOT NULL DEFAULT 0,

    -- Resolution
    status          TEXT NOT NULL DEFAULT 'open',
        -- open | investigating | resolved | reported
    resolved_at     TEXT,
    resolved_by     TEXT,

    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hallucination_org
    ON hallucination_incidents (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_hallucination_severity
    ON hallucination_incidents (severity, status);

-- ── AI Competence Certificates ────────────────────────────────────────────────
-- Track attorney AI competence (ABA Rule 1.1 + state bar requirements)
-- California, Florida, North Carolina, South Carolina require AI CLE
CREATE TABLE IF NOT EXISTS ai_competence_certificates (
    cert_id         TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    attorney_id     TEXT NOT NULL,
    attorney_name   TEXT NOT NULL DEFAULT '',
    bar_number      TEXT NOT NULL DEFAULT '',
    jurisdiction    TEXT NOT NULL DEFAULT '',   -- CA, FL, NY, federal, etc.

    -- Training Completed
    training_provider   TEXT NOT NULL DEFAULT '',
    training_course     TEXT NOT NULL DEFAULT '',
    cle_credits_earned  REAL NOT NULL DEFAULT 0,
    training_date       TEXT NOT NULL,
    training_topics     TEXT NOT NULL DEFAULT '[]',  -- JSON list

    -- AI Systems Covered
    ai_systems_covered  TEXT NOT NULL DEFAULT '[]',  -- JSON list
    competence_areas    TEXT NOT NULL DEFAULT '[]',  -- research/drafting/analysis/e-discovery
        -- JSON list

    -- Compliance Status
    aba_rule_1_1_compliant  INTEGER NOT NULL DEFAULT 0,
    state_bar_compliant     INTEGER NOT NULL DEFAULT 0,
    renewal_due_date        TEXT,
    continuing_ed_required  INTEGER NOT NULL DEFAULT 0,

    -- Certificate Details
    certificate_number  TEXT NOT NULL DEFAULT '',
    issued_by           TEXT NOT NULL DEFAULT '',
    issued_at           TEXT NOT NULL,
    expires_at          TEXT,
    revoked             INTEGER NOT NULL DEFAULT 0,

    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_aicomp_attorney
    ON ai_competence_certificates (attorney_id, jurisdiction);
CREATE INDEX IF NOT EXISTS idx_aicomp_bar
    ON ai_competence_certificates (bar_number);
