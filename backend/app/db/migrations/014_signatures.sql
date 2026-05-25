-- Migration 014 — Universal document signature lifecycle
-- Covers: Brazil ICP-Brasil, EU eIDAS, USA ESIGN, UAE PASS
-- Proof of send / delivery / receipt / signature for responsible personas

CREATE TABLE IF NOT EXISTS document_signatures (
    sig_id          TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL DEFAULT 'org_default',

    -- Document identification
    document_ref    TEXT NOT NULL,
    document_hash   TEXT NOT NULL,        -- SHA-256 (64 hex)
    document_title  TEXT NOT NULL DEFAULT '',
    document_type   TEXT NOT NULL DEFAULT 'legal_document',

    -- Signatory
    signatory_id    TEXT NOT NULL,        -- user_id (persona responsável)
    signatory_name  TEXT NOT NULL,
    signatory_email TEXT NOT NULL,
    signatory_role  TEXT NOT NULL DEFAULT '',  -- advogado, perito, juiz, etc.

    -- Jurisdiction & standard
    jurisdiction    TEXT NOT NULL DEFAULT 'BR',
        -- BR | EU | US | UAE | GLOBAL
    signature_standard TEXT NOT NULL DEFAULT 'ICP-Brasil',
        -- ICP-Brasil | eIDAS-QES | eIDAS-AES | ESIGN | UAE-PASS | Self-Signed
    signature_level TEXT NOT NULL DEFAULT 'QES',
        -- QES | AES | SES | advanced | basic

    -- Certificate / identity
    certificate_issuer  TEXT NOT NULL DEFAULT '',
    certificate_serial  TEXT NOT NULL DEFAULT '',
    certificate_subject TEXT NOT NULL DEFAULT '',
    certificate_valid_from TEXT,
    certificate_valid_until TEXT,

    -- Signature material
    signature_b64   TEXT NOT NULL DEFAULT '',  -- Base64 DER signature
    signature_format TEXT NOT NULL DEFAULT '',
        -- PAdES-LTA | CAdES-LTA | XAdES-LTA | PKCS7 | JAdES | raw

    -- RFC 3161 timestamp
    signed_at       TEXT NOT NULL,
    tsa_timestamp   TEXT,
    tsa_provider    TEXT,
    tsa_serial      TEXT,

    -- Workflow action
    action          TEXT NOT NULL DEFAULT 'signed',
        -- sent | delivered | received | signed | rejected | revoked
    status          TEXT NOT NULL DEFAULT 'valid',
        -- valid | revoked | expired | pending

    -- HDR linkage (optional — AI-assisted actions)
    hdr_id          TEXT,

    -- Audit trail
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

-- Delivery / receipt acknowledgments
-- Each step in the chain (sent → delivered → signed) generates an ack record
CREATE TABLE IF NOT EXISTS signature_acknowledgments (
    ack_id          TEXT PRIMARY KEY,
    sig_id          TEXT NOT NULL REFERENCES document_signatures(sig_id),

    -- Who acknowledged
    acknowledged_by   TEXT NOT NULL,   -- user_id
    acknowledged_name TEXT NOT NULL,
    acknowledged_email TEXT NOT NULL DEFAULT '',

    -- What they did
    action          TEXT NOT NULL DEFAULT 'received',
        -- received | reviewed | accepted | rejected | countersigned

    -- Integrity proof
    ack_hash        TEXT NOT NULL,  -- SHA-256 of (sig_id + acknowledged_by + action + created_at)
    tsa_timestamp   TEXT,

    ip_address      TEXT,
    notes           TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sig_acks_sig
    ON signature_acknowledgments (sig_id);
