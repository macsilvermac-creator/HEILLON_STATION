"""SQLite persistence for the privacy bounded context (LGPD Fase 14)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.privacy.models import (
    AccessLogCreate,
    ConsentBundle,
    ConsentPurpose,
    ConsentRecord,
    ConsentUpdate,
    DPORequest,
    DPORequestCreate,
    DPORequestStatus,
    DPORequestType,
    DPORequestUpdate,
    IncidentCategory,
    IncidentCreate,
    IncidentSeverity,
    IncidentStatus,
    IncidentUpdate,
    LegalBasis,
    LogType,
    PurgeStats,
    RIPDCreate,
    RIPDReport,
    RIPDStatus,
    SecurityIncident,
)

# Default legal basis per consent purpose
_CONSENT_LEGAL_BASIS: dict[ConsentPurpose, LegalBasis] = {
    ConsentPurpose.CORE_SERVICE: LegalBasis.CONTRACT,
    ConsentPurpose.ANALYTICS: LegalBasis.LEGITIMATE_INTEREST,
    ConsentPurpose.AI_TRAINING: LegalBasis.CONSENT,
    ConsentPurpose.MARKETING: LegalBasis.CONSENT,
    ConsentPurpose.THIRD_PARTY: LegalBasis.CONSENT,
    ConsentPurpose.RESEARCH: LegalBasis.CONSENT,
}

# Marco Civil retention periods (in days)
_LOG_RETENTION_DAYS: dict[LogType, int] = {
    LogType.APPLICATION: 180,   # 6 months minimum
    LogType.CONNECTION: 365,    # 1 year minimum
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _parse_json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


# ─── RIPD ──────────────────────────────────────────────────────────────────────


class RIPDRepository:
    """Persistence for RIPD reports."""

    def create(
        self,
        conn: sqlite3.Connection,
        *,
        ripd_id: str,
        organization_id: str,
        created_by: str,
        payload: RIPDCreate,
        dpo_name: str,
        dpo_email: str,
    ) -> RIPDReport:
        now = _now_iso()
        conn.execute(
            """
            INSERT INTO ripd_reports (
                ripd_id, organization_id, created_by,
                title, processing_type, legal_basis, purpose,
                data_categories, data_lifecycle, recipients,
                risks_identified, safeguards,
                dpo_name, dpo_email,
                status, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                ripd_id,
                organization_id,
                created_by,
                payload.title,
                payload.processing_type,
                payload.legal_basis.value,
                payload.purpose,
                json.dumps(payload.data_categories),
                payload.data_lifecycle,
                json.dumps(payload.recipients),
                json.dumps(payload.risks_identified),
                json.dumps(payload.safeguards),
                dpo_name,
                dpo_email,
                RIPDStatus.DRAFT.value,
                now,
            ),
        )
        conn.commit()
        return self.get(conn, ripd_id=ripd_id, organization_id=organization_id)  # type: ignore[return-value]

    def get(
        self, conn: sqlite3.Connection, *, ripd_id: str, organization_id: str
    ) -> RIPDReport | None:
        row = conn.execute(
            "SELECT * FROM ripd_reports WHERE ripd_id=? AND organization_id=?",
            (ripd_id, organization_id),
        ).fetchone()
        return self._hydrate(dict(row)) if row else None

    def list_by_org(
        self, conn: sqlite3.Connection, *, organization_id: str, limit: int = 50, offset: int = 0
    ) -> list[RIPDReport]:
        rows = conn.execute(
            "SELECT * FROM ripd_reports WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (organization_id, limit, offset),
        ).fetchall()
        return [self._hydrate(dict(r)) for r in rows]

    def update_pdf(
        self,
        conn: sqlite3.Connection,
        *,
        ripd_id: str,
        organization_id: str,
        pdf_path: str,
        pdf_checksum: str,
    ) -> None:
        conn.execute(
            "UPDATE ripd_reports SET pdf_path=?, pdf_checksum=?, status=? WHERE ripd_id=? AND organization_id=?",
            (pdf_path, pdf_checksum, RIPDStatus.APPROVED.value, ripd_id, organization_id),
        )
        conn.commit()

    def _hydrate(self, row: dict) -> RIPDReport:
        return RIPDReport(
            ripd_id=row["ripd_id"],
            organization_id=row["organization_id"],
            created_by=row["created_by"],
            title=row["title"],
            processing_type=row["processing_type"],
            legal_basis=LegalBasis(row["legal_basis"]),
            purpose=row["purpose"],
            data_categories=_parse_json_list(row.get("data_categories")),
            data_lifecycle=row["data_lifecycle"],
            recipients=_parse_json_list(row.get("recipients")),
            risks_identified=_parse_json_list(row.get("risks_identified")),
            safeguards=_parse_json_list(row.get("safeguards")),
            dpo_name=row.get("dpo_name", ""),
            dpo_email=row.get("dpo_email", ""),
            status=RIPDStatus(row["status"]),
            pdf_path=row.get("pdf_path"),
            pdf_checksum=row.get("pdf_checksum"),
            created_at=_parse_dt(row["created_at"]) or datetime.now(timezone.utc),
            approved_at=_parse_dt(row.get("approved_at")),
            approved_by=row.get("approved_by"),
        )


# ─── DPO Requests ─────────────────────────────────────────────────────────────


class DPORepository:
    """Persistence for data subject rights requests."""

    def create(
        self,
        conn: sqlite3.Connection,
        *,
        request_id: str,
        organization_id: str,
        payload: DPORequestCreate,
        ip_address: str | None,
        user_agent: str | None,
    ) -> DPORequest:
        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=15)  # LGPD art. 19

        conn.execute(
            """
            INSERT INTO dpo_requests (
                request_id, organization_id,
                requester_name, requester_email, requester_cpf,
                request_type, description,
                status, created_at, due_at,
                ip_address, user_agent
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                request_id,
                organization_id,
                payload.requester_name,
                payload.requester_email,
                payload.requester_cpf,
                payload.request_type.value,
                payload.description,
                DPORequestStatus.PENDING.value,
                now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                due_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                ip_address,
                user_agent,
            ),
        )
        conn.commit()
        return self.get(conn, request_id=request_id, organization_id=organization_id)  # type: ignore[return-value]

    def get(
        self, conn: sqlite3.Connection, *, request_id: str, organization_id: str
    ) -> DPORequest | None:
        row = conn.execute(
            "SELECT * FROM dpo_requests WHERE request_id=? AND organization_id=?",
            (request_id, organization_id),
        ).fetchone()
        return self._hydrate(dict(row)) if row else None

    def list_by_org(
        self,
        conn: sqlite3.Connection,
        *,
        organization_id: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DPORequest]:
        if status:
            rows = conn.execute(
                "SELECT * FROM dpo_requests WHERE organization_id=? AND status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (organization_id, status, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM dpo_requests WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (organization_id, limit, offset),
            ).fetchall()
        return [self._hydrate(dict(r)) for r in rows]

    def update(
        self,
        conn: sqlite3.Connection,
        *,
        request_id: str,
        organization_id: str,
        update: DPORequestUpdate,
    ) -> DPORequest | None:
        fields = []
        values: list[Any] = []
        if update.status is not None:
            fields.append("status=?")
            values.append(update.status.value)
            if update.status in (DPORequestStatus.COMPLETED, DPORequestStatus.REJECTED):
                fields.append("completed_at=?")
                values.append(_now_iso())
        if update.assigned_to is not None:
            fields.append("assigned_to=?")
            values.append(update.assigned_to)
        if update.response_notes is not None:
            fields.append("response_notes=?")
            values.append(update.response_notes)
        if not fields:
            return self.get(conn, request_id=request_id, organization_id=organization_id)
        values.extend([request_id, organization_id])
        conn.execute(
            f"UPDATE dpo_requests SET {', '.join(fields)} WHERE request_id=? AND organization_id=?",
            values,
        )
        conn.commit()
        return self.get(conn, request_id=request_id, organization_id=organization_id)

    def _hydrate(self, row: dict) -> DPORequest:
        return DPORequest(
            request_id=row["request_id"],
            organization_id=row["organization_id"],
            requester_name=row["requester_name"],
            requester_email=row["requester_email"],
            requester_cpf=row.get("requester_cpf"),
            request_type=DPORequestType(row["request_type"]),
            description=row["description"],
            status=DPORequestStatus(row["status"]),
            assigned_to=row.get("assigned_to"),
            response_notes=row.get("response_notes"),
            created_at=_parse_dt(row["created_at"]) or datetime.now(timezone.utc),
            due_at=_parse_dt(row["due_at"]) or datetime.now(timezone.utc),
            completed_at=_parse_dt(row.get("completed_at")),
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
        )


# ─── Security Incidents ────────────────────────────────────────────────────────


class IncidentRepository:
    """Persistence for ANPD security incidents."""

    def create(
        self,
        conn: sqlite3.Connection,
        *,
        incident_id: str,
        organization_id: str,
        detected_by: str,
        payload: IncidentCreate,
    ) -> SecurityIncident:
        now = datetime.now(timezone.utc)
        anpd_due = now + timedelta(hours=72)
        retain_until = now + timedelta(days=365 * 5)  # 5 years LGPD art. 48

        conn.execute(
            """
            INSERT INTO security_incidents (
                incident_id, organization_id,
                detected_at, detected_by,
                category, description, severity,
                affected_subjects_count, affected_data_types, potential_harm,
                status, anpd_notification_due_at,
                containment_measures,
                created_at, updated_at, retain_until
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                incident_id,
                organization_id,
                now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                detected_by,
                payload.category.value,
                payload.description,
                payload.severity.value,
                payload.affected_subjects_count,
                json.dumps(payload.affected_data_types),
                payload.potential_harm,
                IncidentStatus.DETECTED.value,
                anpd_due.strftime("%Y-%m-%dT%H:%M:%SZ"),
                payload.containment_measures,
                now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                retain_until.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
        conn.commit()
        return self.get(conn, incident_id=incident_id, organization_id=organization_id)  # type: ignore[return-value]

    def get(
        self, conn: sqlite3.Connection, *, incident_id: str, organization_id: str
    ) -> SecurityIncident | None:
        row = conn.execute(
            "SELECT * FROM security_incidents WHERE incident_id=? AND organization_id=?",
            (incident_id, organization_id),
        ).fetchone()
        return self._hydrate(dict(row)) if row else None

    def list_by_org(
        self,
        conn: sqlite3.Connection,
        *,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SecurityIncident]:
        rows = conn.execute(
            "SELECT * FROM security_incidents WHERE organization_id=? ORDER BY detected_at DESC LIMIT ? OFFSET ?",
            (organization_id, limit, offset),
        ).fetchall()
        return [self._hydrate(dict(r)) for r in rows]

    def update(
        self,
        conn: sqlite3.Connection,
        *,
        incident_id: str,
        organization_id: str,
        update: IncidentUpdate,
        closed_by: str | None = None,
    ) -> SecurityIncident | None:
        now = _now_iso()
        fields = ["updated_at=?"]
        values: list[Any] = [now]

        def _add(col: str, val: Any) -> None:
            fields.append(f"{col}=?")
            values.append(val)

        if update.status is not None:
            _add("status", update.status.value)
            if update.status == IncidentStatus.CLOSED:
                _add("closed_at", now)
                if closed_by:
                    _add("closed_by", closed_by)
        if update.anpd_notified_at is not None:
            _add("anpd_notified_at", update.anpd_notified_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if update.anpd_notification_ref is not None:
            _add("anpd_notification_ref", update.anpd_notification_ref)
        if update.subjects_notified_at is not None:
            _add("subjects_notified_at", update.subjects_notified_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if update.notification_method is not None:
            _add("notification_method", update.notification_method)
        if update.containment_measures is not None:
            _add("containment_measures", update.containment_measures)
        if update.remediation_plan is not None:
            _add("remediation_plan", update.remediation_plan)

        values.extend([incident_id, organization_id])
        conn.execute(
            f"UPDATE security_incidents SET {', '.join(fields)} WHERE incident_id=? AND organization_id=?",
            values,
        )
        conn.commit()
        return self.get(conn, incident_id=incident_id, organization_id=organization_id)

    def _hydrate(self, row: dict) -> SecurityIncident:
        now = datetime.now(timezone.utc)
        anpd_due = _parse_dt(row.get("anpd_notification_due_at"))
        anpd_notified = _parse_dt(row.get("anpd_notified_at"))
        is_overdue = bool(
            anpd_due and anpd_due < now and not anpd_notified
        )
        return SecurityIncident(
            incident_id=row["incident_id"],
            organization_id=row["organization_id"],
            detected_at=_parse_dt(row["detected_at"]) or now,
            detected_by=row["detected_by"],
            category=IncidentCategory(row["category"]),
            description=row["description"],
            severity=IncidentSeverity(row["severity"]),
            affected_subjects_count=row.get("affected_subjects_count", 0),
            affected_data_types=_parse_json_list(row.get("affected_data_types")),
            potential_harm=row.get("potential_harm"),
            status=IncidentStatus(row["status"]),
            anpd_notification_due_at=anpd_due,
            anpd_notified_at=anpd_notified,
            anpd_notification_ref=row.get("anpd_notification_ref"),
            subjects_notified_at=_parse_dt(row.get("subjects_notified_at")),
            notification_method=row.get("notification_method"),
            containment_measures=row.get("containment_measures"),
            remediation_plan=row.get("remediation_plan"),
            created_at=_parse_dt(row["created_at"]) or now,
            updated_at=_parse_dt(row["updated_at"]) or now,
            closed_at=_parse_dt(row.get("closed_at")),
            closed_by=row.get("closed_by"),
            retain_until=_parse_dt(row["retain_until"]) or now,
            is_overdue_anpd=is_overdue,
        )


# ─── Consent ──────────────────────────────────────────────────────────────────


class ConsentRepository:
    """Persistence for granular consent records (LGPD art. 8)."""

    PRIVACY_POLICY_VERSION = "1.0"

    def get_bundle(
        self,
        conn: sqlite3.Connection,
        *,
        user_id: str,
        organization_id: str,
    ) -> ConsentBundle:
        rows = conn.execute(
            "SELECT * FROM consent_records WHERE user_id=? AND organization_id=?",
            (user_id, organization_id),
        ).fetchall()
        return ConsentBundle(
            user_id=user_id,
            records=[self._hydrate(dict(r)) for r in rows],
        )

    def set_consent(
        self,
        conn: sqlite3.Connection,
        *,
        consent_id: str,
        user_id: str,
        organization_id: str,
        update: ConsentUpdate,
        ip_address: str | None,
        user_agent: str | None,
    ) -> ConsentRecord:
        now = _now_iso()
        legal_basis = _CONSENT_LEGAL_BASIS.get(update.purpose, LegalBasis.CONSENT)
        granted_at = now if update.granted else None
        revoked_at = now if not update.granted else None

        conn.execute(
            """
            INSERT INTO consent_records (
                consent_id, user_id, organization_id,
                purpose, legal_basis,
                granted, granted_at, revoked_at,
                version, ip_address, user_agent,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(user_id, purpose) DO UPDATE SET
                granted=excluded.granted,
                granted_at=excluded.granted_at,
                revoked_at=excluded.revoked_at,
                updated_at=excluded.updated_at,
                ip_address=excluded.ip_address,
                user_agent=excluded.user_agent
            """,
            (
                consent_id,
                user_id,
                organization_id,
                update.purpose.value,
                legal_basis.value,
                1 if update.granted else 0,
                granted_at,
                revoked_at,
                self.PRIVACY_POLICY_VERSION,
                ip_address,
                user_agent,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM consent_records WHERE user_id=? AND purpose=?",
            (user_id, update.purpose.value),
        ).fetchone()
        return self._hydrate(dict(row))

    def _hydrate(self, row: dict) -> ConsentRecord:
        now = datetime.now(timezone.utc)
        return ConsentRecord(
            consent_id=row["consent_id"],
            user_id=row["user_id"],
            organization_id=row["organization_id"],
            purpose=ConsentPurpose(row["purpose"]),
            legal_basis=LegalBasis(row["legal_basis"]),
            granted=bool(row["granted"]),
            granted_at=_parse_dt(row.get("granted_at")),
            revoked_at=_parse_dt(row.get("revoked_at")),
            version=row.get("version", "1.0"),
            created_at=_parse_dt(row["created_at"]) or now,
            updated_at=_parse_dt(row["updated_at"]) or now,
        )


# ─── Access log purge ──────────────────────────────────────────────────────────


class AccessLogRepository:
    """Write access events and run Marco Civil log purge."""

    def write(
        self,
        conn: sqlite3.Connection,
        *,
        log_id: str,
        payload: AccessLogCreate,
    ) -> None:
        retention = _LOG_RETENTION_DAYS[payload.log_type]
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=retention)
        conn.execute(
            """
            INSERT INTO access_logs (
                log_id, organization_id, user_id, log_type,
                event_type, resource, ip_address, user_agent,
                response_code, created_at, expires_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                log_id,
                payload.organization_id,
                payload.user_id,
                payload.log_type.value,
                payload.event_type,
                payload.resource,
                payload.ip_address,
                payload.user_agent,
                payload.response_code,
                now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
        conn.commit()

    def purge_expired(self, conn: sqlite3.Connection) -> PurgeStats:
        """Delete non-held logs past their expires_at (Marco Civil compliance)."""
        now = datetime.now(timezone.utc)
        cutoff = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        result = conn.execute(
            "DELETE FROM access_logs WHERE expires_at < ? AND judicial_hold = 0",
            (cutoff,),
        )
        count = result.rowcount
        conn.commit()
        return PurgeStats(purged_count=count, purge_cutoff=now)
