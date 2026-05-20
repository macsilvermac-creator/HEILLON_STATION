BEGIN;

CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    authorized_agents_json TEXT NOT NULL DEFAULT '[]',
    dag_json TEXT NOT NULL,
    normative_json TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    estimated_cost_gas REAL DEFAULT 0,
    created_at TEXT NOT NULL,
    approved_at TEXT,
    executed_at TEXT,
    completed_at TEXT,
    hdrs_generated_json TEXT NOT NULL DEFAULT '[]',
    mission_plan_snapshot TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_missions_created ON missions(created_at);
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);

COMMIT;
