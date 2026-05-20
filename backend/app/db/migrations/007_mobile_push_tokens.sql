-- Mobile push subscription storage (Phase 8) — MVP bridge until VAPID delivery is wired.
CREATE TABLE IF NOT EXISTS mobile_push_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    subscription_json TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id)
);
