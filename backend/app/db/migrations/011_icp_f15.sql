-- Migration 011: Fase 15 — ICP-Brasil Qualificada + PDF/A-3
-- Signature records, ICP-Brasil certificate verification, document signature chain

-- ─── ICP-Brasil Signature Records ────────────────────────────────────────────
-- Stores CAdES/PAdES signatures (ICP-Brasil A1/A3) attached to HDRs or packages
CREATE TABLE IF NOT EXISTS icp_signatures (
    sig_id           TEXT PRIMARY KEY,
    entity_type      TEXT NOT NULL,  -- 'hdr' | 'forensic_package' | 'ripd'
    entity_id        TEXT NOT NULL,  -- hdr_id / package_id / ripd_id
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    -- Certificate info
    cert_subject     TEXT NOT NULL,
    cert_issuer      TEXT NOT NULL,
    cert_serial      TEXT NOT NULL,
    cert_not_before  TEXT NOT NULL,
    cert_not_after   TEXT NOT NULL,
    cert_type        TEXT NOT NULL DEFAULT 'A1',  -- 'A1' | 'A3'
    icp_brasil       INTEGER NOT NULL DEFAULT 0,  -- 1 = ICP-Brasil chain verified
    -- Signature
    signature_type   TEXT NOT NULL DEFAULT 'CAdES-BES',  -- 'CAdES-BES' | 'PAdES-BES' | 'EdDSA-detached'
    signature_b64    TEXT NOT NULL,  -- Base64 DER signature bytes
    signed_hash      TEXT NOT NULL,  -- SHA-256 of the signed content
    signed_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- TSA (optional — for signatures with embedded timestamp)
    tsa_token_b64    TEXT,           -- RFC3161 token embedded in the signature
    tsa_provider     TEXT,
    -- PDF/A-3 attachment (for PDF packages)
    pdfa3_path       TEXT,           -- path to PDF/A-3 with embedded signature
    pdfa3_checksum   TEXT,
    -- metadata
    signed_by        TEXT NOT NULL,  -- user_id
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_icp_sig_entity ON icp_signatures(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_icp_sig_org ON icp_signatures(organization_id);
CREATE INDEX IF NOT EXISTS idx_icp_sig_cert_serial ON icp_signatures(cert_serial);

-- ─── ICP-Brasil Document Verification ────────────────────────────────────────
-- Stores results of ICP-Brasil chain verification for ingested documents
CREATE TABLE IF NOT EXISTS icp_verifications (
    verify_id         TEXT PRIMARY KEY,
    hdr_id            TEXT NOT NULL,
    organization_id   TEXT NOT NULL DEFAULT 'org_default',
    -- result
    icp_verified      INTEGER NOT NULL DEFAULT 0,  -- 1 = valid ICP-Brasil chain
    signer_name       TEXT,
    signer_cpf_cnpj   TEXT,
    cert_issuer       TEXT,
    cert_serial       TEXT,
    cert_type         TEXT,  -- 'A1' | 'A2' | 'A3' | 'A4'
    signing_time      TEXT,
    signature_valid   INTEGER NOT NULL DEFAULT 0,
    cert_chain_valid  INTEGER NOT NULL DEFAULT 0,
    -- raw details
    details_json      TEXT NOT NULL DEFAULT '{}',
    -- timestamps
    verified_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    verified_by       TEXT  -- user_id or 'system'
);

CREATE INDEX IF NOT EXISTS idx_icp_verify_hdr ON icp_verifications(hdr_id);
CREATE INDEX IF NOT EXISTS idx_icp_verify_org ON icp_verifications(organization_id);

-- ─── PDF/A-3 Package Registry ─────────────────────────────────────────────────
-- Tracks PDF/A-3 files with embedded attachments (chains.json) per forensic package
CREATE TABLE IF NOT EXISTS pdfa3_packages (
    pdfa3_id         TEXT PRIMARY KEY,
    package_id       TEXT NOT NULL,   -- forensic_packages.package_id
    organization_id  TEXT NOT NULL DEFAULT 'org_default',
    -- file
    pdf_path         TEXT NOT NULL,
    pdf_checksum     TEXT NOT NULL,   -- SHA-256 of PDF/A-3 file
    pdf_version      TEXT NOT NULL DEFAULT 'A-3',
    -- embedded attachments
    attachments_json TEXT NOT NULL DEFAULT '[]',  -- [{name, description, checksum}]
    -- signature status
    is_signed        INTEGER NOT NULL DEFAULT 0,
    sig_id           TEXT,            -- icp_signatures.sig_id if signed
    -- metadata
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_by       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pdfa3_package ON pdfa3_packages(package_id);
