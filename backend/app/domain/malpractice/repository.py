"""Malpractice insurance + compliance scoring repository layer."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class ColoradoSB26189Repository:
    def create(self, conn: Any, *, record_id: str, organization_id: str,
               ai_system_ref: str, ai_system_name: str = "",
               ai_system_version: str = "1.0",
               consequential_decision_type: str = "other",
               consumers_affected_count: int = 0,
               disclosure_provided: bool = False, disclosure_timing: str = "",
               disclosure_method: str = "",
               explanation_available: bool = False, explanation_process: str = "",
               explanation_response_days: int = 30,
               data_correction_available: bool = False,
               data_correction_process: str = "",
               human_review_available: bool = False,
               human_review_process: str = "",
               human_review_response_days: int = 30,
               opt_out_available: bool = False,
               opt_out_categories: list | None = None,
               cure_period_days: int = 90,
               ag_notice_received: bool = False,
               ag_notice_date: str | None = None,
               cure_completed: bool = False,
               cure_completion_date: str | None = None,
               small_business_exempt: bool = False,
               open_source_exempt: bool = False,
               national_security_exempt: bool = False,
               created_by: str) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO colorado_sb26189_records (
                record_id, organization_id, ai_system_ref, ai_system_name, ai_system_version,
                consequential_decision_type, consumers_affected_count,
                disclosure_provided, disclosure_timing, disclosure_method,
                explanation_available, explanation_process, explanation_response_days,
                data_correction_available, data_correction_process,
                human_review_available, human_review_process, human_review_response_days,
                opt_out_available, opt_out_categories,
                cure_period_days, ag_notice_received, ag_notice_date,
                cure_completed, cure_completion_date,
                small_business_exempt, open_source_exempt, national_security_exempt,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record_id, organization_id, ai_system_ref, ai_system_name, ai_system_version,
                consequential_decision_type, consumers_affected_count,
                int(disclosure_provided), disclosure_timing, disclosure_method,
                int(explanation_available), explanation_process, explanation_response_days,
                int(data_correction_available), data_correction_process,
                int(human_review_available), human_review_process, human_review_response_days,
                int(opt_out_available), json.dumps(opt_out_categories or []),
                cure_period_days, int(ag_notice_received), ag_notice_date,
                int(cure_completed), cure_completion_date,
                int(small_business_exempt), int(open_source_exempt),
                int(national_security_exempt),
                "active", created_by, now, now,
            ),
        )

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM colorado_sb26189_records WHERE record_id=?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM colorado_sb26189_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


class CCPAADMTRepository:
    def create(self, conn: Any, *, admt_id: str, organization_id: str,
               ai_system_ref: str, ai_system_name: str = "",
               admt_purpose: str = "other",
               significant_decisions: bool = False,
               personal_data_used: bool = False,
               california_consumers: bool = False,
               pre_use_notice_provided: bool = False,
               pre_use_notice_content: str = "",
               notice_delivery_method: str = "",
               opt_out_available: bool = False,
               opt_out_mechanism: str = "",
               opt_out_response_days: int = 15,
               global_opt_out_honored: bool = False,
               access_to_admt_logic: bool = False,
               access_process: str = "",
               human_review_available: bool = False,
               human_review_process: str = "",
               human_review_timing: str = "",
               risk_assessment_required: bool = False,
               risk_assessment_done: bool = False,
               risk_assessment_ref: str | None = None,
               cppa_submission_required: bool = False,
               admt_vendor_agreements: list | None = None,
               created_by: str) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO ccpa_admt_records (
                admt_id, organization_id, ai_system_ref, ai_system_name,
                admt_purpose, significant_decisions, personal_data_used, california_consumers,
                pre_use_notice_provided, pre_use_notice_content, notice_delivery_method,
                opt_out_available, opt_out_mechanism, opt_out_response_days,
                global_opt_out_honored,
                access_to_admt_logic, access_process,
                human_review_available, human_review_process, human_review_timing,
                risk_assessment_required, risk_assessment_done, risk_assessment_ref,
                cppa_submission_required, admt_vendor_agreements,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                admt_id, organization_id, ai_system_ref, ai_system_name,
                admt_purpose, int(significant_decisions), int(personal_data_used),
                int(california_consumers),
                int(pre_use_notice_provided), pre_use_notice_content, notice_delivery_method,
                int(opt_out_available), opt_out_mechanism, opt_out_response_days,
                int(global_opt_out_honored),
                int(access_to_admt_logic), access_process,
                int(human_review_available), human_review_process, human_review_timing,
                int(risk_assessment_required), int(risk_assessment_done), risk_assessment_ref,
                int(cppa_submission_required),
                json.dumps(admt_vendor_agreements or []),
                "active", created_by, now, now,
            ),
        )

    def get(self, conn: Any, admt_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM ccpa_admt_records WHERE admt_id=?", (admt_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM ccpa_admt_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


class MalpracticeInsuranceRepository:
    def create(self, conn: Any, *, insurance_id: str, organization_id: str,
               law_firm_name: str = "", bar_jurisdiction: str = "",
               insurer_name: str = "", policy_number: str = "",
               policy_start: str | None = None, policy_end: str | None = None,
               coverage_limit_usd: float | None = None,
               current_premium_usd: float | None = None,
               ai_tools_used: bool = False,
               ai_tools_list: list | None = None,
               ai_outputs_filed_in_court: bool = False,
               citation_verification_process: bool = False,
               hallucination_incidents_12mo: int = 0,
               ai_competence_certified: bool = False,
               heillon_compliance_score: int | None = None,
               score_breakdown: dict | None = None,
               score_date: str | None = None,
               score_certified_by: str | None = None,
               base_risk_factor: float | None = None,
               ai_risk_adjustment: float | None = None,
               estimated_discount_pct: float | None = None,
               insurer_accepted_score: bool = False,
               ai_related_claims_count: int = 0,
               ai_related_claims_usd: float = 0,
               created_by: str) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO malpractice_insurance_records (
                insurance_id, organization_id, law_firm_name, bar_jurisdiction,
                insurer_name, policy_number, policy_start, policy_end,
                coverage_limit_usd, current_premium_usd,
                ai_tools_used, ai_tools_list, ai_outputs_filed_in_court,
                citation_verification_process, hallucination_incidents_12mo,
                ai_competence_certified,
                heillon_compliance_score, score_breakdown, score_date, score_certified_by,
                base_risk_factor, ai_risk_adjustment, estimated_discount_pct,
                insurer_accepted_score, ai_related_claims_count, ai_related_claims_usd,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                insurance_id, organization_id, law_firm_name, bar_jurisdiction,
                insurer_name, policy_number, policy_start, policy_end,
                coverage_limit_usd, current_premium_usd,
                int(ai_tools_used), json.dumps(ai_tools_list or []),
                int(ai_outputs_filed_in_court),
                int(citation_verification_process), hallucination_incidents_12mo,
                int(ai_competence_certified),
                heillon_compliance_score,
                json.dumps(score_breakdown or {}),
                score_date, score_certified_by,
                base_risk_factor, ai_risk_adjustment, estimated_discount_pct,
                int(insurer_accepted_score),
                ai_related_claims_count, ai_related_claims_usd,
                "active", created_by, now, now,
            ),
        )

    def get(self, conn: Any, insurance_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM malpractice_insurance_records WHERE insurance_id=?", (insurance_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM malpractice_insurance_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]


class HeilonScoreRepository:
    def create(self, conn: Any, *, score_id: str, organization_id: str,
               ai_system_ref: str, ai_system_name: str = "",
               component_scores: dict | None = None,
               total_score: int = 0, certification_tier: str = "unrated",
               evidence_bundle: dict | None = None,
               valid_until: str | None = None,
               computed_by: str = "system") -> None:
        now = _now()
        scores = component_scores or {}
        conn.execute(
            """INSERT INTO heillon_compliance_scores (
                score_id, organization_id, ai_system_ref, ai_system_name,
                score_hdr_coverage, score_citation_accuracy, score_hallucination,
                score_lgpd, score_gdpr_eu, score_gdpr_uk, score_ccpa, score_colorado,
                score_pdpl_uae, score_pdpa_sg, score_privacy_au, score_pipeda_ca,
                score_iso42001, score_iso27001, score_nist_rmf, score_euai_act,
                score_attorney_competence,
                total_score, certification_tier, evidence_bundle,
                computed_at, valid_until, computed_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                score_id, organization_id, ai_system_ref, ai_system_name,
                scores.get("score_hdr_coverage", 0),
                scores.get("score_citation_accuracy", 0),
                scores.get("score_hallucination", 0),
                scores.get("score_lgpd", 0), scores.get("score_gdpr_eu", 0),
                scores.get("score_gdpr_uk", 0), scores.get("score_ccpa", 0),
                scores.get("score_colorado", 0), scores.get("score_pdpl_uae", 0),
                scores.get("score_pdpa_sg", 0), scores.get("score_privacy_au", 0),
                scores.get("score_pipeda_ca", 0),
                scores.get("score_iso42001", 0), scores.get("score_iso27001", 0),
                scores.get("score_nist_rmf", 0), scores.get("score_euai_act", 0),
                scores.get("score_attorney_competence", 0),
                total_score, certification_tier,
                json.dumps(evidence_bundle or {}),
                now, valid_until, computed_by, now, now,
            ),
        )

    def get_latest(self, conn: Any, org_id: str,
                   ai_system_ref: str) -> dict[str, Any] | None:
        row = conn.execute(
            """SELECT * FROM heillon_compliance_scores
               WHERE organization_id=? AND ai_system_ref=?
               ORDER BY computed_at DESC LIMIT 1""",
            (org_id, ai_system_ref),
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM heillon_compliance_scores
               WHERE organization_id=? ORDER BY computed_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]
