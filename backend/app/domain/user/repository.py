"""SQLite persistence façade for EASY operators."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from app.domain.user.models import UserRecord, UserRole


class UserRepository:
    """Append-oriented user catalogue with bcrypt digests."""

    @staticmethod
    def create_user(
        conn: sqlite3.Connection,
        *,
        email: str,
        name: str,
        hashed_password: str,
        role: UserRole,
        organization_id: str,
        user_id: str | None = None,
        is_active: bool = True,
    ) -> UserRecord:
        """Insert a sanitized operator dossier keyed by EASY UUID."""

        resolved_id = user_id or f"user_{uuid.uuid4().hex}"
        created_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO users (
                    user_id, email, name, role, organization_id,
                    hashed_password, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resolved_id,
                email.lower(),
                name,
                role.value,
                organization_id,
                hashed_password,
                bool(is_active),
                created_iso,
            ),
        )
        return UserRepository.get_by_id(conn, resolved_id)

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, user_id: str) -> UserRecord | None:
        row = conn.execute(
            """SELECT user_id, email, name, role, organization_id,
                      hashed_password, is_active, created_at
               FROM users WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
        return UserRepository._row_to_record(row) if row else None

    @staticmethod
    def get_by_email(conn: sqlite3.Connection, email: str) -> UserRecord | None:
        row = conn.execute(
            """SELECT user_id, email, name, role, organization_id,
                      hashed_password, is_active, created_at
               FROM users WHERE email = ?""",
            (email.lower(),),
        ).fetchone()
        return UserRepository._row_to_record(row) if row else None

    @staticmethod
    def ensure_organization(
        conn: sqlite3.Connection, *, organization_id: str, name: str
    ) -> None:
        snapshot = conn.execute(
            "SELECT organization_id FROM organizations WHERE organization_id = ?",
            (organization_id,),
        ).fetchone()
        if snapshot:
            return
        created_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO organizations (organization_id, name, settings_json, created_at)
                   VALUES (?, ?, ?, ?)
            """,
            (organization_id, name, json.dumps({}, separators=(",", ":")), created_iso),
        )

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> UserRecord:
        ts_value = datetime.fromisoformat(str(row["created_at"]))
        if ts_value.tzinfo is None:
            ts_value = ts_value.replace(tzinfo=timezone.utc)
        return UserRecord(
            user_id=str(row["user_id"]),
            email=str(row["email"]),
            name=str(row["name"]),
            role=UserRole(str(row["role"])),
            organization_id=str(row["organization_id"]),
            hashed_password=str(row["hashed_password"]),
            is_active=bool(row["is_active"]),
            created_at=ts_value,
        )
