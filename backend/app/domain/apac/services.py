"""APAC privacy compliance services."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.apac.models import (
    AUSTRALIA_APPS, PDPC_AGENTIC_OBLIGATIONS, UK_ICO_EXEMPTIONS,
)
from app.domain.apac.repository import (
    AustraliaPrivacyRepository,
    CanadaPrivacyRepository,
    SingaporePDPARepository,
    UKGDPRRepository,
)


class UKGDPRService:
    def __init__(self, repo: UKGDPRRepository | None = None) -> None:
        self._repo = repo or UKGDPRRepository()

    def register(self, conn: Any, *, organization_id: str,
                 ai_system_ref: str, ai_system_name: str = "",
                 ico_reference: str = "", ico_registered: bool = False,
                 data_protection_fee_paid: bool = False,
                 lawful_basis: str = "legitimate_interests",
                 legitimate_interests_assessment: str = "",
                 ai_code_applicable: bool = False,
                 transparency_notice_published: bool = False,
                 human_review_available: bool = False,
                 profiling_used: bool = False, profiling_basis: str = "",
                 right_access_process: str = "", right_erasure_process: str = "",
                 right_portability_process: str = "", right_object_ai: str = "",
                 dpo_required: bool = False, dpo_name: str = "",
                 uk_rep_appointed: bool = False, uk_rep_name: str = "",
                 eu_transfer_mechanism: str = "none",
                 international_transfers: dict | None = None,
                 dpia_conducted: bool = False, dpia_ref: str | None = None,
                 created_by: str) -> dict[str, Any]:
        record_id = str(uuid.uuid4())
        warnings: list[str] = []
        if not ico_registered:
            warnings.append("UK GDPR: ICO registration required for data controllers.")
        if ai_code_applicable and not transparency_notice_published:
            warnings.append("UK AI Code of Practice: transparency notice required for AI systems.")
        if profiling_used and not profiling_basis:
            warnings.append("UK GDPR Art. 22: legal basis required for automated profiling decisions.")

        self._repo.create(
            conn, record_id=record_id, organization_id=organization_id,
            ai_system_ref=ai_system_ref, ai_system_name=ai_system_name,
            ico_reference=ico_reference, ico_registered=ico_registered,
            data_protection_fee_paid=data_protection_fee_paid,
            lawful_basis=lawful_basis,
            legitimate_interests_assessment=legitimate_interests_assessment,
            ai_code_applicable=ai_code_applicable,
            transparency_notice_published=transparency_notice_published,
            human_review_available=human_review_available,
            profiling_used=profiling_used, profiling_basis=profiling_basis,
            right_access_process=right_access_process,
            right_erasure_process=right_erasure_process,
            right_portability_process=right_portability_process,
            right_object_ai=right_object_ai,
            dpo_required=dpo_required, dpo_name=dpo_name,
            uk_rep_appointed=uk_rep_appointed, uk_rep_name=uk_rep_name,
            eu_transfer_mechanism=eu_transfer_mechanism,
            international_transfers=international_transfers,
            dpia_conducted=dpia_conducted, dpia_ref=dpia_ref,
            created_by=created_by,
        )
        return {"record_id": record_id, "warnings": warnings}

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, record_id)

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    @staticmethod
    def ico_exemptions() -> dict[str, str]:
        return UK_ICO_EXEMPTIONS


class CanadaPrivacyService:
    def __init__(self, repo: CanadaPrivacyRepository | None = None) -> None:
        self._repo = repo or CanadaPrivacyRepository()

    def register(self, conn: Any, *, organization_id: str,
                 ai_system_ref: str, ai_system_name: str = "",
                 provincial_law: str = "federal", law_25_quebec: bool = False,
                 consent_obtained: bool = False, consent_form: str = "",
                 implied_consent_basis: str = "", withdrawal_mechanism: str = "",
                 aida_applicable: bool = False, high_impact_system: bool = False,
                 high_impact_categories: list | None = None,
                 impact_assessment_done: bool = False,
                 impact_assessment_ref: str | None = None,
                 mitigation_measures: list | None = None,
                 incident_reporting_process: str = "",
                 q25_privacy_officer: str = "",
                 q25_privacy_policy_published: bool = False,
                 q25_pia_required: bool = False, q25_pia_done: bool = False,
                 q25_72h_breach_report: bool = False,
                 q25_portability_enabled: bool = False,
                 breach_reported_to_opc: bool = False,
                 opc_file_number: str | None = None,
                 created_by: str) -> dict[str, Any]:
        record_id = str(uuid.uuid4())
        warnings: list[str] = []
        if aida_applicable and high_impact_system and not impact_assessment_done:
            warnings.append("Bill C-27 AIDA: impact assessment required for high-impact AI systems.")
        if law_25_quebec and not q25_privacy_officer:
            warnings.append("Quebec Law 25: Privacy Officer designation required.")
        if law_25_quebec and q25_pia_required and not q25_pia_done:
            warnings.append("Quebec Law 25: Privacy Impact Assessment (PIA) required before deployment.")

        self._repo.create(
            conn, record_id=record_id, organization_id=organization_id,
            ai_system_ref=ai_system_ref, ai_system_name=ai_system_name,
            provincial_law=provincial_law, law_25_quebec=law_25_quebec,
            consent_obtained=consent_obtained, consent_form=consent_form,
            implied_consent_basis=implied_consent_basis,
            withdrawal_mechanism=withdrawal_mechanism,
            aida_applicable=aida_applicable, high_impact_system=high_impact_system,
            high_impact_categories=high_impact_categories,
            impact_assessment_done=impact_assessment_done,
            impact_assessment_ref=impact_assessment_ref,
            mitigation_measures=mitigation_measures,
            incident_reporting_process=incident_reporting_process,
            q25_privacy_officer=q25_privacy_officer,
            q25_privacy_policy_published=q25_privacy_policy_published,
            q25_pia_required=q25_pia_required, q25_pia_done=q25_pia_done,
            q25_72h_breach_report=q25_72h_breach_report,
            q25_portability_enabled=q25_portability_enabled,
            breach_reported_to_opc=breach_reported_to_opc,
            opc_file_number=opc_file_number,
            created_by=created_by,
        )
        return {"record_id": record_id, "warnings": warnings}

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, record_id)

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)


class SingaporePDPAService:
    def __init__(self, repo: SingaporePDPARepository | None = None) -> None:
        self._repo = repo or SingaporePDPARepository()

    def register(self, conn: Any, *, organization_id: str,
                 ai_system_ref: str, ai_system_name: str = "",
                 pdpa_dpo_designated: bool = False, pdpa_dpo_name: str = "",
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
                 created_by: str) -> dict[str, Any]:
        record_id = str(uuid.uuid4())
        warnings: list[str] = []
        if not pdpa_dpo_designated:
            warnings.append("PDPA: Data Protection Officer designation recommended.")
        if agentic_ai_applicable:
            if not agentic_human_oversight:
                warnings.append("PDPC Agentic AI Framework: human oversight mechanism required.")
            if not agentic_disclosure:
                warnings.append("PDPC Agentic AI Framework: AI agent disclosure to users required.")
        if cbdt_countries and not (cbdt_contractual_clauses or cbdt_binding_corporate_rules
                                   or cbdt_adequacy_applicable):
            warnings.append("PDPA Part IX: transfer mechanism required for cross-border data transfers.")

        self._repo.create(
            conn, record_id=record_id, organization_id=organization_id,
            ai_system_ref=ai_system_ref, ai_system_name=ai_system_name,
            pdpa_dpo_designated=pdpa_dpo_designated, pdpa_dpo_name=pdpa_dpo_name,
            pdpa_dpo_registered=pdpa_dpo_registered,
            data_protection_policy_published=data_protection_policy_published,
            do_not_call_compliant=do_not_call_compliant,
            consent_purpose_specific=consent_purpose_specific,
            notification_given=notification_given,
            deemed_consent_applied=deemed_consent_applied,
            agentic_ai_applicable=agentic_ai_applicable,
            agentic_human_oversight=agentic_human_oversight,
            agentic_oversight_desc=agentic_oversight_desc,
            agentic_disclosure=agentic_disclosure,
            agentic_disclosure_text=agentic_disclosure_text,
            agentic_consent_scope=agentic_consent_scope,
            agentic_data_minimised=agentic_data_minimised,
            agentic_incident_plan=agentic_incident_plan,
            pdpc_model_governance_aligned=pdpc_model_governance_aligned,
            explainability_implemented=explainability_implemented,
            bias_testing_done=bias_testing_done,
            cbdt_countries=cbdt_countries,
            cbdt_contractual_clauses=cbdt_contractual_clauses,
            cbdt_binding_corporate_rules=cbdt_binding_corporate_rules,
            cbdt_adequacy_applicable=cbdt_adequacy_applicable,
            created_by=created_by,
        )
        # Agentic AI compliance score (0-5 obligations)
        agentic_score = 0
        if agentic_ai_applicable:
            agentic_score = sum([
                agentic_human_oversight, agentic_disclosure,
                bool(agentic_consent_scope), agentic_data_minimised,
                bool(agentic_incident_plan),
            ])
        return {
            "record_id": record_id,
            "warnings": warnings,
            "agentic_compliance_score": agentic_score,
            "agentic_compliance_max": 5 if agentic_ai_applicable else 0,
        }

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, record_id)

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    @staticmethod
    def agentic_obligations() -> dict[str, str]:
        return PDPC_AGENTIC_OBLIGATIONS


class AustraliaPrivacyService:
    def __init__(self, repo: AustraliaPrivacyRepository | None = None) -> None:
        self._repo = repo or AustraliaPrivacyRepository()

    def register(self, conn: Any, *, organization_id: str,
                 ai_system_ref: str, ai_system_name: str = "",
                 annual_turnover_aud: float | None = None,
                 health_service_provider: bool = False,
                 acts_covered: bool = False,
                 app1_privacy_policy: bool = False,
                 app5_collection_notice: bool = False,
                 app6_primary_purpose_only: bool = False,
                 app11_security_measures: str = "",
                 app12_access_process: str = "",
                 app13_correction_process: str = "",
                 adm_used: bool = False, adm_description: str = "",
                 adm_explanation_available: bool = False,
                 adm_human_review_available: bool = False,
                 adm_opt_out_available: bool = False,
                 adm_meaningful_impact: bool = False,
                 ndb_scheme_applicable: bool = True,
                 breach_assessment_process: str = "",
                 oaic_notification_process: str = "",
                 oaic_complaint_process: str = "",
                 privacy_impact_assessment_done: bool = False,
                 created_by: str) -> dict[str, Any]:
        record_id = str(uuid.uuid4())
        warnings: list[str] = []
        if adm_used and adm_meaningful_impact:
            if not adm_explanation_available:
                warnings.append("Privacy Act (proposed 2026): right to explanation for meaningful AI decisions.")
            if not adm_human_review_available:
                warnings.append("Privacy Act (proposed 2026): right to human review for meaningful AI decisions.")
        if ndb_scheme_applicable and not breach_assessment_process:
            warnings.append("NDB Scheme: breach assessment and OAIC notification process required.")

        self._repo.create(
            conn, record_id=record_id, organization_id=organization_id,
            ai_system_ref=ai_system_ref, ai_system_name=ai_system_name,
            annual_turnover_aud=annual_turnover_aud,
            health_service_provider=health_service_provider,
            acts_covered=acts_covered,
            app1_privacy_policy=app1_privacy_policy,
            app5_collection_notice=app5_collection_notice,
            app6_primary_purpose_only=app6_primary_purpose_only,
            app11_security_measures=app11_security_measures,
            app12_access_process=app12_access_process,
            app13_correction_process=app13_correction_process,
            adm_used=adm_used, adm_description=adm_description,
            adm_explanation_available=adm_explanation_available,
            adm_human_review_available=adm_human_review_available,
            adm_opt_out_available=adm_opt_out_available,
            adm_meaningful_impact=adm_meaningful_impact,
            ndb_scheme_applicable=ndb_scheme_applicable,
            breach_assessment_process=breach_assessment_process,
            oaic_notification_process=oaic_notification_process,
            oaic_complaint_process=oaic_complaint_process,
            privacy_impact_assessment_done=privacy_impact_assessment_done,
            created_by=created_by,
        )
        # APP coverage score (6 key APPs out of 13)
        app_score = round(sum([
            app1_privacy_policy, app5_collection_notice, app6_primary_purpose_only,
            bool(app11_security_measures), bool(app12_access_process),
            bool(app13_correction_process),
        ]) / 6 * 100)
        return {
            "record_id": record_id,
            "warnings": warnings,
            "app_coverage_score": app_score,
        }

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, record_id)

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    @staticmethod
    def privacy_principles() -> dict[str, str]:
        return AUSTRALIA_APPS
