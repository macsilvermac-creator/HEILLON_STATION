"""ISO 42001 AIMS + FRIA repository layer."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── ISO 42001 AIMS ────────────────────────────────────────────────────────────


class ISO42001Repository:
    def create(
        self,
        conn: Any,
        *,
        aims_id: str,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
        ai_system_version: str = "1.0",
        # Clause 4
        c4_internal_issues: str = "",
        c4_external_issues: str = "",
        c4_interested_parties: list | None = None,
        c4_aims_scope: str = "",
        c4_ai_policy_defined: bool = False,
        # Clause 5
        c5_top_mgmt_commitment: bool = False,
        c5_ai_policy_text: str = "",
        c5_roles_defined: bool = False,
        c5_dpo_appointed: bool = False,
        # Clause 6
        c6_risks_assessed: bool = False,
        c6_opportunities_noted: bool = False,
        c6_objectives_set: list | None = None,
        c6_action_plans: list | None = None,
        # Clause 7
        c7_resources_allocated: bool = False,
        c7_competence_verified: bool = False,
        c7_awareness_training: bool = False,
        c7_documentation_maintained: bool = False,
        # Clause 8
        c8_operational_controls: bool = False,
        c8_ai_system_lifecycle: str = "",
        c8_data_quality_assured: bool = False,
        c8_human_oversight_active: bool = False,
        c8_incident_response_plan: str = "",
        # Clause 9
        c9_monitoring_metrics: dict | None = None,
        c9_internal_audit_done: bool = False,
        c9_mgmt_review_done: bool = False,
        c9_last_audit_date: str | None = None,
        # Clause 10
        c10_nonconformities: list | None = None,
        c10_corrective_actions: list | None = None,
        c10_continual_improvement_plan: str = "",
        # Annex A
        annex_a2: bool = False,
        annex_a3: bool = False,
        annex_a4: bool = False,
        annex_a5: bool = False,
        annex_a6: bool = False,
        annex_a7: bool = False,
        annex_a8: bool = False,
        annex_a9: bool = False,
        # Certification
        certification_body: str | None = None,
        certification_status: str = "not_started",
        created_by: str,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO iso42001_aims_records (
                aims_id, organization_id, ai_system_ref, ai_system_name, ai_system_version,
                c4_internal_issues, c4_external_issues, c4_interested_parties,
                c4_aims_scope, c4_ai_policy_defined,
                c5_top_mgmt_commitment, c5_ai_policy_text, c5_roles_defined, c5_dpo_appointed,
                c6_risks_assessed, c6_opportunities_noted, c6_objectives_set, c6_action_plans,
                c7_resources_allocated, c7_competence_verified, c7_awareness_training,
                c7_documentation_maintained,
                c8_operational_controls, c8_ai_system_lifecycle, c8_data_quality_assured,
                c8_human_oversight_active, c8_incident_response_plan,
                c9_monitoring_metrics, c9_internal_audit_done, c9_mgmt_review_done,
                c9_last_audit_date,
                c10_nonconformities, c10_corrective_actions, c10_continual_improvement_plan,
                annex_a2_dev_policy, annex_a3_internal_audit, annex_a4_impact_assess,
                annex_a5_lifecycle_mgmt, annex_a6_data_mgmt, annex_a7_training_data,
                annex_a8_documentation, annex_a9_logging,
                certification_body, certification_status,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                aims_id,
                organization_id,
                ai_system_ref,
                ai_system_name,
                ai_system_version,
                c4_internal_issues,
                c4_external_issues,
                json.dumps(c4_interested_parties or []),
                c4_aims_scope,
                int(c4_ai_policy_defined),
                int(c5_top_mgmt_commitment),
                c5_ai_policy_text,
                int(c5_roles_defined),
                int(c5_dpo_appointed),
                int(c6_risks_assessed),
                int(c6_opportunities_noted),
                json.dumps(c6_objectives_set or []),
                json.dumps(c6_action_plans or []),
                int(c7_resources_allocated),
                int(c7_competence_verified),
                int(c7_awareness_training),
                int(c7_documentation_maintained),
                int(c8_operational_controls),
                c8_ai_system_lifecycle,
                int(c8_data_quality_assured),
                int(c8_human_oversight_active),
                c8_incident_response_plan,
                json.dumps(c9_monitoring_metrics or {}),
                int(c9_internal_audit_done),
                int(c9_mgmt_review_done),
                c9_last_audit_date,
                json.dumps(c10_nonconformities or []),
                json.dumps(c10_corrective_actions or []),
                c10_continual_improvement_plan,
                int(annex_a2),
                int(annex_a3),
                int(annex_a4),
                int(annex_a5),
                int(annex_a6),
                int(annex_a7),
                int(annex_a8),
                int(annex_a9),
                certification_body,
                certification_status,
                "active",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, aims_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM iso42001_aims_records WHERE aims_id=?", (aims_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM iso42001_aims_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_certification(
        self,
        conn: Any,
        aims_id: str,
        *,
        certification_status: str,
        conformity_score: int | None = None,
        certification_body: str | None = None,
        certificate_number: str | None = None,
        certificate_expires_at: str | None = None,
    ) -> None:
        now = _now()
        conn.execute(
            """UPDATE iso42001_aims_records
               SET certification_status=?, conformity_score=?, certification_body=?,
                   certificate_number=?, certificate_expires_at=?, updated_at=?
               WHERE aims_id=?""",
            (
                certification_status,
                conformity_score,
                certification_body,
                certificate_number,
                certificate_expires_at,
                now,
                aims_id,
            ),
        )

    def add_control_log(
        self,
        conn: Any,
        *,
        log_id: str,
        aims_id: str,
        control_ref: str,
        control_name: str = "",
        evidence: str = "",
        status: str = "planned",
        verified_by: str | None = None,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO iso42001_control_log
               (log_id, aims_id, control_ref, control_name, evidence,
                status, verified_by, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                log_id,
                aims_id,
                control_ref,
                control_name,
                evidence,
                status,
                verified_by,
                now,
            ),
        )

    def list_control_logs(self, conn: Any, aims_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM iso42001_control_log WHERE aims_id=? ORDER BY created_at DESC",
            (aims_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── FRIA Assessments ──────────────────────────────────────────────────────────


class FRIARepository:
    def create(
        self,
        conn: Any,
        *,
        fria_id: str,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
        intended_purpose: str = "",
        foreseeable_misuse: str = "",
        geographic_scope: str = "",
        population_affected: str = "",
        right_dignity: bool = False,
        right_privacy: bool = False,
        right_nondiscrimination: bool = False,
        right_fair_trial: bool = False,
        right_presumption: bool = False,
        right_labour: bool = False,
        right_education: bool = False,
        right_property: bool = False,
        other_rights: str = "",
        impact_severity: str = "low",
        impact_likelihood: str = "low",
        impact_description: str = "",
        vulnerable_groups_affected: bool = False,
        vulnerable_groups_desc: str = "",
        technical_measures: list | None = None,
        organisational_measures: list | None = None,
        transparency_measures: list | None = None,
        human_oversight_measures: list | None = None,
        residual_risk_level: str = "low",
        deployment_approved: bool = False,
        deployment_conditions: str = "",
        review_frequency: str = "annual",
        assessor_id: str,
        assessor_name: str = "",
        dpo_consulted: bool = False,
        legal_reviewed: bool = False,
        status: str = "draft",
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO fria_assessments (
                fria_id, organization_id, ai_system_ref, ai_system_name,
                intended_purpose, foreseeable_misuse, geographic_scope, population_affected,
                right_dignity, right_privacy, right_nondiscrimination, right_fair_trial,
                right_presumption, right_labour, right_education, right_property,
                other_rights,
                impact_severity, impact_likelihood, impact_description,
                vulnerable_groups_affected, vulnerable_groups_desc,
                technical_measures, organisational_measures,
                transparency_measures, human_oversight_measures,
                residual_risk_level, deployment_approved, deployment_conditions,
                review_frequency,
                assessor_id, assessor_name, dpo_consulted, legal_reviewed,
                status, version, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                fria_id,
                organization_id,
                ai_system_ref,
                ai_system_name,
                intended_purpose,
                foreseeable_misuse,
                geographic_scope,
                population_affected,
                int(right_dignity),
                int(right_privacy),
                int(right_nondiscrimination),
                int(right_fair_trial),
                int(right_presumption),
                int(right_labour),
                int(right_education),
                int(right_property),
                other_rights,
                impact_severity,
                impact_likelihood,
                impact_description,
                int(vulnerable_groups_affected),
                vulnerable_groups_desc,
                json.dumps(technical_measures or []),
                json.dumps(organisational_measures or []),
                json.dumps(transparency_measures or []),
                json.dumps(human_oversight_measures or []),
                residual_risk_level,
                int(deployment_approved),
                deployment_conditions,
                review_frequency,
                assessor_id,
                assessor_name,
                int(dpo_consulted),
                int(legal_reviewed),
                status,
                1,
                now,
                now,
            ),
        )

    def get(self, conn: Any, fria_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM fria_assessments WHERE fria_id=?", (fria_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM fria_assessments
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def approve(
        self,
        conn: Any,
        fria_id: str,
        *,
        approved_by: str,
        deployment_conditions: str = "",
    ) -> None:
        now = _now()
        conn.execute(
            """UPDATE fria_assessments
               SET status='approved', deployment_approved=1,
                   approved_by=?, approved_at=?, deployment_conditions=?, updated_at=?
               WHERE fria_id=?""",
            (approved_by, now, deployment_conditions, now, fria_id),
        )

    def reject(
        self, conn: Any, fria_id: str, *, rejected_by: str, rejection_reason: str = ""
    ) -> None:
        now = _now()
        conn.execute(
            """UPDATE fria_assessments
               SET status='rejected', deployment_approved=0,
                   approved_by=?, approved_at=?, deployment_conditions=?, updated_at=?
               WHERE fria_id=?""",
            (rejected_by, now, rejection_reason, now, fria_id),
        )
