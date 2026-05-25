-- Migration 016 — UAE regulatory compliance (Fase 19)
-- Covers: UAE PDPL (Federal Decree-Law 45/2021), UAE AI Ethics Principles,
--         UAE AI Strategy 2031, DIFC Data Protection Law 2020, UAE PASS signatures

-- UAE PDPL consent management
-- Federal Decree-Law No. 45 of 2021 on Personal Data Protection
CREATE TABLE IF NOT EXISTS uae_pdpl_consent (
    consent_id          TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    data_subject_id     TEXT NOT NULL,
    data_subject_name   TEXT NOT NULL,
    data_subject_email  TEXT NOT NULL DEFAULT '',
    data_subject_nationality TEXT NOT NULL DEFAULT '',

    -- What data / purpose
    data_categories     TEXT NOT NULL DEFAULT '[]',   -- JSON
    processing_purposes TEXT NOT NULL DEFAULT '[]',   -- JSON

    legal_basis         TEXT NOT NULL DEFAULT 'consent',
        -- consent | contract | legal_obligation | vital_interests
        -- public_interest | legitimate_interest

    -- PDPL-specific
    sensitive_data_processing  INTEGER NOT NULL DEFAULT 0,
    biometric_data             INTEGER NOT NULL DEFAULT 0,
    health_data                INTEGER NOT NULL DEFAULT 0,
    children_data              INTEGER NOT NULL DEFAULT 0,  -- Under 18
    guardian_consent_obtained  INTEGER NOT NULL DEFAULT 0,  -- If children_data=1

    -- Cross-border transfer (Art. 26 PDPL)
    cross_border_transfer      INTEGER NOT NULL DEFAULT 0,
    transfer_destination_country TEXT,
    transfer_safeguards        TEXT NOT NULL DEFAULT '',
        -- adequacy_decision | standard_contractual_clauses | binding_corporate_rules | consent

    -- DIFC / ADGM (financial free zones have separate data laws)
    difc_jurisdiction          INTEGER NOT NULL DEFAULT 0,
    adgm_jurisdiction          INTEGER NOT NULL DEFAULT 0,

    consent_text        TEXT NOT NULL DEFAULT '',
    ip_address          TEXT,
    language            TEXT NOT NULL DEFAULT 'en',  -- en | ar

    status              TEXT NOT NULL DEFAULT 'active',
        -- active | withdrawn | expired
    withdrawn_at        TEXT,
    withdrawal_reason   TEXT,
    expires_at          TEXT,

    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_uae_pdpl_org
    ON uae_pdpl_consent (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uae_pdpl_subject
    ON uae_pdpl_consent (data_subject_id);

-- UAE AI Governance
-- UAE AI Strategy 2031 + UAE National AI Ethics Guidelines (7 principles)
-- + Dubai AI Seal + DIFC AI Governance
CREATE TABLE IF NOT EXISTS uae_ai_governance (
    gov_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    ai_system_name      TEXT NOT NULL,
    ai_system_version   TEXT NOT NULL DEFAULT '1.0',
    ai_system_purpose   TEXT NOT NULL DEFAULT '',

    -- UAE AI Ethics Principles (7 pillars, 2019 guidelines)
    ethics_human_centered       INTEGER NOT NULL DEFAULT 0,  -- 1. Human-centred
    ethics_fairness             INTEGER NOT NULL DEFAULT 0,  -- 2. Fairness
    ethics_transparency         INTEGER NOT NULL DEFAULT 0,  -- 3. Transparency
    ethics_safety_reliability   INTEGER NOT NULL DEFAULT 0,  -- 4. Safety & Reliability
    ethics_privacy_security     INTEGER NOT NULL DEFAULT 0,  -- 5. Privacy & Security
    ethics_accountability       INTEGER NOT NULL DEFAULT 0,  -- 6. Accountability
    ethics_sustainability       INTEGER NOT NULL DEFAULT 0,  -- 7. Environmental sustainability

    -- UAE AI Seal (awarded by Ministry of AI)
    ai_seal_applied         INTEGER NOT NULL DEFAULT 0,
    ai_seal_reference       TEXT,
    ai_seal_issued_at       TEXT,
    ai_seal_expires_at      TEXT,
    ai_seal_category        TEXT,
        -- government | commercial | research | critical_infrastructure

    -- Sector alignment (UAE AI Strategy priority sectors)
    sector                  TEXT NOT NULL DEFAULT 'legal',
        -- legal | health | transport | space | renewable_energy
        -- water | technology | education | economy | cybersecurity | telecommunications

    -- DIFC compliance (Dubai International Financial Centre)
    difc_compliant          INTEGER NOT NULL DEFAULT 0,
    difc_registration_ref   TEXT,
    difc_dp_law_version     TEXT NOT NULL DEFAULT '2020',

    -- ADGM compliance (Abu Dhabi Global Market)
    adgm_compliant          INTEGER NOT NULL DEFAULT 0,
    adgm_registration_ref   TEXT,

    -- Jurisdiction
    jurisdiction_ae         TEXT NOT NULL DEFAULT 'federal',
        -- federal | dubai | abu_dhabi | sharjah | difc | adgm | dmcc

    -- Risk assessment
    risk_level              TEXT NOT NULL DEFAULT 'medium',
        -- low | medium | high
    risk_assessment_notes   TEXT NOT NULL DEFAULT '',

    status                  TEXT NOT NULL DEFAULT 'active',
    created_by              TEXT NOT NULL,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_uae_gov_org
    ON uae_ai_governance (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uae_gov_seal
    ON uae_ai_governance (ai_seal_applied);

-- UAE PASS signatures
-- UAE PASS is the national digital identity app — equivalent to eIDAS QES level
-- Regulated by UAE Telecommunications and Digital Government Regulatory Authority (TDRA)
CREATE TABLE IF NOT EXISTS uae_pass_signatures (
    sig_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    document_ref        TEXT NOT NULL,
    document_hash       TEXT NOT NULL,  -- SHA-256 (64 hex)
    document_title      TEXT NOT NULL DEFAULT '',

    -- Signatory
    signatory_name      TEXT NOT NULL,
    signatory_email     TEXT NOT NULL,
    signatory_emirates_id TEXT,  -- Emirates ID (784-YYYY-NNNNNNN-C format, optional)
    signatory_mobile    TEXT,

    -- UAE PASS verification
    uae_pass_verified       INTEGER NOT NULL DEFAULT 0,
    uae_pass_identity_level TEXT NOT NULL DEFAULT 'verified',
        -- basic | verified | qualified
    uae_pass_session_ref    TEXT,

    -- Trust Service Provider
    trust_service_provider  TEXT NOT NULL DEFAULT '',
        -- TDRA | Etisalat | DU | ADGM-PKI | DIFC-PKI | custom
    trust_service_level     TEXT NOT NULL DEFAULT 'qualified',
        -- qualified | advanced | basic
    qtsp_country            TEXT NOT NULL DEFAULT 'AE',

    -- Signature
    signature_format        TEXT NOT NULL DEFAULT 'PAdES-LTA',
        -- PAdES-LTA | CAdES-LTA | XAdES-LTA
    signature_level         TEXT NOT NULL DEFAULT 'QES',
        -- QES | AES | SES

    -- Timestamp
    signed_at               TEXT NOT NULL,
    tsa_timestamp           TEXT,
    tsa_provider            TEXT,

    -- HDR linkage
    hdr_id                  TEXT,

    status                  TEXT NOT NULL DEFAULT 'valid',
        -- valid | revoked | expired
    created_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_uae_pass_org
    ON uae_pass_signatures (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uae_pass_hash
    ON uae_pass_signatures (document_hash);
