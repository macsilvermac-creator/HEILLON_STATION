-- Beta feedback survey (Fase 32)
--
-- Captures voluntary product feedback from authenticated beta users across
-- four axes (usabilidade, experiência, funcionalidades, "entrega o que promete")
-- plus an NPS score and free-text fields.
--
-- Privacy posture: this is the user's OWN product opinion, not third-party PII.
-- Identity columns (organization_id, user_id) exist for de-duplication and
-- follow-up only; the admin SUMMARY endpoint never joins identity to the
-- free-text comments (aggregate-only, de-identified — consistent with /admin).
--
-- Scores are validated at the application layer (Pydantic 0..10) rather than
-- via CHECK constraints, to avoid SQLite/Postgres dialect quirks. NULL means
-- "respondent skipped this axis".

BEGIN;

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

COMMIT;
