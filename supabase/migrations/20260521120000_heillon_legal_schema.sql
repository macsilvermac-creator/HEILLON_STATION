-- Heillon Legal — schema Postgres (equivalente às migrações SQLite 001–007)
-- Aplicar com: supabase db push (projeto ligado) ou SQL Editor no dashboard

-- Histórico de migrações (espelha apply_migrations local)
CREATE TABLE IF NOT EXISTS migration_history (
    id BIGSERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 001 — HDR ledger (+ 021: created_at server-side para quota/retention)
CREATE TABLE IF NOT EXISTS hdrs (
    hdr_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    previous_hdr TEXT,
    hdr_type TEXT NOT NULL,
    timestamp_iso TIMESTAMPTZ NOT NULL,
    canonical_hash TEXT NOT NULL,
    payload JSONB NOT NULL,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hdr_mission ON hdrs (mission_id);
CREATE INDEX IF NOT EXISTS idx_hdr_previous ON hdrs (previous_hdr);
CREATE INDEX IF NOT EXISTS idx_hdr_type ON hdrs (hdr_type);
CREATE INDEX IF NOT EXISTS idx_hdr_ts ON hdrs (timestamp_iso);
CREATE INDEX IF NOT EXISTS idx_hdr_organization ON hdrs (organization_id);
CREATE INDEX IF NOT EXISTS idx_hdr_created_at ON hdrs (created_at);
CREATE INDEX IF NOT EXISTS idx_hdr_org_created ON hdrs (organization_id, created_at);

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

-- 003 + 005 + 008 — Pacotes forenses
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
    signature_path TEXT,
    organization_id TEXT NOT NULL DEFAULT 'org_default'
);

CREATE INDEX IF NOT EXISTS idx_forensic_pkg_mission ON forensic_packages (mission_id);
CREATE INDEX IF NOT EXISTS idx_forensic_pkg_org ON forensic_packages (organization_id);

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


-- =====================================================================
-- PARIDADE Postgres das migracoes SQLite 010-022 (gerado por script).
-- FTS5/triggers omitidos (Postgres usa fallback LIKE/ILIKE no app).
-- Tipos conservadores: TEXT/INTEGER preservados (timestamps ISO em TEXT).
-- =====================================================================

-- ===== 009_normative_fts.sql -- base table apenas, FTS5/triggers omitidos =====
CREATE TABLE IF NOT EXISTS normative_rules (
    rule_id             TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    description         TEXT NOT NULL,
    category            TEXT NOT NULL,
    condition_text      TEXT NOT NULL,
    action_on_violation TEXT NOT NULL,
    priority            INTEGER NOT NULL DEFAULT 50,
    enabled             INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT NOT NULL DEFAULT to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')
);

-- ===== 010_privacy_f14.sql =====
CREATE TABLE IF NOT EXISTS ripd_reports (
    ripd_id          TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    created_by       TEXT NOT NULL,   
    
    title            TEXT NOT NULL,
    processing_type  TEXT NOT NULL,   
    legal_basis      TEXT NOT NULL,   
    purpose          TEXT NOT NULL,
    data_categories  TEXT NOT NULL,   
    data_lifecycle   TEXT NOT NULL,   
    recipients       TEXT NOT NULL,   
    risks_identified TEXT NOT NULL,   
    safeguards       TEXT NOT NULL,   
    dpo_name         TEXT NOT NULL DEFAULT '',
    dpo_email        TEXT NOT NULL DEFAULT '',
    
    status           TEXT NOT NULL DEFAULT 'draft',  
    pdf_path         TEXT,            
    pdf_checksum     TEXT,
    created_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    approved_at      TEXT,
    approved_by      TEXT
);
CREATE INDEX IF NOT EXISTS idx_ripd_org ON ripd_reports(organization_id);
CREATE INDEX IF NOT EXISTS idx_ripd_created ON ripd_reports(created_at);
CREATE TABLE IF NOT EXISTS dpo_requests (
    request_id       TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    
    requester_name   TEXT NOT NULL,
    requester_email  TEXT NOT NULL,
    requester_cpf    TEXT,            
    
    request_type     TEXT NOT NULL,   
    description      TEXT NOT NULL,
    
    status           TEXT NOT NULL DEFAULT 'pending',  
    assigned_to      TEXT,            
    response_notes   TEXT,
    
    created_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    due_at           TEXT NOT NULL,   
    completed_at     TEXT,
    
    ip_address       TEXT,
    user_agent       TEXT
);
CREATE INDEX IF NOT EXISTS idx_dpo_org ON dpo_requests(organization_id);
CREATE INDEX IF NOT EXISTS idx_dpo_email ON dpo_requests(requester_email);
CREATE INDEX IF NOT EXISTS idx_dpo_status ON dpo_requests(status);
CREATE INDEX IF NOT EXISTS idx_dpo_due ON dpo_requests(due_at);
CREATE TABLE IF NOT EXISTS access_logs (
    log_id           TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    user_id          TEXT,
    log_type         TEXT NOT NULL,   
    event_type       TEXT NOT NULL,   
    resource         TEXT,            
    ip_address       TEXT NOT NULL,
    user_agent       TEXT,
    response_code    INTEGER,
    
    created_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    expires_at       TEXT NOT NULL,   
    
    judicial_hold    INTEGER NOT NULL DEFAULT 0  
);
CREATE INDEX IF NOT EXISTS idx_access_logs_org ON access_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_expires ON access_logs(expires_at);
CREATE INDEX IF NOT EXISTS idx_access_logs_type ON access_logs(log_type);
CREATE TABLE IF NOT EXISTS security_incidents (
    incident_id        TEXT PRIMARY KEY,
    organization_id    TEXT NOT NULL DEFAULT 'org_default',
    
    detected_at        TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    detected_by        TEXT NOT NULL,   
    
    category           TEXT NOT NULL,   
    description        TEXT NOT NULL,
    severity           TEXT NOT NULL DEFAULT 'medium',  
    
    affected_subjects_count  INTEGER NOT NULL DEFAULT 0,
    affected_data_types      TEXT NOT NULL DEFAULT '[]',  
    potential_harm           TEXT,
    
    status             TEXT NOT NULL DEFAULT 'detected',
    
    
    anpd_notification_due_at  TEXT,    
    anpd_notified_at          TEXT,
    anpd_notification_ref     TEXT,    
    
    subjects_notified_at      TEXT,
    notification_method       TEXT,
    
    containment_measures      TEXT,
    remediation_plan          TEXT,
    
    created_at         TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    updated_at         TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    closed_at          TEXT,
    closed_by          TEXT,
    retain_until       TEXT NOT NULL  
);
CREATE INDEX IF NOT EXISTS idx_incidents_org ON security_incidents(organization_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_detected ON security_incidents(detected_at);
CREATE TABLE IF NOT EXISTS consent_records (
    consent_id       TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    
    purpose          TEXT NOT NULL,   
    legal_basis      TEXT NOT NULL,   
    
    granted          INTEGER NOT NULL DEFAULT 0,   
    
    granted_at       TEXT,
    revoked_at       TEXT,
    version          TEXT NOT NULL DEFAULT '1.0',  
    ip_address       TEXT,
    user_agent       TEXT,
    created_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    updated_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_consent_user_purpose ON consent_records(user_id, purpose);
CREATE INDEX IF NOT EXISTS idx_consent_user ON consent_records(user_id);
CREATE INDEX IF NOT EXISTS idx_consent_org ON consent_records(organization_id);

-- ===== 011_icp_f15.sql =====
CREATE TABLE IF NOT EXISTS icp_signatures (
    sig_id           TEXT PRIMARY KEY,
    entity_type      TEXT NOT NULL,  
    entity_id        TEXT NOT NULL,  
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    
    cert_subject     TEXT NOT NULL,
    cert_issuer      TEXT NOT NULL,
    cert_serial      TEXT NOT NULL,
    cert_not_before  TEXT NOT NULL,
    cert_not_after   TEXT NOT NULL,
    cert_type        TEXT NOT NULL DEFAULT 'A1',  
    icp_brasil       INTEGER NOT NULL DEFAULT 0,  
    
    signature_type   TEXT NOT NULL DEFAULT 'CAdES-BES',  
    signature_b64    TEXT NOT NULL,  
    signed_hash      TEXT NOT NULL,  
    signed_at        TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    
    tsa_token_b64    TEXT,           
    tsa_provider     TEXT,
    
    pdfa3_path       TEXT,           
    pdfa3_checksum   TEXT,
    
    signed_by        TEXT NOT NULL,  
    created_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_icp_sig_entity ON icp_signatures(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_icp_sig_org ON icp_signatures(organization_id);
CREATE INDEX IF NOT EXISTS idx_icp_sig_cert_serial ON icp_signatures(cert_serial);
CREATE TABLE IF NOT EXISTS icp_verifications (
    verify_id         TEXT PRIMARY KEY,
    hdr_id            TEXT NOT NULL,
    organization_id   TEXT NOT NULL DEFAULT 'org_default',
    
    icp_verified      INTEGER NOT NULL DEFAULT 0,  
    signer_name       TEXT,
    signer_cpf_cnpj   TEXT,
    cert_issuer       TEXT,
    cert_serial       TEXT,
    cert_type         TEXT,  
    signing_time      TEXT,
    signature_valid   INTEGER NOT NULL DEFAULT 0,
    cert_chain_valid  INTEGER NOT NULL DEFAULT 0,
    
    details_json      TEXT NOT NULL DEFAULT '{}',
    
    verified_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    verified_by       TEXT  
);
CREATE INDEX IF NOT EXISTS idx_icp_verify_hdr ON icp_verifications(hdr_id);
CREATE INDEX IF NOT EXISTS idx_icp_verify_org ON icp_verifications(organization_id);
CREATE TABLE IF NOT EXISTS pdfa3_packages (
    pdfa3_id         TEXT PRIMARY KEY,
    package_id       TEXT NOT NULL,   
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    
    pdf_path         TEXT NOT NULL,
    pdf_checksum     TEXT NOT NULL,   
    pdf_version      TEXT NOT NULL DEFAULT 'A-3',
    
    attachments_json TEXT NOT NULL DEFAULT '[]',  
    
    is_signed        INTEGER NOT NULL DEFAULT 0,
    sig_id           TEXT,            
    
    created_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    created_by       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pdfa3_package ON pdfa3_packages(package_id);

-- ===== 012_governance_f16.sql =====
CREATE TABLE IF NOT EXISTS ai_risk_classifications (
    classification_id   TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    
    system_name         TEXT NOT NULL,
    system_version      TEXT NOT NULL DEFAULT '1.0',
    system_description  TEXT NOT NULL DEFAULT '',
    
    risk_level          TEXT NOT NULL DEFAULT 'low',
    risk_justification  TEXT NOT NULL DEFAULT '',
    
    impact_areas        TEXT NOT NULL DEFAULT '',
    
    regulatory_refs     TEXT NOT NULL DEFAULT '[]',  
    
    classified_by       TEXT NOT NULL,
    classified_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    reviewed_at         TEXT,
    review_due_at       TEXT,  
    status              TEXT NOT NULL DEFAULT 'active',  
    
    created_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_ai_risk_org ON ai_risk_classifications(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_risk_level ON ai_risk_classifications(risk_level);
CREATE INDEX IF NOT EXISTS idx_ai_risk_status ON ai_risk_classifications(status);
CREATE TABLE IF NOT EXISTS ai_decision_logs (
    decision_id         TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    
    hdr_id              TEXT,   
    mission_id          TEXT,
    classification_id   TEXT,   
    
    decision_type       TEXT NOT NULL,  
    decision_summary    TEXT NOT NULL DEFAULT '',
    ai_model            TEXT NOT NULL DEFAULT '',
    ai_provider         TEXT NOT NULL DEFAULT '',
    
    human_reviewed      INTEGER NOT NULL DEFAULT 0,  
    human_reviewer_id   TEXT,
    human_decision      TEXT,   
    human_notes         TEXT,
    reviewed_at         TEXT,
    
    disclosed_to_client INTEGER NOT NULL DEFAULT 0,
    disclosure_method   TEXT,   
    disclosed_at        TEXT,
    
    decided_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    created_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_ai_decision_org ON ai_decision_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_decision_hdr ON ai_decision_logs(hdr_id);
CREATE INDEX IF NOT EXISTS idx_ai_decision_mission ON ai_decision_logs(mission_id);
CREATE INDEX IF NOT EXISTS idx_ai_decision_reviewed ON ai_decision_logs(human_reviewed);
CREATE TABLE IF NOT EXISTS human_approval_gates (
    gate_id             TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    
    decision_id         TEXT NOT NULL,  
    
    gate_type           TEXT NOT NULL DEFAULT 'mandatory',   
    risk_level          TEXT NOT NULL DEFAULT 'high',
    required_role       TEXT NOT NULL DEFAULT 'advogado',    
    
    expires_at          TEXT NOT NULL,
    
    status              TEXT NOT NULL DEFAULT 'pending',     
    resolved_by         TEXT,
    resolution_notes    TEXT,
    resolved_at         TEXT,
    
    created_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_gate_org ON human_approval_gates(organization_id);
CREATE INDEX IF NOT EXISTS idx_gate_status ON human_approval_gates(status);
CREATE INDEX IF NOT EXISTS idx_gate_decision ON human_approval_gates(decision_id);
CREATE TABLE IF NOT EXISTS ai_disclosures (
    disclosure_id       TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    
    lawyer_id           TEXT NOT NULL,
    client_identifier   TEXT NOT NULL,  
    
    ai_systems_used     TEXT NOT NULL DEFAULT '[]',  
    mission_ids         TEXT NOT NULL DEFAULT '[]',  
    disclosure_text     TEXT NOT NULL DEFAULT '',
    
    method              TEXT NOT NULL DEFAULT 'written',  
    channel             TEXT NOT NULL DEFAULT 'email',    
    
    client_acknowledged INTEGER NOT NULL DEFAULT 0,
    acknowledged_at     TEXT,
    
    disclosed_at        TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    created_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_disclosure_org ON ai_disclosures(organization_id);
CREATE INDEX IF NOT EXISTS idx_disclosure_lawyer ON ai_disclosures(lawyer_id);

-- ===== 013_euaiact_f17.sql =====
CREATE TABLE IF NOT EXISTS euai_technical_docs (
    doc_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    
    system_name         TEXT NOT NULL,
    system_version      TEXT NOT NULL DEFAULT '1.0',
    system_description  TEXT NOT NULL DEFAULT '',
    
    risk_category       TEXT NOT NULL DEFAULT 'high',  
    annex_iii_category  TEXT,       
    intended_purpose    TEXT NOT NULL DEFAULT '',
    
    general_description TEXT NOT NULL DEFAULT '{}',   
    training_data       TEXT NOT NULL DEFAULT '{}',   
    testing_validation  TEXT NOT NULL DEFAULT '{}',   
    performance_metrics TEXT NOT NULL DEFAULT '{}',   
    human_oversight     TEXT NOT NULL DEFAULT '{}',   
    cybersecurity       TEXT NOT NULL DEFAULT '{}',   
    
    conformity_assessed INTEGER NOT NULL DEFAULT 0,
    conformity_date     TEXT,
    notified_body       TEXT,   
    
    status              TEXT NOT NULL DEFAULT 'draft',  
    created_by          TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    updated_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_euai_doc_org ON euai_technical_docs(organization_id);
CREATE INDEX IF NOT EXISTS idx_euai_doc_status ON euai_technical_docs(status);
CREATE TABLE IF NOT EXISTS dpia_records (
    dpia_id             TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    
    processing_name     TEXT NOT NULL,
    processing_purpose  TEXT NOT NULL DEFAULT '',
    legal_basis         TEXT NOT NULL DEFAULT 'legitimate_interest',
    data_categories     TEXT NOT NULL DEFAULT '[]',  
    data_subjects       TEXT NOT NULL DEFAULT '[]',  
    
    necessity_assessment    TEXT NOT NULL DEFAULT '',
    proportionality_check   TEXT NOT NULL DEFAULT '',
    risks_identified    TEXT NOT NULL DEFAULT '[]',  
    mitigations         TEXT NOT NULL DEFAULT '[]',  
    
    dpo_consulted       INTEGER NOT NULL DEFAULT 0,
    dpo_opinion         TEXT,
    dpo_consulted_at    TEXT,
    
    prior_consultation  INTEGER NOT NULL DEFAULT 0,
    supervisory_authority TEXT,
    consultation_ref    TEXT,
    
    status              TEXT NOT NULL DEFAULT 'draft',  
    approved_by         TEXT,
    approved_at         TEXT,
    review_due_at       TEXT,  
    
    created_by          TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    updated_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_dpia_org ON dpia_records(organization_id);
CREATE INDEX IF NOT EXISTS idx_dpia_status ON dpia_records(status);
CREATE TABLE IF NOT EXISTS eidas_qes_records (
    qes_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    
    document_type       TEXT NOT NULL,  
    document_ref        TEXT NOT NULL,  
    document_hash       TEXT NOT NULL,  
    
    signatory_name      TEXT NOT NULL,
    signatory_email     TEXT NOT NULL,
    qtsp_provider       TEXT NOT NULL DEFAULT '',  
    qtsp_country        TEXT NOT NULL DEFAULT 'EU',
    signature_format    TEXT NOT NULL DEFAULT 'PAdES-LTA',  
    signature_level     TEXT NOT NULL DEFAULT 'QES',  
    
    eudi_wallet_used    INTEGER NOT NULL DEFAULT 0,
    eudi_pid_verified   INTEGER NOT NULL DEFAULT 0,  
    
    signature_timestamp TEXT NOT NULL,
    tsa_provider        TEXT,
    
    status              TEXT NOT NULL DEFAULT 'valid',  
    revocation_reason   TEXT,
    
    verified_at         TEXT,
    created_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_qes_org ON eidas_qes_records(organization_id);
CREATE INDEX IF NOT EXISTS idx_qes_doc_ref ON eidas_qes_records(document_ref);
CREATE TABLE IF NOT EXISTS isms_risks (
    risk_id             TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',
    
    asset               TEXT NOT NULL,   
    threat              TEXT NOT NULL,   
    vulnerability       TEXT NOT NULL DEFAULT '',
    
    likelihood          INTEGER NOT NULL DEFAULT 2,  
    impact              INTEGER NOT NULL DEFAULT 2,  
    risk_score          INTEGER GENERATED ALWAYS AS (likelihood * impact) STORED,
    risk_level          TEXT NOT NULL DEFAULT 'medium',  
    
    control_ref         TEXT,  
    control_description TEXT NOT NULL DEFAULT '',
    treatment_option    TEXT NOT NULL DEFAULT 'mitigate',  
    residual_risk       TEXT,
    
    risk_owner          TEXT NOT NULL,
    review_due_at       TEXT,
    status              TEXT NOT NULL DEFAULT 'open',  
    
    identified_at       TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    updated_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    created_at          TEXT NOT NULL DEFAULT (to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);
CREATE INDEX IF NOT EXISTS idx_isms_risk_org ON isms_risks(organization_id);
CREATE INDEX IF NOT EXISTS idx_isms_risk_level ON isms_risks(risk_level);
CREATE INDEX IF NOT EXISTS idx_isms_risk_status ON isms_risks(status);

-- ===== 014_signatures.sql =====
CREATE TABLE IF NOT EXISTS document_signatures (
    sig_id          TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',

    
    document_ref    TEXT NOT NULL,
    document_hash   TEXT NOT NULL,        
    document_title  TEXT NOT NULL DEFAULT '',
    document_type   TEXT NOT NULL DEFAULT 'legal_document',

    
    signatory_id    TEXT NOT NULL,        
    signatory_name  TEXT NOT NULL,
    signatory_email TEXT NOT NULL,
    signatory_role  TEXT NOT NULL DEFAULT '',  

    
    jurisdiction    TEXT NOT NULL DEFAULT 'BR',
        
    signature_standard TEXT NOT NULL DEFAULT 'ICP-Brasil',
        
    signature_level TEXT NOT NULL DEFAULT 'QES',
        

    
    certificate_issuer  TEXT NOT NULL DEFAULT '',
    certificate_serial  TEXT NOT NULL DEFAULT '',
    certificate_subject TEXT NOT NULL DEFAULT '',
    certificate_valid_from TEXT,
    certificate_valid_until TEXT,

    
    signature_b64   TEXT NOT NULL DEFAULT '',  
    signature_format TEXT NOT NULL DEFAULT '',
        

    
    signed_at       TEXT NOT NULL,
    tsa_timestamp   TEXT,
    tsa_provider    TEXT,
    tsa_serial      TEXT,

    
    action          TEXT NOT NULL DEFAULT 'signed',
        
    status          TEXT NOT NULL DEFAULT 'valid',
        

    
    hdr_id          TEXT,

    
    ip_address      TEXT,
    user_agent      TEXT,
    notes           TEXT NOT NULL DEFAULT '',

    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_doc_sigs_org
    ON document_signatures (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_doc_sigs_hash
    ON document_signatures (document_hash);
CREATE INDEX IF NOT EXISTS idx_doc_sigs_ref
    ON document_signatures (document_ref);
CREATE INDEX IF NOT EXISTS idx_doc_sigs_signatory
    ON document_signatures (signatory_id);
CREATE TABLE IF NOT EXISTS signature_acknowledgments (
    ack_id          TEXT PRIMARY KEY,
    sig_id          TEXT NOT NULL REFERENCES document_signatures(sig_id),

    
    acknowledged_by   TEXT NOT NULL,   
    acknowledged_name TEXT NOT NULL,
    acknowledged_email TEXT NOT NULL DEFAULT '',

    
    action          TEXT NOT NULL DEFAULT 'received',
        

    
    ack_hash        TEXT NOT NULL,  
    tsa_timestamp   TEXT,

    ip_address      TEXT,
    notes           TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sig_acks_sig
    ON signature_acknowledgments (sig_id);

-- ===== 015_usa_f18.sql =====
CREATE TABLE IF NOT EXISTS colorado_ai_records (
    record_id           TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    ai_system_name      TEXT NOT NULL,
    ai_system_version   TEXT NOT NULL DEFAULT '1.0',
    developer_name      TEXT NOT NULL DEFAULT '',
    deployer_name       TEXT NOT NULL DEFAULT '',

    
    risk_tier           TEXT NOT NULL DEFAULT 'limited',
        
    high_risk_category  TEXT,
        
        

    
    consequential_decision_desc TEXT NOT NULL DEFAULT '',

    
    impact_assessment_done   INTEGER NOT NULL DEFAULT 0,
    impact_assessment_date   TEXT,
    impact_assessment_ref    TEXT,
    bias_audit_done          INTEGER NOT NULL DEFAULT 0,
    bias_audit_date          TEXT,
    bias_audit_provider      TEXT,

    
    consumer_notification_text  TEXT NOT NULL DEFAULT '',
    opt_out_mechanism           TEXT NOT NULL DEFAULT '',
    appeal_process_available    INTEGER NOT NULL DEFAULT 0,

    
    monitoring_plan         TEXT NOT NULL DEFAULT '',
    incident_log            TEXT NOT NULL DEFAULT '[]',  

    status                  TEXT NOT NULL DEFAULT 'active',
        
    created_by              TEXT NOT NULL,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_colorado_org
    ON colorado_ai_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_colorado_tier
    ON colorado_ai_records (risk_tier);
CREATE TABLE IF NOT EXISTS ccpa_consent_records (
    consent_id          TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    consumer_id         TEXT NOT NULL,
    consumer_email      TEXT NOT NULL,
    consumer_state      TEXT NOT NULL DEFAULT 'CA',  

    
    data_categories     TEXT NOT NULL DEFAULT '[]',   
    processing_purposes TEXT NOT NULL DEFAULT '[]',   

    consent_type        TEXT NOT NULL DEFAULT 'opt_in',
        

    
    sensitive_data_consent         INTEGER NOT NULL DEFAULT 0,
    automated_decision_consent     INTEGER NOT NULL DEFAULT 0,
    sale_of_personal_info_consent  INTEGER NOT NULL DEFAULT 0,
    sharing_for_cross_context      INTEGER NOT NULL DEFAULT 0,

    
    consent_text        TEXT NOT NULL DEFAULT '',
    ip_address          TEXT,
    user_agent          TEXT,

    
    status              TEXT NOT NULL DEFAULT 'active',
        
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
CREATE TABLE IF NOT EXISTS aba_compliance_log (
    log_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    matter_ref          TEXT NOT NULL,
    attorney_id         TEXT NOT NULL,
    attorney_name       TEXT NOT NULL DEFAULT '',

    
    ai_tool_name        TEXT NOT NULL DEFAULT '',
    ai_tool_version     TEXT NOT NULL DEFAULT '',
    ai_tool_provider    TEXT NOT NULL DEFAULT '',

    
    rule_11_competence           INTEGER NOT NULL DEFAULT 0,  
    rule_16_confidentiality      INTEGER NOT NULL DEFAULT 0,  
    rule_34_fairness             INTEGER NOT NULL DEFAULT 0,  
    rule_53_supervision          INTEGER NOT NULL DEFAULT 0,  
    client_disclosure_made       INTEGER NOT NULL DEFAULT 0,  

    
    state_bar               TEXT NOT NULL DEFAULT 'CA',
    state_specific_rule_ref TEXT NOT NULL DEFAULT '',
    state_specific_notes    TEXT NOT NULL DEFAULT '',

    
    output_reviewed         INTEGER NOT NULL DEFAULT 0,
    review_notes            TEXT NOT NULL DEFAULT '',

    created_at              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_aba_org
    ON aba_compliance_log (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_aba_attorney
    ON aba_compliance_log (attorney_id);
CREATE TABLE IF NOT EXISTS nist_ai_rmf_records (
    rmf_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    ai_system_ref       TEXT NOT NULL,
    ai_system_name      TEXT NOT NULL DEFAULT '',
    ai_system_version   TEXT NOT NULL DEFAULT '1.0',

    
    govern_policies_defined     INTEGER NOT NULL DEFAULT 0,
    govern_roles_assigned       INTEGER NOT NULL DEFAULT 0,
    govern_risk_tolerance_set   INTEGER NOT NULL DEFAULT 0,
    govern_training_completed   INTEGER NOT NULL DEFAULT 0,
    govern_notes                TEXT NOT NULL DEFAULT '',

    
    map_intended_use            TEXT NOT NULL DEFAULT '',
    map_context_established     INTEGER NOT NULL DEFAULT 0,
    map_risks_identified        TEXT NOT NULL DEFAULT '[]',  
    map_stakeholders_consulted  INTEGER NOT NULL DEFAULT 0,
    map_notes                   TEXT NOT NULL DEFAULT '',

    
    measure_metrics_defined     INTEGER NOT NULL DEFAULT 0,
    measure_testing_completed   INTEGER NOT NULL DEFAULT 0,
    measure_bias_evaluated      INTEGER NOT NULL DEFAULT 0,
    measure_performance_score   REAL,        
    measure_trustworthiness     INTEGER,     
    measure_notes               TEXT NOT NULL DEFAULT '',

    
    manage_risk_responses       TEXT NOT NULL DEFAULT '[]',  
    manage_residual_risks       TEXT NOT NULL DEFAULT '[]',  
    manage_monitoring_plan      TEXT NOT NULL DEFAULT '',
    manage_incident_plan        TEXT NOT NULL DEFAULT '',
    manage_notes                TEXT NOT NULL DEFAULT '',

    
    profile_tier                TEXT NOT NULL DEFAULT 'tier-2',
        
    last_review_at              TEXT,
    next_review_at              TEXT,

    status                      TEXT NOT NULL DEFAULT 'active',
    created_by                  TEXT NOT NULL,
    created_at                  TEXT NOT NULL,
    updated_at                  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nist_org
    ON nist_ai_rmf_records (organization_id, created_at DESC);
CREATE TABLE IF NOT EXISTS esign_audit_log (
    audit_id        TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',

    
    sig_id          TEXT,

    event_type      TEXT NOT NULL,
        
        
    event_sequence  INTEGER NOT NULL DEFAULT 1,

    actor_id        TEXT NOT NULL,
    actor_name      TEXT NOT NULL DEFAULT '',
    actor_email     TEXT NOT NULL,
    actor_ip        TEXT,
    actor_user_agent TEXT,

    document_ref    TEXT NOT NULL DEFAULT '',
    document_hash   TEXT,

    
    event_hash      TEXT NOT NULL,  
    event_data      TEXT NOT NULL DEFAULT '{}',  

    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_esign_org
    ON esign_audit_log (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_esign_sig
    ON esign_audit_log (sig_id);
CREATE INDEX IF NOT EXISTS idx_esign_doc
    ON esign_audit_log (document_ref);

-- ===== 016_uae_f19.sql =====
CREATE TABLE IF NOT EXISTS uae_pdpl_consent (
    consent_id          TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    data_subject_id     TEXT NOT NULL,
    data_subject_name   TEXT NOT NULL,
    data_subject_email  TEXT NOT NULL DEFAULT '',
    data_subject_nationality TEXT NOT NULL DEFAULT '',

    
    data_categories     TEXT NOT NULL DEFAULT '[]',   
    processing_purposes TEXT NOT NULL DEFAULT '[]',   

    legal_basis         TEXT NOT NULL DEFAULT 'consent',
        
        

    
    sensitive_data_processing  INTEGER NOT NULL DEFAULT 0,
    biometric_data             INTEGER NOT NULL DEFAULT 0,
    health_data                INTEGER NOT NULL DEFAULT 0,
    children_data              INTEGER NOT NULL DEFAULT 0,  
    guardian_consent_obtained  INTEGER NOT NULL DEFAULT 0,  

    
    cross_border_transfer      INTEGER NOT NULL DEFAULT 0,
    transfer_destination_country TEXT,
    transfer_safeguards        TEXT NOT NULL DEFAULT '',
        

    
    difc_jurisdiction          INTEGER NOT NULL DEFAULT 0,
    adgm_jurisdiction          INTEGER NOT NULL DEFAULT 0,

    consent_text        TEXT NOT NULL DEFAULT '',
    ip_address          TEXT,
    language            TEXT NOT NULL DEFAULT 'en',  

    status              TEXT NOT NULL DEFAULT 'active',
        
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
CREATE TABLE IF NOT EXISTS uae_ai_governance (
    gov_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    ai_system_name      TEXT NOT NULL,
    ai_system_version   TEXT NOT NULL DEFAULT '1.0',
    ai_system_purpose   TEXT NOT NULL DEFAULT '',

    
    ethics_human_centered       INTEGER NOT NULL DEFAULT 0,  
    ethics_fairness             INTEGER NOT NULL DEFAULT 0,  
    ethics_transparency         INTEGER NOT NULL DEFAULT 0,  
    ethics_safety_reliability   INTEGER NOT NULL DEFAULT 0,  
    ethics_privacy_security     INTEGER NOT NULL DEFAULT 0,  
    ethics_accountability       INTEGER NOT NULL DEFAULT 0,  
    ethics_sustainability       INTEGER NOT NULL DEFAULT 0,  

    
    ai_seal_applied         INTEGER NOT NULL DEFAULT 0,
    ai_seal_reference       TEXT,
    ai_seal_issued_at       TEXT,
    ai_seal_expires_at      TEXT,
    ai_seal_category        TEXT,
        

    
    sector                  TEXT NOT NULL DEFAULT 'legal',
        
        

    
    difc_compliant          INTEGER NOT NULL DEFAULT 0,
    difc_registration_ref   TEXT,
    difc_dp_law_version     TEXT NOT NULL DEFAULT '2020',

    
    adgm_compliant          INTEGER NOT NULL DEFAULT 0,
    adgm_registration_ref   TEXT,

    
    jurisdiction_ae         TEXT NOT NULL DEFAULT 'federal',
        

    
    risk_level              TEXT NOT NULL DEFAULT 'medium',
        
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
CREATE TABLE IF NOT EXISTS uae_pass_signatures (
    sig_id              TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL DEFAULT 'org_default',

    document_ref        TEXT NOT NULL,
    document_hash       TEXT NOT NULL,  
    document_title      TEXT NOT NULL DEFAULT '',

    
    signatory_name      TEXT NOT NULL,
    signatory_email     TEXT NOT NULL,
    signatory_emirates_id TEXT,  
    signatory_mobile    TEXT,

    
    uae_pass_verified       INTEGER NOT NULL DEFAULT 0,
    uae_pass_identity_level TEXT NOT NULL DEFAULT 'verified',
        
    uae_pass_session_ref    TEXT,

    
    trust_service_provider  TEXT NOT NULL DEFAULT '',
        
    trust_service_level     TEXT NOT NULL DEFAULT 'qualified',
        
    qtsp_country            TEXT NOT NULL DEFAULT 'AE',

    
    signature_format        TEXT NOT NULL DEFAULT 'PAdES-LTA',
        
    signature_level         TEXT NOT NULL DEFAULT 'QES',
        

    
    signed_at               TEXT NOT NULL,
    tsa_timestamp           TEXT,
    tsa_provider            TEXT,

    
    hdr_id                  TEXT,

    status                  TEXT NOT NULL DEFAULT 'valid',
        
    created_at              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_uae_pass_org
    ON uae_pass_signatures (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uae_pass_hash
    ON uae_pass_signatures (document_hash);

-- ===== 017_iso42001_fria_f20.sql =====
CREATE TABLE IF NOT EXISTS iso42001_aims_records (
    aims_id         TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',
    ai_system_version TEXT NOT NULL DEFAULT '1.0',

    
    c4_internal_issues      TEXT NOT NULL DEFAULT '',   
    c4_external_issues      TEXT NOT NULL DEFAULT '',   
    c4_interested_parties   TEXT NOT NULL DEFAULT '[]', 
    c4_aims_scope           TEXT NOT NULL DEFAULT '',   
    c4_ai_policy_defined    INTEGER NOT NULL DEFAULT 0,

    
    c5_top_mgmt_commitment  INTEGER NOT NULL DEFAULT 0,
    c5_ai_policy_text       TEXT NOT NULL DEFAULT '',
    c5_roles_defined        INTEGER NOT NULL DEFAULT 0,
    c5_dpo_appointed        INTEGER NOT NULL DEFAULT 0,

    
    c6_risks_assessed       INTEGER NOT NULL DEFAULT 0,
    c6_opportunities_noted  INTEGER NOT NULL DEFAULT 0,
    c6_objectives_set       TEXT NOT NULL DEFAULT '[]', 
    c6_action_plans         TEXT NOT NULL DEFAULT '[]', 

    
    c7_resources_allocated  INTEGER NOT NULL DEFAULT 0,
    c7_competence_verified  INTEGER NOT NULL DEFAULT 0,
    c7_awareness_training   INTEGER NOT NULL DEFAULT 0,
    c7_documentation_maintained INTEGER NOT NULL DEFAULT 0,

    
    c8_operational_controls INTEGER NOT NULL DEFAULT 0,
    c8_ai_system_lifecycle  TEXT NOT NULL DEFAULT '',   
    c8_data_quality_assured INTEGER NOT NULL DEFAULT 0,
    c8_human_oversight_active INTEGER NOT NULL DEFAULT 0,
    c8_incident_response_plan TEXT NOT NULL DEFAULT '',

    
    c9_monitoring_metrics   TEXT NOT NULL DEFAULT '{}', 
    c9_internal_audit_done  INTEGER NOT NULL DEFAULT 0,
    c9_mgmt_review_done     INTEGER NOT NULL DEFAULT 0,
    c9_last_audit_date      TEXT,

    
    c10_nonconformities     TEXT NOT NULL DEFAULT '[]', 
    c10_corrective_actions  TEXT NOT NULL DEFAULT '[]', 
    c10_continual_improvement_plan TEXT NOT NULL DEFAULT '',

    
    
    annex_a2_dev_policy     INTEGER NOT NULL DEFAULT 0,
    
    annex_a3_internal_audit INTEGER NOT NULL DEFAULT 0,
    
    annex_a4_impact_assess  INTEGER NOT NULL DEFAULT 0,
    
    annex_a5_lifecycle_mgmt INTEGER NOT NULL DEFAULT 0,
    
    annex_a6_data_mgmt      INTEGER NOT NULL DEFAULT 0,
    
    annex_a7_training_data  INTEGER NOT NULL DEFAULT 0,
    
    annex_a8_documentation  INTEGER NOT NULL DEFAULT 0,
    
    annex_a9_logging        INTEGER NOT NULL DEFAULT 0,

    
    certification_body      TEXT,
    certification_date      TEXT,
    certificate_number      TEXT,
    certificate_expires_at  TEXT,
    certification_status    TEXT NOT NULL DEFAULT 'not_started',
        

    
    conformity_score        INTEGER,  
    status                  TEXT NOT NULL DEFAULT 'active',
    created_by              TEXT NOT NULL,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_iso42001_org
    ON iso42001_aims_records (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_iso42001_cert
    ON iso42001_aims_records (certification_status);
CREATE TABLE IF NOT EXISTS iso42001_control_log (
    log_id          TEXT PRIMARY KEY,
    aims_id         TEXT NOT NULL REFERENCES iso42001_aims_records(aims_id),
    control_ref     TEXT NOT NULL,   
    control_name    TEXT NOT NULL DEFAULT '',
    evidence        TEXT NOT NULL DEFAULT '',   
    status          TEXT NOT NULL DEFAULT 'planned',
        
    verified_by     TEXT,
    verified_at     TEXT,
    created_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fria_assessments (
    fria_id         TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    
    intended_purpose        TEXT NOT NULL DEFAULT '',
    foreseeable_misuse      TEXT NOT NULL DEFAULT '',
    geographic_scope        TEXT NOT NULL DEFAULT '',  
    population_affected     TEXT NOT NULL DEFAULT '',  

    
    right_dignity           INTEGER NOT NULL DEFAULT 0,  
    right_privacy           INTEGER NOT NULL DEFAULT 0,  
    right_nondiscrimination INTEGER NOT NULL DEFAULT 0,  
    right_fair_trial        INTEGER NOT NULL DEFAULT 0,  
    right_presumption       INTEGER NOT NULL DEFAULT 0,  
    right_labour            INTEGER NOT NULL DEFAULT 0,  
    right_education         INTEGER NOT NULL DEFAULT 0,  
    right_property          INTEGER NOT NULL DEFAULT 0,  
    other_rights            TEXT NOT NULL DEFAULT '',

    
    impact_severity         TEXT NOT NULL DEFAULT 'low',
        
    impact_likelihood       TEXT NOT NULL DEFAULT 'low',
        
    impact_description      TEXT NOT NULL DEFAULT '',
    vulnerable_groups_affected INTEGER NOT NULL DEFAULT 0,
    vulnerable_groups_desc  TEXT NOT NULL DEFAULT '',

    
    technical_measures      TEXT NOT NULL DEFAULT '[]',  
    organisational_measures TEXT NOT NULL DEFAULT '[]',  
    transparency_measures   TEXT NOT NULL DEFAULT '[]',  
    human_oversight_measures TEXT NOT NULL DEFAULT '[]', 
    residual_risk_level     TEXT NOT NULL DEFAULT 'low',
        

    
    deployment_approved     INTEGER NOT NULL DEFAULT 0,
    deployment_conditions   TEXT NOT NULL DEFAULT '',
    review_frequency        TEXT NOT NULL DEFAULT 'annual',
        

    
    assessor_id             TEXT NOT NULL,
    assessor_name           TEXT NOT NULL DEFAULT '',
    dpo_consulted           INTEGER NOT NULL DEFAULT 0,
    legal_reviewed          INTEGER NOT NULL DEFAULT 0,
    approved_by             TEXT,
    approved_at             TEXT,

    status                  TEXT NOT NULL DEFAULT 'draft',
        
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

-- ===== 018_legal_evidence_f20.sql =====
CREATE TABLE IF NOT EXISTS fre707_evidence_records (
    evidence_id     TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    case_ref        TEXT NOT NULL,        
    court           TEXT NOT NULL DEFAULT '',
    jurisdiction    TEXT NOT NULL DEFAULT 'federal',
        
    document_ref    TEXT NOT NULL,        
    document_type   TEXT NOT NULL DEFAULT '',
        

    
    ai_system_name  TEXT NOT NULL DEFAULT '',
    ai_system_version TEXT NOT NULL DEFAULT '',
    ai_provider     TEXT NOT NULL DEFAULT '',  
    ai_model_id     TEXT NOT NULL DEFAULT '',
    training_data_cutoff TEXT,
    training_data_description TEXT NOT NULL DEFAULT '',

    
    methodology_disclosed    INTEGER NOT NULL DEFAULT 0,   
    reliable_principles      INTEGER NOT NULL DEFAULT 0,   
    principles_applied       INTEGER NOT NULL DEFAULT 0,   
    opinion_not_speculative  INTEGER NOT NULL DEFAULT 0,   

    
    validation_method       TEXT NOT NULL DEFAULT '',
    error_rate_known        INTEGER NOT NULL DEFAULT 0,
    error_rate_value        REAL,           
    peer_reviewed           INTEGER NOT NULL DEFAULT 0,
    human_attorney_reviewed INTEGER NOT NULL DEFAULT 0,
    human_reviewer_id       TEXT,

    
    daubert_analysis        TEXT NOT NULL DEFAULT '',   
    admissibility_opinion   TEXT NOT NULL DEFAULT 'pending',
        
    admissibility_conditions TEXT NOT NULL DEFAULT '',
    opposing_counsel_notified INTEGER NOT NULL DEFAULT 0,
    court_ruling            TEXT,

    
    hdr_id                  TEXT,   
    generation_timestamp    TEXT NOT NULL,
    hash_sha256             TEXT NOT NULL DEFAULT '',
    chain_of_custody_intact INTEGER NOT NULL DEFAULT 1,

    status                  TEXT NOT NULL DEFAULT 'draft',
        
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
CREATE TABLE IF NOT EXISTS citation_verifications (
    citation_id     TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    document_ref    TEXT NOT NULL,          
    case_ref        TEXT NOT NULL DEFAULT '',

    
    citation_text   TEXT NOT NULL DEFAULT '',   
    citation_type   TEXT NOT NULL DEFAULT 'case',
        
    cited_court     TEXT NOT NULL DEFAULT '',
    cited_year      TEXT NOT NULL DEFAULT '',
    reporter        TEXT NOT NULL DEFAULT '',   
    volume          TEXT NOT NULL DEFAULT '',
    page_start      TEXT NOT NULL DEFAULT '',
    url             TEXT NOT NULL DEFAULT '',

    
    verified_by     TEXT NOT NULL,          
    verification_method TEXT NOT NULL DEFAULT 'manual',
        
    verification_db TEXT NOT NULL DEFAULT '',  
    verification_date TEXT NOT NULL,

    
    citation_exists INTEGER NOT NULL DEFAULT 0,   
    proposition_accurate INTEGER NOT NULL DEFAULT 0, 
    quote_accurate  INTEGER NOT NULL DEFAULT 0,   
    case_still_good_law INTEGER NOT NULL DEFAULT 1, 

    
    is_hallucination        INTEGER NOT NULL DEFAULT 0,
    hallucination_type      TEXT,
        
    hallucination_severity  TEXT NOT NULL DEFAULT 'none',
        
    hallucination_notes     TEXT NOT NULL DEFAULT '',

    
    filed_with_court        INTEGER NOT NULL DEFAULT 0,
    corrective_action_taken INTEGER NOT NULL DEFAULT 0,
    corrective_action_desc  TEXT NOT NULL DEFAULT '',
    bar_complaint_risk      TEXT NOT NULL DEFAULT 'none',
        

    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_citation_org
    ON citation_verifications (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_citation_doc
    ON citation_verifications (document_ref);
CREATE INDEX IF NOT EXISTS idx_citation_hallucination
    ON citation_verifications (is_hallucination, hallucination_severity);
CREATE TABLE IF NOT EXISTS hallucination_incidents (
    incident_id     TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    citation_id     TEXT REFERENCES citation_verifications(citation_id),
    document_ref    TEXT NOT NULL DEFAULT '',
    case_ref        TEXT NOT NULL DEFAULT '',

    
    incident_type   TEXT NOT NULL DEFAULT 'citation',
        
    ai_system       TEXT NOT NULL DEFAULT '',
    ai_model        TEXT NOT NULL DEFAULT '',
    original_output TEXT NOT NULL DEFAULT '',   
    correct_info    TEXT NOT NULL DEFAULT '',   

    
    severity        TEXT NOT NULL DEFAULT 'medium',
        
    filed_with_court INTEGER NOT NULL DEFAULT 0,
    court_sanction  TEXT,   
    financial_impact REAL,  
    client_notified INTEGER NOT NULL DEFAULT 0,
    bar_reported    INTEGER NOT NULL DEFAULT 0,

    
    root_cause      TEXT NOT NULL DEFAULT '',
    prevention_measure TEXT NOT NULL DEFAULT '',
    workflow_updated INTEGER NOT NULL DEFAULT 0,

    
    status          TEXT NOT NULL DEFAULT 'open',
        
    resolved_at     TEXT,
    resolved_by     TEXT,

    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hallucination_org
    ON hallucination_incidents (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_hallucination_severity
    ON hallucination_incidents (severity, status);
CREATE TABLE IF NOT EXISTS ai_competence_certificates (
    cert_id         TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    attorney_id     TEXT NOT NULL,
    attorney_name   TEXT NOT NULL DEFAULT '',
    bar_number      TEXT NOT NULL DEFAULT '',
    jurisdiction    TEXT NOT NULL DEFAULT '',   

    
    training_provider   TEXT NOT NULL DEFAULT '',
    training_course     TEXT NOT NULL DEFAULT '',
    cle_credits_earned  REAL NOT NULL DEFAULT 0,
    training_date       TEXT NOT NULL,
    training_topics     TEXT NOT NULL DEFAULT '[]',  

    
    ai_systems_covered  TEXT NOT NULL DEFAULT '[]',  
    competence_areas    TEXT NOT NULL DEFAULT '[]',  
        

    
    aba_rule_1_1_compliant  INTEGER NOT NULL DEFAULT 0,
    state_bar_compliant     INTEGER NOT NULL DEFAULT 0,
    renewal_due_date        TEXT,
    continuing_ed_required  INTEGER NOT NULL DEFAULT 0,

    
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

-- ===== 019_apac_global_f20.sql =====
CREATE TABLE IF NOT EXISTS uk_gdpr_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    
    ico_reference   TEXT NOT NULL DEFAULT '',
    ico_registered  INTEGER NOT NULL DEFAULT 0,
    data_protection_fee_paid INTEGER NOT NULL DEFAULT 0,

    
    lawful_basis    TEXT NOT NULL DEFAULT '',
        
    legitimate_interests_assessment TEXT NOT NULL DEFAULT '',

    
    ai_code_applicable INTEGER NOT NULL DEFAULT 0,
    transparency_notice_published INTEGER NOT NULL DEFAULT 0,
    human_review_available INTEGER NOT NULL DEFAULT 0,
    profiling_used  INTEGER NOT NULL DEFAULT 0,
    profiling_basis TEXT NOT NULL DEFAULT '',

    
    right_access_process    TEXT NOT NULL DEFAULT '',  
    right_erasure_process   TEXT NOT NULL DEFAULT '',  
    right_portability_process TEXT NOT NULL DEFAULT '', 
    right_object_ai         TEXT NOT NULL DEFAULT '',  

    
    dpo_required    INTEGER NOT NULL DEFAULT 0,
    dpo_name        TEXT NOT NULL DEFAULT '',
    uk_rep_appointed INTEGER NOT NULL DEFAULT 0,
    uk_rep_name     TEXT NOT NULL DEFAULT '',

    
    eu_transfer_mechanism TEXT NOT NULL DEFAULT '',
        
    international_transfers TEXT NOT NULL DEFAULT '{}', 

    
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
CREATE TABLE IF NOT EXISTS canada_privacy_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    
    provincial_law  TEXT NOT NULL DEFAULT 'federal',
        
    law_25_quebec   INTEGER NOT NULL DEFAULT 0,

    
    consent_obtained        INTEGER NOT NULL DEFAULT 0,
    consent_form            TEXT NOT NULL DEFAULT '',
    implied_consent_basis   TEXT NOT NULL DEFAULT '',
    withdrawal_mechanism    TEXT NOT NULL DEFAULT '',

    
    aida_applicable         INTEGER NOT NULL DEFAULT 0,
    high_impact_system      INTEGER NOT NULL DEFAULT 0,
    high_impact_categories  TEXT NOT NULL DEFAULT '[]',  
    impact_assessment_done  INTEGER NOT NULL DEFAULT 0,
    impact_assessment_ref   TEXT,
    mitigation_measures     TEXT NOT NULL DEFAULT '[]',  
    incident_reporting_process TEXT NOT NULL DEFAULT '',

    
    q25_privacy_officer     TEXT NOT NULL DEFAULT '',
    q25_privacy_policy_published INTEGER NOT NULL DEFAULT 0,
    q25_pia_required        INTEGER NOT NULL DEFAULT 0,
    q25_pia_done            INTEGER NOT NULL DEFAULT 0,
    q25_72h_breach_report   INTEGER NOT NULL DEFAULT 0,
    q25_portability_enabled INTEGER NOT NULL DEFAULT 0,

    
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
CREATE TABLE IF NOT EXISTS singapore_pdpa_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    
    pdpa_dpo_designated     INTEGER NOT NULL DEFAULT 0,
    pdpa_dpo_name           TEXT NOT NULL DEFAULT '',
    pdpa_dpo_registered     INTEGER NOT NULL DEFAULT 0,  
    data_protection_policy_published INTEGER NOT NULL DEFAULT 0,
    do_not_call_compliant   INTEGER NOT NULL DEFAULT 0,

    
    consent_purpose_specific INTEGER NOT NULL DEFAULT 0,
    notification_given      INTEGER NOT NULL DEFAULT 0,
    deemed_consent_applied  INTEGER NOT NULL DEFAULT 0,  

    
    agentic_ai_applicable   INTEGER NOT NULL DEFAULT 0,
    
    agentic_human_oversight INTEGER NOT NULL DEFAULT 0,
    agentic_oversight_desc  TEXT NOT NULL DEFAULT '',
    
    agentic_disclosure      INTEGER NOT NULL DEFAULT 0,
    agentic_disclosure_text TEXT NOT NULL DEFAULT '',
    
    agentic_consent_scope   TEXT NOT NULL DEFAULT '',
    
    agentic_data_minimised  INTEGER NOT NULL DEFAULT 0,
    
    agentic_incident_plan   TEXT NOT NULL DEFAULT '',

    
    pdpc_model_governance_aligned INTEGER NOT NULL DEFAULT 0,
    explainability_implemented INTEGER NOT NULL DEFAULT 0,
    bias_testing_done       INTEGER NOT NULL DEFAULT 0,

    
    cbdt_countries          TEXT NOT NULL DEFAULT '[]',  
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
CREATE TABLE IF NOT EXISTS australia_privacy_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    
    annual_turnover_aud     REAL,   
    health_service_provider INTEGER NOT NULL DEFAULT 0,  
    acts_covered            INTEGER NOT NULL DEFAULT 0,

    
    
    app1_privacy_policy     INTEGER NOT NULL DEFAULT 0,
    
    app5_collection_notice  INTEGER NOT NULL DEFAULT 0,
    
    app6_primary_purpose_only INTEGER NOT NULL DEFAULT 0,
    
    app11_security_measures TEXT NOT NULL DEFAULT '',
    
    app12_access_process    TEXT NOT NULL DEFAULT '',
    
    app13_correction_process TEXT NOT NULL DEFAULT '',

    
    adm_used                INTEGER NOT NULL DEFAULT 0,
    adm_description         TEXT NOT NULL DEFAULT '',
    adm_explanation_available INTEGER NOT NULL DEFAULT 0,  
    adm_human_review_available INTEGER NOT NULL DEFAULT 0,
    adm_opt_out_available   INTEGER NOT NULL DEFAULT 0,
    adm_meaningful_impact   INTEGER NOT NULL DEFAULT 0,    

    
    ndb_scheme_applicable   INTEGER NOT NULL DEFAULT 1,
    breach_assessment_process TEXT NOT NULL DEFAULT '',
    oaic_notification_process TEXT NOT NULL DEFAULT '',   

    
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
CREATE TABLE IF NOT EXISTS apac_compliance_summary (
    summary_id      TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    
    uk_record_id    TEXT REFERENCES uk_gdpr_records(record_id),
    canada_record_id TEXT REFERENCES canada_privacy_records(record_id),
    singapore_record_id TEXT REFERENCES singapore_pdpa_records(record_id),
    australia_record_id TEXT REFERENCES australia_privacy_records(record_id),

    
    uk_score        INTEGER,
    canada_score    INTEGER,
    singapore_score INTEGER,
    australia_score INTEGER,
    global_score    INTEGER,  

    
    open_gaps       TEXT NOT NULL DEFAULT '[]',   
    critical_gaps   INTEGER NOT NULL DEFAULT 0,

    last_assessed_at TEXT,
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_apac_summary_org
    ON apac_compliance_summary (organization_id);

-- ===== 020_malpractice_f20.sql =====
CREATE TABLE IF NOT EXISTS colorado_sb26189_records (
    record_id       TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',
    ai_system_version TEXT NOT NULL DEFAULT '1.0',

    
    consequential_decision_type TEXT NOT NULL DEFAULT '',
        
        
    consumers_affected_count INTEGER NOT NULL DEFAULT 0,

    
    
    disclosure_provided     INTEGER NOT NULL DEFAULT 0,
    disclosure_timing       TEXT NOT NULL DEFAULT '',  
    disclosure_method       TEXT NOT NULL DEFAULT '',  

    
    explanation_available   INTEGER NOT NULL DEFAULT 0,
    explanation_process     TEXT NOT NULL DEFAULT '',
    explanation_response_days INTEGER NOT NULL DEFAULT 30,

    
    data_correction_available INTEGER NOT NULL DEFAULT 0,
    data_correction_process TEXT NOT NULL DEFAULT '',

    
    human_review_available  INTEGER NOT NULL DEFAULT 0,
    human_review_process    TEXT NOT NULL DEFAULT '',
    human_review_response_days INTEGER NOT NULL DEFAULT 30,

    
    opt_out_available       INTEGER NOT NULL DEFAULT 0,
    opt_out_categories      TEXT NOT NULL DEFAULT '[]',  

    
    cure_period_days        INTEGER NOT NULL DEFAULT 90,
    ag_notice_received      INTEGER NOT NULL DEFAULT 0,
    ag_notice_date          TEXT,
    cure_completed          INTEGER NOT NULL DEFAULT 0,
    cure_completion_date    TEXT,

    
    small_business_exempt   INTEGER NOT NULL DEFAULT 0,  
    open_source_exempt      INTEGER NOT NULL DEFAULT 0,
    national_security_exempt INTEGER NOT NULL DEFAULT 0,

    
    legacy_sb205_impact_assessment TEXT,   
    legacy_sb205_bias_audit TEXT,          

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_co_sb26189_org
    ON colorado_sb26189_records (organization_id);
CREATE INDEX IF NOT EXISTS idx_co_sb26189_type
    ON colorado_sb26189_records (consequential_decision_type);
CREATE TABLE IF NOT EXISTS ccpa_admt_records (
    admt_id         TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    
    admt_purpose    TEXT NOT NULL DEFAULT '',
        
        
    significant_decisions INTEGER NOT NULL DEFAULT 0,  
    personal_data_used    INTEGER NOT NULL DEFAULT 0,
    california_consumers  INTEGER NOT NULL DEFAULT 0,

    
    pre_use_notice_provided INTEGER NOT NULL DEFAULT 0,
    pre_use_notice_content  TEXT NOT NULL DEFAULT '',
    notice_delivery_method  TEXT NOT NULL DEFAULT '',

    
    opt_out_available       INTEGER NOT NULL DEFAULT 0,
    opt_out_mechanism       TEXT NOT NULL DEFAULT '',
    opt_out_response_days   INTEGER NOT NULL DEFAULT 15,
    global_opt_out_honored  INTEGER NOT NULL DEFAULT 0,  

    
    access_to_admt_logic    INTEGER NOT NULL DEFAULT 0,
    access_process          TEXT NOT NULL DEFAULT '',

    
    human_review_available  INTEGER NOT NULL DEFAULT 0,
    human_review_process    TEXT NOT NULL DEFAULT '',
    human_review_timing     TEXT NOT NULL DEFAULT '',

    
    risk_assessment_required INTEGER NOT NULL DEFAULT 0,
    risk_assessment_done    INTEGER NOT NULL DEFAULT 0,
    risk_assessment_ref     TEXT,
    cppa_submission_required INTEGER NOT NULL DEFAULT 0,  

    
    admt_vendor_agreements  TEXT NOT NULL DEFAULT '[]',  

    status          TEXT NOT NULL DEFAULT 'active',
    created_by      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ccpa_admt_org
    ON ccpa_admt_records (organization_id);
CREATE INDEX IF NOT EXISTS idx_ccpa_admt_purpose
    ON ccpa_admt_records (admt_purpose, significant_decisions);
CREATE TABLE IF NOT EXISTS malpractice_insurance_records (
    insurance_id    TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    law_firm_name   TEXT NOT NULL DEFAULT '',
    bar_jurisdiction TEXT NOT NULL DEFAULT '',   

    
    insurer_name    TEXT NOT NULL DEFAULT '',
    policy_number   TEXT NOT NULL DEFAULT '',
    policy_start    TEXT,
    policy_end      TEXT,
    coverage_limit_usd REAL,
    current_premium_usd REAL,

    
    ai_tools_used           INTEGER NOT NULL DEFAULT 0,
    ai_tools_list           TEXT NOT NULL DEFAULT '[]',  
    ai_outputs_filed_in_court INTEGER NOT NULL DEFAULT 0,
    citation_verification_process INTEGER NOT NULL DEFAULT 0,
    hallucination_incidents_12mo INTEGER NOT NULL DEFAULT 0,
    ai_competence_certified INTEGER NOT NULL DEFAULT 0,  

    
    
    
    heillon_compliance_score INTEGER,
    score_breakdown         TEXT NOT NULL DEFAULT '{}',  
    score_date              TEXT,
    score_certified_by      TEXT,   

    
    base_risk_factor        REAL,    
    ai_risk_adjustment      REAL,    
    estimated_discount_pct  REAL,    
    insurer_accepted_score  INTEGER NOT NULL DEFAULT 0,

    
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
CREATE TABLE IF NOT EXISTS heillon_compliance_scores (
    score_id        TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',
    ai_system_ref   TEXT NOT NULL,
    ai_system_name  TEXT NOT NULL DEFAULT '',

    
    score_hdr_coverage      INTEGER NOT NULL DEFAULT 0,  
    score_citation_accuracy INTEGER NOT NULL DEFAULT 0,  
    score_hallucination     INTEGER NOT NULL DEFAULT 0,  
    score_lgpd              INTEGER NOT NULL DEFAULT 0,  
    score_gdpr_eu           INTEGER NOT NULL DEFAULT 0,  
    score_gdpr_uk           INTEGER NOT NULL DEFAULT 0,  
    score_ccpa              INTEGER NOT NULL DEFAULT 0,  
    score_colorado          INTEGER NOT NULL DEFAULT 0,  
    score_pdpl_uae          INTEGER NOT NULL DEFAULT 0,  
    score_pdpa_sg           INTEGER NOT NULL DEFAULT 0,  
    score_privacy_au        INTEGER NOT NULL DEFAULT 0,  
    score_pipeda_ca         INTEGER NOT NULL DEFAULT 0,  
    score_iso42001          INTEGER NOT NULL DEFAULT 0,  
    score_iso27001          INTEGER NOT NULL DEFAULT 0,  
    score_nist_rmf          INTEGER NOT NULL DEFAULT 0,  
    score_euai_act          INTEGER NOT NULL DEFAULT 0,  
    score_attorney_competence INTEGER NOT NULL DEFAULT 0, 

    
    total_score             INTEGER NOT NULL DEFAULT 0,
    certification_tier      TEXT NOT NULL DEFAULT 'unrated',
        

    
    evidence_bundle         TEXT NOT NULL DEFAULT '{}',  

    computed_at             TEXT NOT NULL,
    valid_until             TEXT,       
    computed_by             TEXT NOT NULL DEFAULT 'system',
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_heillon_score_org
    ON heillon_compliance_scores (organization_id, computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_heillon_score_tier
    ON heillon_compliance_scores (certification_tier);

-- ===== 021_freemium_tiers.sql =====
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS tier TEXT NOT NULL DEFAULT 'free';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS tier_period_start TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS tier_period_end TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS tier_updated_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z';
CREATE INDEX IF NOT EXISTS idx_orgs_tier ON organizations(tier);
ALTER TABLE hdrs ADD COLUMN IF NOT EXISTS created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z';
CREATE INDEX IF NOT EXISTS idx_hdr_created_at ON hdrs(created_at);
CREATE INDEX IF NOT EXISTS idx_hdr_org_created ON hdrs(organization_id, created_at);

-- ===== 022_api_keys.sql =====
CREATE TABLE IF NOT EXISTS api_keys (
    api_key_id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    last_used_at TEXT,
    revoked_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

-- ===== 023_beta_feedback.sql =====
CREATE TABLE IF NOT EXISTS beta_feedback (
    id                   TEXT PRIMARY KEY,
    organization_id      TEXT NOT NULL DEFAULT 'org_default',
    user_id              TEXT,
    role                 TEXT,
    usability_score      INTEGER,
    experience_score     INTEGER,
    functionality_score  INTEGER,
    delivers_score       INTEGER,
    nps                  INTEGER,
    adopt                TEXT,
    most_valuable        TEXT,
    frictions            TEXT,
    improvements         TEXT,
    contact_ok           INTEGER NOT NULL DEFAULT 0,
    created_at           TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_feedback_org ON beta_feedback(organization_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON beta_feedback(created_at);
