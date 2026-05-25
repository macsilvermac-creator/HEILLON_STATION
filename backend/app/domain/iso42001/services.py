"""ISO 42001 AIMS + FRIA services — Fase 20."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.iso42001.models import ANNEX_A_CONTROLS, EU_CHARTER_RIGHTS
from app.domain.iso42001.repository import FRIARepository, ISO42001Repository


class ISO42001Service:
    def __init__(self, repo: ISO42001Repository | None = None) -> None:
        self._repo = repo or ISO42001Repository()

    def register(self, conn: Any, *, organization_id: str,
                 ai_system_ref: str, ai_system_name: str = "",
                 ai_system_version: str = "1.0",
                 c4_internal_issues: str = "", c4_external_issues: str = "",
                 c4_interested_parties: list | None = None,
                 c4_aims_scope: str = "", c4_ai_policy_defined: bool = False,
                 c5_top_mgmt_commitment: bool = False, c5_ai_policy_text: str = "",
                 c5_roles_defined: bool = False, c5_dpo_appointed: bool = False,
                 c6_risks_assessed: bool = False, c6_opportunities_noted: bool = False,
                 c6_objectives_set: list | None = None, c6_action_plans: list | None = None,
                 c7_resources_allocated: bool = False, c7_competence_verified: bool = False,
                 c7_awareness_training: bool = False, c7_documentation_maintained: bool = False,
                 c8_operational_controls: bool = False, c8_ai_system_lifecycle: str = "",
                 c8_data_quality_assured: bool = False, c8_human_oversight_active: bool = False,
                 c8_incident_response_plan: str = "",
                 c9_monitoring_metrics: dict | None = None,
                 c9_internal_audit_done: bool = False, c9_mgmt_review_done: bool = False,
                 c9_last_audit_date: str | None = None,
                 c10_nonconformities: list | None = None,
                 c10_corrective_actions: list | None = None,
                 c10_continual_improvement_plan: str = "",
                 annex_a2: bool = False, annex_a3: bool = False,
                 annex_a4: bool = False, annex_a5: bool = False,
                 annex_a6: bool = False, annex_a7: bool = False,
                 annex_a8: bool = False, annex_a9: bool = False,
                 certification_body: str | None = None,
                 certification_status: str = "not_started",
                 created_by: str) -> dict[str, Any]:
        aims_id = str(uuid.uuid4())

        # Compute initial conformity score
        conformity_score = self._compute_score(
            c4_ai_policy_defined=c4_ai_policy_defined,
            c5_top_mgmt_commitment=c5_top_mgmt_commitment, c5_roles_defined=c5_roles_defined,
            c6_risks_assessed=c6_risks_assessed, c6_objectives_set=bool(c6_objectives_set),
            c7_resources_allocated=c7_resources_allocated,
            c7_awareness_training=c7_awareness_training,
            c8_operational_controls=c8_operational_controls,
            c8_human_oversight_active=c8_human_oversight_active,
            c9_internal_audit_done=c9_internal_audit_done,
            c9_mgmt_review_done=c9_mgmt_review_done,
            c10_continual_improvement_plan=bool(c10_continual_improvement_plan),
            annex_a2=annex_a2, annex_a3=annex_a3, annex_a4=annex_a4, annex_a5=annex_a5,
            annex_a6=annex_a6, annex_a7=annex_a7, annex_a8=annex_a8, annex_a9=annex_a9,
        )

        self._repo.create(
            conn, aims_id=aims_id, organization_id=organization_id,
            ai_system_ref=ai_system_ref, ai_system_name=ai_system_name,
            ai_system_version=ai_system_version,
            c4_internal_issues=c4_internal_issues, c4_external_issues=c4_external_issues,
            c4_interested_parties=c4_interested_parties, c4_aims_scope=c4_aims_scope,
            c4_ai_policy_defined=c4_ai_policy_defined,
            c5_top_mgmt_commitment=c5_top_mgmt_commitment, c5_ai_policy_text=c5_ai_policy_text,
            c5_roles_defined=c5_roles_defined, c5_dpo_appointed=c5_dpo_appointed,
            c6_risks_assessed=c6_risks_assessed, c6_opportunities_noted=c6_opportunities_noted,
            c6_objectives_set=c6_objectives_set, c6_action_plans=c6_action_plans,
            c7_resources_allocated=c7_resources_allocated,
            c7_competence_verified=c7_competence_verified,
            c7_awareness_training=c7_awareness_training,
            c7_documentation_maintained=c7_documentation_maintained,
            c8_operational_controls=c8_operational_controls,
            c8_ai_system_lifecycle=c8_ai_system_lifecycle,
            c8_data_quality_assured=c8_data_quality_assured,
            c8_human_oversight_active=c8_human_oversight_active,
            c8_incident_response_plan=c8_incident_response_plan,
            c9_monitoring_metrics=c9_monitoring_metrics,
            c9_internal_audit_done=c9_internal_audit_done,
            c9_mgmt_review_done=c9_mgmt_review_done,
            c9_last_audit_date=c9_last_audit_date,
            c10_nonconformities=c10_nonconformities,
            c10_corrective_actions=c10_corrective_actions,
            c10_continual_improvement_plan=c10_continual_improvement_plan,
            annex_a2=annex_a2, annex_a3=annex_a3, annex_a4=annex_a4, annex_a5=annex_a5,
            annex_a6=annex_a6, annex_a7=annex_a7, annex_a8=annex_a8, annex_a9=annex_a9,
            certification_body=certification_body,
            certification_status=certification_status,
            created_by=created_by,
        )
        return {
            "aims_id": aims_id,
            "conformity_score": conformity_score,
            "certification_status": certification_status,
        }

    @staticmethod
    def _compute_score(**flags: bool | int) -> int:
        """Compute 0-100 conformity score from clause + annex flags."""
        # 20 checkpoints: 12 clause flags + 8 annex controls
        checkpoint_values = list(flags.values())
        filled = sum(1 for v in checkpoint_values if v)
        total = len(checkpoint_values)
        return round(filled / total * 100) if total else 0

    def get(self, conn: Any, aims_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, aims_id)

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    def update_certification(self, conn: Any, aims_id: str, *,
                             certification_status: str,
                             conformity_score: int | None = None,
                             certification_body: str | None = None,
                             certificate_number: str | None = None,
                             certificate_expires_at: str | None = None) -> dict[str, Any]:
        self._repo.update_certification(
            conn, aims_id, certification_status=certification_status,
            conformity_score=conformity_score, certification_body=certification_body,
            certificate_number=certificate_number,
            certificate_expires_at=certificate_expires_at,
        )
        return {"aims_id": aims_id, "certification_status": certification_status}

    def add_control_evidence(self, conn: Any, aims_id: str, *,
                             control_ref: str, evidence: str,
                             status: str = "implemented",
                             verified_by: str | None = None) -> dict[str, Any]:
        if control_ref not in ANNEX_A_CONTROLS:
            raise ValueError(f"control_ref must be one of {list(ANNEX_A_CONTROLS.keys())}")
        log_id = str(uuid.uuid4())
        self._repo.add_control_log(
            conn, log_id=log_id, aims_id=aims_id,
            control_ref=control_ref,
            control_name=ANNEX_A_CONTROLS[control_ref],
            evidence=evidence, status=status, verified_by=verified_by,
        )
        return {"log_id": log_id, "aims_id": aims_id, "control_ref": control_ref}

    def list_controls(self, conn: Any, aims_id: str) -> list[dict[str, Any]]:
        return self._repo.list_control_logs(conn, aims_id)

    @staticmethod
    def annex_controls() -> dict[str, str]:
        return ANNEX_A_CONTROLS


class FRIAService:
    def __init__(self, repo: FRIARepository | None = None) -> None:
        self._repo = repo or FRIARepository()

    def create(self, conn: Any, *, organization_id: str,
               ai_system_ref: str, ai_system_name: str = "",
               intended_purpose: str = "", foreseeable_misuse: str = "",
               geographic_scope: str = "", population_affected: str = "",
               right_dignity: bool = False, right_privacy: bool = False,
               right_nondiscrimination: bool = False, right_fair_trial: bool = False,
               right_presumption: bool = False, right_labour: bool = False,
               right_education: bool = False, right_property: bool = False,
               other_rights: str = "",
               impact_severity: str = "low", impact_likelihood: str = "low",
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
               assessor_id: str, assessor_name: str = "",
               dpo_consulted: bool = False, legal_reviewed: bool = False,
               status: str = "draft") -> dict[str, Any]:
        fria_id = str(uuid.uuid4())
        self._repo.create(
            conn, fria_id=fria_id, organization_id=organization_id,
            ai_system_ref=ai_system_ref, ai_system_name=ai_system_name,
            intended_purpose=intended_purpose, foreseeable_misuse=foreseeable_misuse,
            geographic_scope=geographic_scope, population_affected=population_affected,
            right_dignity=right_dignity, right_privacy=right_privacy,
            right_nondiscrimination=right_nondiscrimination,
            right_fair_trial=right_fair_trial, right_presumption=right_presumption,
            right_labour=right_labour, right_education=right_education,
            right_property=right_property, other_rights=other_rights,
            impact_severity=impact_severity, impact_likelihood=impact_likelihood,
            impact_description=impact_description,
            vulnerable_groups_affected=vulnerable_groups_affected,
            vulnerable_groups_desc=vulnerable_groups_desc,
            technical_measures=technical_measures,
            organisational_measures=organisational_measures,
            transparency_measures=transparency_measures,
            human_oversight_measures=human_oversight_measures,
            residual_risk_level=residual_risk_level,
            deployment_approved=deployment_approved,
            deployment_conditions=deployment_conditions,
            review_frequency=review_frequency,
            assessor_id=assessor_id, assessor_name=assessor_name,
            dpo_consulted=dpo_consulted, legal_reviewed=legal_reviewed,
            status=status,
        )
        # Block deployment if residual risk is unacceptable
        blocked = residual_risk_level == "unacceptable"
        return {
            "fria_id": fria_id,
            "status": status,
            "residual_risk_level": residual_risk_level,
            "deployment_blocked": blocked,
        }

    def get(self, conn: Any, fria_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, fria_id)

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    def approve(self, conn: Any, fria_id: str, *, approved_by: str,
                deployment_conditions: str = "") -> dict[str, Any]:
        self._repo.approve(conn, fria_id, approved_by=approved_by,
                           deployment_conditions=deployment_conditions)
        return {"fria_id": fria_id, "status": "approved", "approved_by": approved_by}

    def reject(self, conn: Any, fria_id: str, *, rejected_by: str,
               rejection_reason: str = "") -> dict[str, Any]:
        self._repo.reject(conn, fria_id, rejected_by=rejected_by,
                          rejection_reason=rejection_reason)
        return {"fria_id": fria_id, "status": "rejected"}

    @staticmethod
    def eu_charter_rights() -> dict[str, str]:
        return EU_CHARTER_RIGHTS
