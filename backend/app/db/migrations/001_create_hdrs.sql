BEGIN;

CREATE TABLE IF NOT EXISTS hdrs (
    hdr_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    previous_hdr TEXT,
    hdr_type TEXT NOT NULL,
    timestamp_iso TEXT NOT NULL,
    canonical_hash TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hdr_mission ON hdrs(mission_id);
CREATE INDEX IF NOT EXISTS idx_hdr_previous ON hdrs(previous_hdr);
CREATE INDEX IF NOT EXISTS idx_hdr_type ON hdrs(hdr_type);
CREATE INDEX IF NOT EXISTS idx_hdr_ts ON hdrs(timestamp_iso);

COMMIT;
