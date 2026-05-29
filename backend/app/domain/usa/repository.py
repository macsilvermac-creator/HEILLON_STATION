"""USA regulatory compliance repository layer."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Colorado AI Act ────────────────────────────────────────────────────────────


class ColoradoAIRepository:
    def create(
        self,
        conn: Any,
        *,
        record_id: str,
        organization_id: str = "org_default",
        ai_system_name: str,
        ai_system_version: str = "1.0",
        developer_name: str = "",
        deployer_name: str = "",
        risk_tier: str = "limited",
        high_risk_category: str | None = None,
        consequential_decision_desc: str = "",
        impact_assessment_done: bool = False,
        impact_assessment_date: str | None = None,
        impact_assessment_ref: str = "",
        bias_audit_done: bool = False,
        bias_audit_date: str | None = None,
        bias_audit_provider: str = "",
        consumer_notification_text: str = "",
        opt_out_mechanism: str = "",
        appeal_process_available: bool = False,
        monitoring_plan: str = "",
        created_by: str,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO colorado_ai_records (
                record_id, organization_id, ai_system_name, ai_system_version,
                developer_name, deployer_name, risk_tier, high_risk_category,
                consequential_decision_desc,
                impact_assessment_done, impact_assessment_date, impact_assessment_ref,
                bias_audit_done, bias_audit_date, bias_audit_provider,
                consumer_notification_text, opt_out_mechanism, appeal_process_available,
                monitoring_plan, incident_log, status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record_id,
                organization_id,
                ai_system_name,
                ai_system_version,
                developer_name,
                deployer_name,
                risk_tier,
                high_risk_category,
                consequential_decision_desc,
                int(impact_assessment_done),
                impact_assessment_date,
                impact_assessment_ref,
                int(bias_audit_done),
                bias_audit_date,
                bias_audit_provider,
                consumer_notification_text,
                opt_out_mechanism,
                int(appeal_process_available),
                monitoring_plan,
                "[]",
                "active",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM colorado_ai_records WHERE record_id=?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self,
        conn: Any,
        organization_id: str,
        *,
        risk_tier: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if risk_tier:
            rows = conn.execute(
                """SELECT * FROM colorado_ai_records
                   WHERE organization_id=? AND risk_tier=?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (organization_id, risk_tier, limit, skip),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM colorado_ai_records
                   WHERE organization_id=?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (organization_id, limit, skip),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, conn: Any, record_id: str, status: str) -> None:
        now = _now()
        conn.execute(
            "UPDATE colorado_ai_records SET status=?, updated_at=? WHERE record_id=?",
            (status, now, record_id),
        )


# ── CCPA / CPRA ───────────────────────────────────────────────────────────────


class CCPAConsentRepository:
    def create(
        self,
        conn: Any,
        *,
        consent_id: str,
        organization_id: str = "org_default",
        consumer_id: str,
        consumer_email: str,
        consumer_state: str = "CA",
        data_categories: list[str] | None = None,
        processing_purposes: list[str] | None = None,
        consent_type: str = "opt_in",
        sensitive_data_consent: bool = False,
        automated_decision_consent: bool = False,
        sale_of_personal_info_consent: bool = False,
        sharing_for_cross_context: bool = False,
        consent_text: str = "",
        ip_address: str | None = None,
        expires_at: str | None = None,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO ccpa_consent_records (
                consent_id, organization_id, consumer_id, consumer_email,
                consumer_state, data_categories, processing_purposes, consent_type,
                sensitive_data_consent, automated_decision_consent,
                sale_of_personal_info_consent, sharing_for_cross_context,
                consent_text, ip_address, status, expires_at,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                consent_id,
                organization_id,
                consumer_id,
                consumer_email,
                consumer_state,
                json.dumps(data_categories or []),
                json.dumps(processing_purposes or []),
                consent_type,
                int(sensitive_data_consent),
                int(automated_decision_consent),
                int(sale_of_personal_info_consent),
                int(sharing_for_cross_context),
                consent_text,
                ip_address,
                "active",
                expires_at,
                now,
                now,
            ),
        )

    def get(self, conn: Any, consent_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM ccpa_consent_records WHERE consent_id=?", (consent_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM ccpa_consent_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def withdraw(self, conn: Any, consent_id: str, *, reason: str = "") -> None:
        now = _now()
        conn.execute(
            """UPDATE ccpa_consent_records
               SET status='withdrawn', withdrawn_at=?, withdrawal_reason=?, updated_at=?
               WHERE consent_id=?""",
            (now, reason, now, consent_id),
        )


# ── ABA Compliance ────────────────────────────────────────────────────────────


class ABAComplianceRepository:
    def create(
        self,
        conn: Any,
        *,
        log_id: str,
        organization_id: str = "org_default",
        matter_ref: str,
        attorney_id: str,
        attorney_name: str = "",
        ai_tool_name: str = "",
        ai_tool_version: str = "",
        ai_tool_provider: str = "",
        rule_11_competence: bool = False,
        rule_16_confidentiality: bool = False,
        rule_34_fairness: bool = False,
        rule_53_supervision: bool = False,
        client_disclosure_made: bool = False,
        state_bar: str = "CA",
        state_specific_rule_ref: str = "",
        state_specific_notes: str = "",
        output_reviewed: bool = False,
        review_notes: str = "",
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO aba_compliance_log (
                log_id, organization_id, matter_ref, attorney_id, attorney_name,
                ai_tool_name, ai_tool_version, ai_tool_provider,
                rule_11_competence, rule_16_confidentiality,
                rule_34_fairness, rule_53_supervision, client_disclosure_made,
                state_bar, state_specific_rule_ref, state_specific_notes,
                output_reviewed, review_notes, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                log_id,
                organization_id,
                matter_ref,
                attorney_id,
                attorney_name,
                ai_tool_name,
                ai_tool_version,
                ai_tool_provider,
                int(rule_11_competence),
                int(rule_16_confidentiality),
                int(rule_34_fairness),
                int(rule_53_supervision),
                int(client_disclosure_made),
                state_bar,
                state_specific_rule_ref,
                state_specific_notes,
                int(output_reviewed),
                review_notes,
                now,
            ),
        )

    def get(self, conn: Any, log_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM aba_compliance_log WHERE log_id=?", (log_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM aba_compliance_log
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


# ── NIST AI RMF ───────────────────────────────────────────────────────────────


class NISTRMFRepository:
    def create(
        self,
        conn: Any,
        *,
        rmf_id: str,
        organization_id: str = "org_default",
        ai_system_ref: str,
        ai_system_name: str = "",
        ai_system_version: str = "1.0",
        govern_policies_defined: bool = False,
        govern_roles_assigned: bool = False,
        govern_risk_tolerance_set: bool = False,
        govern_training_completed: bool = False,
        govern_notes: str = "",
        map_intended_use: str = "",
        map_context_established: bool = False,
        map_risks_identified: list | None = None,
        map_stakeholders_consulted: bool = False,
        map_notes: str = "",
        measure_metrics_defined: bool = False,
        measure_testing_completed: bool = False,
        measure_bias_evaluated: bool = False,
        measure_performance_score: float | None = None,
        measure_trustworthiness: int | None = None,
        measure_notes: str = "",
        manage_risk_responses: list | None = None,
        manage_residual_risks: list | None = None,
        manage_monitoring_plan: str = "",
        manage_incident_plan: str = "",
        manage_notes: str = "",
        profile_tier: str = "tier-2",
        created_by: str,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO nist_ai_rmf_records (
                rmf_id, organization_id, ai_system_ref, ai_system_name, ai_system_version,
                govern_policies_defined, govern_roles_assigned,
                govern_risk_tolerance_set, govern_training_completed, govern_notes,
                map_intended_use, map_context_established, map_risks_identified,
                map_stakeholders_consulted, map_notes,
                measure_metrics_defined, measure_testing_completed, measure_bias_evaluated,
                measure_performance_score, measure_trustworthiness, measure_notes,
                manage_risk_responses, manage_residual_risks,
                manage_monitoring_plan, manage_incident_plan, manage_notes,
                profile_tier, status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                rmf_id,
                organization_id,
                ai_system_ref,
                ai_system_name,
                ai_system_version,
                int(govern_policies_defined),
                int(govern_roles_assigned),
                int(govern_risk_tolerance_set),
                int(govern_training_completed),
                govern_notes,
                map_intended_use,
                int(map_context_established),
                json.dumps(map_risks_identified or []),
                int(map_stakeholders_consulted),
                map_notes,
                int(measure_metrics_defined),
                int(measure_testing_completed),
                int(measure_bias_evaluated),
                measure_performance_score,
                measure_trustworthiness,
                measure_notes,
                json.dumps(manage_risk_responses or []),
                json.dumps(manage_residual_risks or []),
                manage_monitoring_plan,
                manage_incident_plan,
                manage_notes,
                profile_tier,
                "active",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, rmf_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM nist_ai_rmf_records WHERE rmf_id=?", (rmf_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM nist_ai_rmf_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


# ── ESIGN Audit Log ───────────────────────────────────────────────────────────


class ESIGNAuditRepository:
    def create(
        self,
        conn: Any,
        *,
        audit_id: str,
        organization_id: str = "org_default",
        sig_id: str | None = None,
        event_type: str,
        event_sequence: int = 1,
        actor_id: str,
        actor_name: str = "",
        actor_email: str,
        actor_ip: str | None = None,
        document_ref: str = "",
        document_hash: str | None = None,
        event_data: dict | None = None,
    ) -> str:
        """Create an ESIGN audit entry. Returns event_hash."""
        now = _now()
        raw = json.dumps(event_data or {}, sort_keys=True)
        event_hash = hashlib.sha256(
            f"{audit_id}:{actor_id}:{event_type}:{now}:{raw}".encode()
        ).hexdigest()
        conn.execute(
            """INSERT INTO esign_audit_log (
                audit_id, organization_id, sig_id, event_type, event_sequence,
                actor_id, actor_name, actor_email, actor_ip,
                document_ref, document_hash, event_hash, event_data, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                audit_id,
                organization_id,
                sig_id,
                event_type,
                event_sequence,
                actor_id,
                actor_name,
                actor_email,
                actor_ip,
                document_ref,
                document_hash,
                event_hash,
                raw,
                now,
            ),
        )
        return event_hash

    def list_by_doc(
        self, conn: Any, organization_id: str, document_ref: str
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM esign_audit_log
               WHERE organization_id=? AND document_ref=?
               ORDER BY event_sequence ASC, created_at ASC""",
            (organization_id, document_ref),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM esign_audit_log
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (organization_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]
