-- Migration 010: Fase 14 — LGPD Técnica + Marco Civil
-- RIPD, DPO requests, access logs com retenção, incidentes, consentimento granular
-- Safe to run multiple times (all DDL uses IF NOT EXISTS)

-- ─── RIPD (Relatório de Impacto à Proteção de Dados) ───────────────────────
CREATE TABLE IF NOT EXISTS ripd_reports (
    ripd_id          TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    created_by       TEXT NOT NULL,   -- user_id
    -- LGPD art. 38 campos obrigatórios
    title            TEXT NOT NULL,
    processing_type  TEXT NOT NULL,   -- ex: 'ingestion', 'analysis', 'forensic'
    legal_basis      TEXT NOT NULL,   -- 'consent' | 'contract' | 'legal_obligation' | 'legitimate_interest' | 'vital_interest' | 'public_task'
    purpose          TEXT NOT NULL,
    data_categories  TEXT NOT NULL,   -- JSON array
    data_lifecycle   TEXT NOT NULL,   -- retention policy description
    recipients       TEXT NOT NULL,   -- JSON array
    risks_identified TEXT NOT NULL,   -- JSON array
    safeguards       TEXT NOT NULL,   -- JSON array
    dpo_name         TEXT NOT NULL DEFAULT '',
    dpo_email        TEXT NOT NULL DEFAULT '',
    -- metadata
    status           TEXT NOT NULL DEFAULT 'draft',  -- 'draft' | 'approved' | 'archived'
    pdf_path         TEXT,            -- path to generated PDF/A
    pdf_checksum     TEXT,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    approved_at      TEXT,
    approved_by      TEXT
);

CREATE INDEX IF NOT EXISTS idx_ripd_org ON ripd_reports(organization_id);
CREATE INDEX IF NOT EXISTS idx_ripd_created ON ripd_reports(created_at);

-- ─── DPO Requests (solicitações de direitos do titular — LGPD art. 18) ──────
CREATE TABLE IF NOT EXISTS dpo_requests (
    request_id       TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    -- dados do solicitante (pode ser não autenticado)
    requester_name   TEXT NOT NULL,
    requester_email  TEXT NOT NULL,
    requester_cpf    TEXT,            -- identificação opcional
    -- tipo de solicitação
    request_type     TEXT NOT NULL,   -- 'access' | 'correction' | 'deletion' | 'portability' | 'revocation' | 'info'
    description      TEXT NOT NULL,
    -- workflow (prazo 15 dias LGPD art. 19)
    status           TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'in_progress' | 'completed' | 'rejected'
    assigned_to      TEXT,            -- user_id do responsável
    response_notes   TEXT,
    -- timestamps
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    due_at           TEXT NOT NULL,   -- created_at + 15 days
    completed_at     TEXT,
    -- audit
    ip_address       TEXT,
    user_agent       TEXT
);

CREATE INDEX IF NOT EXISTS idx_dpo_org ON dpo_requests(organization_id);
CREATE INDEX IF NOT EXISTS idx_dpo_email ON dpo_requests(requester_email);
CREATE INDEX IF NOT EXISTS idx_dpo_status ON dpo_requests(status);
CREATE INDEX IF NOT EXISTS idx_dpo_due ON dpo_requests(due_at);

-- ─── Access Logs (Marco Civil arts. 13-15) ───────────────────────────────────
-- application logs: min 6 months, max 12 months; connection logs: min 1 year
CREATE TABLE IF NOT EXISTS access_logs (
    log_id           TEXT PRIMARY KEY,
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    user_id          TEXT,
    log_type         TEXT NOT NULL,   -- 'application' | 'connection'
    event_type       TEXT NOT NULL,   -- 'login' | 'logout' | 'api_call' | 'data_access' | 'data_export' etc.
    resource         TEXT,            -- endpoint or resource accessed
    ip_address       TEXT NOT NULL,
    user_agent       TEXT,
    response_code    INTEGER,
    -- retention (Marco Civil)
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    expires_at       TEXT NOT NULL,   -- auto-purged after this date
    -- judicial access control (ONLY via court order)
    judicial_hold    INTEGER NOT NULL DEFAULT 0  -- 1 = court order, never purge
);

CREATE INDEX IF NOT EXISTS idx_access_logs_org ON access_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_expires ON access_logs(expires_at);
CREATE INDEX IF NOT EXISTS idx_access_logs_type ON access_logs(log_type);

-- ─── Security Incidents (ANPD Res. 15/2024) ──────────────────────────────────
-- workflow: detection → evaluation → ANPD notification (≤72h) → data subject notification
-- retention: minimum 5 years (LGPD art. 48 + Res. 15/2024)
CREATE TABLE IF NOT EXISTS security_incidents (
    incident_id        TEXT PRIMARY KEY,
    organization_id    TEXT NOT NULL DEFAULT 'org_default',
    -- detecção
    detected_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    detected_by        TEXT NOT NULL,   -- user_id ou 'system'
    -- categorização (ANPD Res. 15/2024 art. 6)
    category           TEXT NOT NULL,   -- 'unauthorized_access' | 'data_leak' | 'ransomware' | 'insider_threat' | 'lost_device' | 'other'
    description        TEXT NOT NULL,
    severity           TEXT NOT NULL DEFAULT 'medium',  -- 'low' | 'medium' | 'high' | 'critical'
    -- impacto
    affected_subjects_count  INTEGER NOT NULL DEFAULT 0,
    affected_data_types      TEXT NOT NULL DEFAULT '[]',  -- JSON array
    potential_harm           TEXT,
    -- workflow
    status             TEXT NOT NULL DEFAULT 'detected',
    -- 'detected' | 'evaluating' | 'anpd_notified' | 'subjects_notified' | 'closed'
    -- notificação ANPD (prazo ≤72h)
    anpd_notification_due_at  TEXT,    -- detected_at + 72h
    anpd_notified_at          TEXT,
    anpd_notification_ref     TEXT,    -- número de protocolo ANPD
    -- notificação titulares
    subjects_notified_at      TEXT,
    notification_method       TEXT,
    -- contenção e remediação
    containment_measures      TEXT,
    remediation_plan          TEXT,
    -- audit (LGPD art. 48: retenção mínima 5 anos)
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    closed_at          TEXT,
    closed_by          TEXT,
    retain_until       TEXT NOT NULL  -- created_at + 5 years
);

CREATE INDEX IF NOT EXISTS idx_incidents_org ON security_incidents(organization_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_detected ON security_incidents(detected_at);

-- ─── Consent Records (LGPD art. 8 — consentimento granular) ─────────────────
-- one row per (user_id, purpose) — updated on change
CREATE TABLE IF NOT EXISTS consent_records (
    consent_id       TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    -- purpose (granular)
    purpose          TEXT NOT NULL,   -- 'analytics' | 'ai_training' | 'marketing' | 'third_party' | 'research'
    legal_basis      TEXT NOT NULL,   -- 'consent' | 'contract' | 'legitimate_interest' | 'legal_obligation'
    -- state
    granted          INTEGER NOT NULL DEFAULT 0,   -- 0=denied, 1=granted
    -- audit trail
    granted_at       TEXT,
    revoked_at       TEXT,
    version          TEXT NOT NULL DEFAULT '1.0',  -- privacy policy version at time of consent
    ip_address       TEXT,
    user_agent       TEXT,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_consent_user_purpose ON consent_records(user_id, purpose);
CREATE INDEX IF NOT EXISTS idx_consent_user ON consent_records(user_id);
CREATE INDEX IF NOT EXISTS idx_consent_org ON consent_records(organization_id);
