"""SQLite façade for ephemeral mobile bridge tables."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone


class MobileBridgeRepository:
    """Persists handset push artefacts until dedicated notification plane ships."""

    @staticmethod
    def upsert_push_token(
        conn: sqlite3.Connection, *, user_id: str, subscription_json: str
    ) -> None:
        """Replace single subscription envelope per judiciary operator."""

        payload = subscription_json.strip()
        json.loads(payload)  # validate JSON early
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """INSERT INTO mobile_push_tokens (user_id, subscription_json, updated_at)
                   VALUES (?, ?, ?)
                 ON CONFLICT(user_id)
                 DO UPDATE SET subscription_json = excluded.subscription_json,
                               updated_at = excluded.updated_at
            """,
            (user_id, payload, now),
        )
