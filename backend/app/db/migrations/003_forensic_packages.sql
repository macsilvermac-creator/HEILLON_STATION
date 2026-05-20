BEGIN;

CREATE TABLE IF NOT EXISTS forensic_packages (
    package_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    status TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    integrity_hash TEXT NOT NULL,
    pdf_path TEXT NOT NULL,
    json_chain_path TEXT NOT NULL,
    pdf_checksum TEXT NOT NULL,
    json_chain_checksum TEXT NOT NULL,
    created_at TEXT NOT NULL,
    generated_by TEXT NOT NULL,
    verification_url_snapshot TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_forensic_pkg_mission ON forensic_packages(mission_id);

COMMIT;
