"""APAC privacy compliance repository layer."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class UKGDPRRepository:
    def create(
        self,
        conn: Any,
        *,
        record_id: str,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
        ico_reference: str = "",
        ico_registered: bool = False,
        data_protection_fee_paid: bool = False,
        lawful_basis: str = "legitimate_interests",
        legitimate_interests_assessment: str = "",
        ai_code_applicable: bool = False,
        transparency_notice_published: bool = False,
        human_review_available: bool = False,
        profiling_used: bool = False,
        profiling_basis: str = "",
        right_access_process: str = "",
        right_erasure_process: str = "",
        right_portability_process: str = "",
        right_object_ai: str = "",
        dpo_required: bool = False,
        dpo_name: str = "",
        uk_rep_appointed: bool = False,
        uk_rep_name: str = "",
        eu_transfer_mechanism: str = "none",
        international_transfers: dict | None = None,
        dpia_conducted: bool = False,
        dpia_ref: str | None = None,
        created_by: str,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO uk_gdpr_records (
                record_id, organization_id, ai_system_ref, ai_system_name,
                ico_reference, ico_registered, data_protection_fee_paid,
                lawful_basis, legitimate_interests_assessment,
                ai_code_applicable, transparency_notice_published,
                human_review_available, profiling_used, profiling_basis,
                right_access_process, right_erasure_process,
                right_portability_process, right_object_ai,
                dpo_required, dpo_name, uk_rep_appointed, uk_rep_name,
                eu_transfer_mechanism, international_transfers,
                dpia_conducted, dpia_ref,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record_id,
                organization_id,
                ai_system_ref,
                ai_system_name,
                ico_reference,
                int(ico_registered),
                int(data_protection_fee_paid),
                lawful_basis,
                legitimate_interests_assessment,
                int(ai_code_applicable),
                int(transparency_notice_published),
                int(human_review_available),
                int(profiling_used),
                profiling_basis,
                right_access_process,
                right_erasure_process,
                right_portability_process,
                right_object_ai,
                int(dpo_required),
                dpo_name,
                int(uk_rep_appointed),
                uk_rep_name,
                eu_transfer_mechanism,
                json.dumps(international_transfers or {}),
                int(dpia_conducted),
                dpia_ref,
                "active",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM uk_gdpr_records WHERE record_id=?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM uk_gdpr_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


class CanadaPrivacyRepository:
    def create(
        self,
        conn: Any,
        *,
        record_id: str,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
        provincial_law: str = "federal",
        law_25_quebec: bool = False,
        consent_obtained: bool = False,
        consent_form: str = "",
        implied_consent_basis: str = "",
        withdrawal_mechanism: str = "",
        aida_applicable: bool = False,
        high_impact_system: bool = False,
        high_impact_categories: list | None = None,
        impact_assessment_done: bool = False,
        impact_assessment_ref: str | None = None,
        mitigation_measures: list | None = None,
        incident_reporting_process: str = "",
        q25_privacy_officer: str = "",
        q25_privacy_policy_published: bool = False,
        q25_pia_required: bool = False,
        q25_pia_done: bool = False,
        q25_72h_breach_report: bool = False,
        q25_portability_enabled: bool = False,
        breach_reported_to_opc: bool = False,
        opc_file_number: str | None = None,
        created_by: str,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO canada_privacy_records (
                record_id, organization_id, ai_system_ref, ai_system_name,
                provincial_law, law_25_quebec,
                consent_obtained, consent_form, implied_consent_basis, withdrawal_mechanism,
                aida_applicable, high_impact_system, high_impact_categories,
                impact_assessment_done, impact_assessment_ref,
                mitigation_measures, incident_reporting_process,
                q25_privacy_officer, q25_privacy_policy_published,
                q25_pia_required, q25_pia_done, q25_72h_breach_report, q25_portability_enabled,
                breach_reported_to_opc, opc_file_number,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record_id,
                organization_id,
                ai_system_ref,
                ai_system_name,
                provincial_law,
                int(law_25_quebec),
                int(consent_obtained),
                consent_form,
                implied_consent_basis,
                withdrawal_mechanism,
                int(aida_applicable),
                int(high_impact_system),
                json.dumps(high_impact_categories or []),
                int(impact_assessment_done),
                impact_assessment_ref,
                json.dumps(mitigation_measures or []),
                incident_reporting_process,
                q25_privacy_officer,
                int(q25_privacy_policy_published),
                int(q25_pia_required),
                int(q25_pia_done),
                int(q25_72h_breach_report),
                int(q25_portability_enabled),
                int(breach_reported_to_opc),
                opc_file_number,
                "active",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM canada_privacy_records WHERE record_id=?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM canada_privacy_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


class SingaporePDPARepository:
    def create(
        self,
        conn: Any,
        *,
        record_id: str,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
        pdpa_dpo_designated: bool = False,
        pdpa_dpo_name: str = "",
        pdpa_dpo_registered: bool = False,
        data_protection_policy_published: bool = False,
        do_not_call_compliant: bool = False,
        consent_purpose_specific: bool = False,
        notification_given: bool = False,
        deemed_consent_applied: bool = False,
        agentic_ai_applicable: bool = False,
        agentic_human_oversight: bool = False,
        agentic_oversight_desc: str = "",
        agentic_disclosure: bool = False,
        agentic_disclosure_text: str = "",
        agentic_consent_scope: str = "",
        agentic_data_minimised: bool = False,
        agentic_incident_plan: str = "",
        pdpc_model_governance_aligned: bool = False,
        explainability_implemented: bool = False,
        bias_testing_done: bool = False,
        cbdt_countries: list | None = None,
        cbdt_contractual_clauses: bool = False,
        cbdt_binding_corporate_rules: bool = False,
        cbdt_adequacy_applicable: bool = False,
        created_by: str,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO singapore_pdpa_records (
                record_id, organization_id, ai_system_ref, ai_system_name,
                pdpa_dpo_designated, pdpa_dpo_name, pdpa_dpo_registered,
                data_protection_policy_published, do_not_call_compliant,
                consent_purpose_specific, notification_given, deemed_consent_applied,
                agentic_ai_applicable, agentic_human_oversight, agentic_oversight_desc,
                agentic_disclosure, agentic_disclosure_text, agentic_consent_scope,
                agentic_data_minimised, agentic_incident_plan,
                pdpc_model_governance_aligned, explainability_implemented, bias_testing_done,
                cbdt_countries, cbdt_contractual_clauses, cbdt_binding_corporate_rules,
                cbdt_adequacy_applicable,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record_id,
                organization_id,
                ai_system_ref,
                ai_system_name,
                int(pdpa_dpo_designated),
                pdpa_dpo_name,
                int(pdpa_dpo_registered),
                int(data_protection_policy_published),
                int(do_not_call_compliant),
                int(consent_purpose_specific),
                int(notification_given),
                int(deemed_consent_applied),
                int(agentic_ai_applicable),
                int(agentic_human_oversight),
                agentic_oversight_desc,
                int(agentic_disclosure),
                agentic_disclosure_text,
                agentic_consent_scope,
                int(agentic_data_minimised),
                agentic_incident_plan,
                int(pdpc_model_governance_aligned),
                int(explainability_implemented),
                int(bias_testing_done),
                json.dumps(cbdt_countries or []),
                int(cbdt_contractual_clauses),
                int(cbdt_binding_corporate_rules),
                int(cbdt_adequacy_applicable),
                "active",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM singapore_pdpa_records WHERE record_id=?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM singapore_pdpa_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


class AustraliaPrivacyRepository:
    def create(
        self,
        conn: Any,
        *,
        record_id: str,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
        annual_turnover_aud: float | None = None,
        health_service_provider: bool = False,
        acts_covered: bool = False,
        app1_privacy_policy: bool = False,
        app5_collection_notice: bool = False,
        app6_primary_purpose_only: bool = False,
        app11_security_measures: str = "",
        app12_access_process: str = "",
        app13_correction_process: str = "",
        adm_used: bool = False,
        adm_description: str = "",
        adm_explanation_available: bool = False,
        adm_human_review_available: bool = False,
        adm_opt_out_available: bool = False,
        adm_meaningful_impact: bool = False,
        ndb_scheme_applicable: bool = True,
        breach_assessment_process: str = "",
        oaic_notification_process: str = "",
        oaic_complaint_process: str = "",
        privacy_impact_assessment_done: bool = False,
        created_by: str,
    ) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO australia_privacy_records (
                record_id, organization_id, ai_system_ref, ai_system_name,
                annual_turnover_aud, health_service_provider, acts_covered,
                app1_privacy_policy, app5_collection_notice, app6_primary_purpose_only,
                app11_security_measures, app12_access_process, app13_correction_process,
                adm_used, adm_description, adm_explanation_available,
                adm_human_review_available, adm_opt_out_available, adm_meaningful_impact,
                ndb_scheme_applicable, breach_assessment_process, oaic_notification_process,
                oaic_complaint_process, privacy_impact_assessment_done,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record_id,
                organization_id,
                ai_system_ref,
                ai_system_name,
                annual_turnover_aud,
                int(health_service_provider),
                int(acts_covered),
                int(app1_privacy_policy),
                int(app5_collection_notice),
                int(app6_primary_purpose_only),
                app11_security_measures,
                app12_access_process,
                app13_correction_process,
                int(adm_used),
                adm_description,
                int(adm_explanation_available),
                int(adm_human_review_available),
                int(adm_opt_out_available),
                int(adm_meaningful_impact),
                int(ndb_scheme_applicable),
                breach_assessment_process,
                oaic_notification_process,
                oaic_complaint_process,
                int(privacy_impact_assessment_done),
                "active",
                created_by,
                now,
                now,
            ),
        )

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM australia_privacy_records WHERE record_id=?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM australia_privacy_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]
