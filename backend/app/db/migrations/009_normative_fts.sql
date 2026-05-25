-- Migration 009: Normative corpus persistence + FTS5 full-text search
-- Safe to run multiple times (all DDL uses IF NOT EXISTS)

CREATE TABLE IF NOT EXISTS normative_rules (
    rule_id             TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    description         TEXT NOT NULL,
    category            TEXT NOT NULL,
    condition_text      TEXT NOT NULL,
    action_on_violation TEXT NOT NULL,
    priority            INTEGER NOT NULL DEFAULT 50,
    enabled             INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- FTS5 virtual table for full-text search across name, description and condition
CREATE VIRTUAL TABLE IF NOT EXISTS normative_rules_fts USING fts5(
    rule_id UNINDEXED,
    name,
    description,
    condition_text,
    content=normative_rules,
    content_rowid=rowid
);

-- Keep FTS index in sync via triggers
CREATE TRIGGER IF NOT EXISTS normative_rules_ai
AFTER INSERT ON normative_rules BEGIN
    INSERT INTO normative_rules_fts(rowid, rule_id, name, description, condition_text)
    VALUES (NEW.rowid, NEW.rule_id, NEW.name, NEW.description, NEW.condition_text);
END;

CREATE TRIGGER IF NOT EXISTS normative_rules_ad
AFTER DELETE ON normative_rules BEGIN
    INSERT INTO normative_rules_fts(normative_rules_fts, rowid, rule_id, name, description, condition_text)
    VALUES ('delete', OLD.rowid, OLD.rule_id, OLD.name, OLD.description, OLD.condition_text);
END;

CREATE TRIGGER IF NOT EXISTS normative_rules_au
AFTER UPDATE ON normative_rules BEGIN
    INSERT INTO normative_rules_fts(normative_rules_fts, rowid, rule_id, name, description, condition_text)
    VALUES ('delete', OLD.rowid, OLD.rule_id, OLD.name, OLD.description, OLD.condition_text);
    INSERT INTO normative_rules_fts(rowid, rule_id, name, description, condition_text)
    VALUES (NEW.rowid, NEW.rule_id, NEW.name, NEW.description, NEW.condition_text);
END;
