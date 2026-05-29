"""Malpractice insurance + compliance scoring services."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.malpractice.models import (
    CCPA_ADMT_RIGHTS,
    COLORADO_SB26189_RIGHTS,
    SCORE_WEIGHTS,
    tier_from_score,
)
from app.domain.malpractice.repository import (
    CCPAADMTRepository,
    ColoradoSB26189Repository,
    HeilonScoreRepository,
    MalpracticeInsuranceRepository,
)


class ColoradoSB26189Service:
    def __init__(self, repo: ColoradoSB26189Repository | None = None) -> None:
        self._repo = repo or ColoradoSB26189Repository()

    def register(
        self,
        conn: Any,
        *,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
        ai_system_version: str = "1.0",
        consequential_decision_type: str = "other",
        consumers_affected_count: int = 0,
        disclosure_provided: bool = False,
        disclosure_timing: str = "",
        disclosure_method: str = "",
        explanation_available: bool = False,
        explanation_process: str = "",
        explanation_response_days: int = 30,
        data_correction_available: bool = False,
        data_correction_process: str = "",
        human_review_available: bool = False,
        human_review_process: str = "",
        human_review_response_days: int = 30,
        opt_out_available: bool = False,
        opt_out_categories: list | None = None,
        small_business_exempt: bool = False,
        open_source_exempt: bool = False,
        national_security_exempt: bool = False,
        created_by: str,
    ) -> dict[str, Any]:
        record_id = str(uuid.uuid4())
        # SB 26-189 compliance warnings
        warnings: list[str] = []
        is_exempt = (
            small_business_exempt or open_source_exempt or national_security_exempt
        )
        if not is_exempt:
            if not disclosure_provided:
                warnings.append(
                    "SB 26-189 Art. 8: Consumer disclosure required before consequential AI decision."
                )
            if not explanation_available:
                warnings.append(
                    "SB 26-189 Art. 9: Right to explanation must be available."
                )
            if not data_correction_available:
                warnings.append(
                    "SB 26-189 Art. 10: Right to data correction must be available."
                )
            if not human_review_available:
                warnings.append(
                    "SB 26-189 Art. 11: Right to human review must be available."
                )

        self._repo.create(
            conn,
            record_id=record_id,
            organization_id=organization_id,
            ai_system_ref=ai_system_ref,
            ai_system_name=ai_system_name,
            ai_system_version=ai_system_version,
            consequential_decision_type=consequential_decision_type,
            consumers_affected_count=consumers_affected_count,
            disclosure_provided=disclosure_provided,
            disclosure_timing=disclosure_timing,
            disclosure_method=disclosure_method,
            explanation_available=explanation_available,
            explanation_process=explanation_process,
            explanation_response_days=explanation_response_days,
            data_correction_available=data_correction_available,
            data_correction_process=data_correction_process,
            human_review_available=human_review_available,
            human_review_process=human_review_process,
            human_review_response_days=human_review_response_days,
            opt_out_available=opt_out_available,
            opt_out_categories=opt_out_categories,
            small_business_exempt=small_business_exempt,
            open_source_exempt=open_source_exempt,
            national_security_exempt=national_security_exempt,
            created_by=created_by,
        )
        rights_score = sum(
            [
                disclosure_provided,
                explanation_available,
                data_correction_available,
                human_review_available,
            ]
        )
        return {
            "record_id": record_id,
            "warnings": warnings,
            "rights_score": rights_score,
            "rights_max": 4,
            "is_exempt": is_exempt,
        }

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, record_id)

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    @staticmethod
    def consumer_rights() -> dict[str, str]:
        return COLORADO_SB26189_RIGHTS


class CCPAADMTService:
    def __init__(self, repo: CCPAADMTRepository | None = None) -> None:
        self._repo = repo or CCPAADMTRepository()

    def register(
        self,
        conn: Any,
        *,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
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
        created_by: str,
    ) -> dict[str, Any]:
        admt_id = str(uuid.uuid4())
        warnings: list[str] = []
        if not pre_use_notice_provided:
            warnings.append(
                "CCPA ADMT §7085: Pre-use notice required before deployment."
            )
        if not opt_out_available:
            warnings.append("CCPA ADMT §1798.121: Opt-out mechanism required.")
        if risk_assessment_required and not risk_assessment_done:
            warnings.append(
                "CCPA ADMT Art. 22: Risk assessment required before deployment."
            )

        self._repo.create(
            conn,
            admt_id=admt_id,
            organization_id=organization_id,
            ai_system_ref=ai_system_ref,
            ai_system_name=ai_system_name,
            admt_purpose=admt_purpose,
            significant_decisions=significant_decisions,
            personal_data_used=personal_data_used,
            california_consumers=california_consumers,
            pre_use_notice_provided=pre_use_notice_provided,
            pre_use_notice_content=pre_use_notice_content,
            notice_delivery_method=notice_delivery_method,
            opt_out_available=opt_out_available,
            opt_out_mechanism=opt_out_mechanism,
            opt_out_response_days=opt_out_response_days,
            global_opt_out_honored=global_opt_out_honored,
            access_to_admt_logic=access_to_admt_logic,
            access_process=access_process,
            human_review_available=human_review_available,
            human_review_process=human_review_process,
            human_review_timing=human_review_timing,
            risk_assessment_required=risk_assessment_required,
            risk_assessment_done=risk_assessment_done,
            risk_assessment_ref=risk_assessment_ref,
            cppa_submission_required=cppa_submission_required,
            admt_vendor_agreements=admt_vendor_agreements,
            created_by=created_by,
        )
        rights_score = sum(
            [
                pre_use_notice_provided,
                opt_out_available,
                access_to_admt_logic,
                human_review_available,
            ]
        )
        return {
            "admt_id": admt_id,
            "warnings": warnings,
            "rights_compliance_score": rights_score,
            "rights_compliance_max": 4,
        }

    def get(self, conn: Any, admt_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, admt_id)

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    @staticmethod
    def admt_rights() -> dict[str, str]:
        return CCPA_ADMT_RIGHTS


class MalpracticeInsuranceService:
    def __init__(self, repo: MalpracticeInsuranceRepository | None = None) -> None:
        self._repo = repo or MalpracticeInsuranceRepository()

    def register(
        self,
        conn: Any,
        *,
        organization_id: str,
        law_firm_name: str = "",
        bar_jurisdiction: str = "",
        insurer_name: str = "",
        policy_number: str = "",
        policy_start: str | None = None,
        policy_end: str | None = None,
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
        ai_related_claims_count: int = 0,
        ai_related_claims_usd: float = 0,
        created_by: str,
    ) -> dict[str, Any]:
        insurance_id = str(uuid.uuid4())

        # Risk adjustment calculation
        risk_adjustment = 0.0
        if heillon_compliance_score is not None:
            if heillon_compliance_score >= 90:
                risk_adjustment = -0.20  # 20% discount for platinum
            elif heillon_compliance_score >= 75:
                risk_adjustment = -0.12  # 12% discount for gold
            elif heillon_compliance_score >= 50:
                risk_adjustment = -0.05  # 5% discount for silver
        if hallucination_incidents_12mo > 0:
            risk_adjustment += 0.05 * min(hallucination_incidents_12mo, 5)  # surcharge
        if ai_outputs_filed_in_court and not citation_verification_process:
            risk_adjustment += 0.10  # 10% surcharge for filing without verification

        estimated_discount = round(max(0, -risk_adjustment) * 100, 1)
        base_risk_factor = 1.0 + risk_adjustment
        now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        self._repo.create(
            conn,
            insurance_id=insurance_id,
            organization_id=organization_id,
            law_firm_name=law_firm_name,
            bar_jurisdiction=bar_jurisdiction,
            insurer_name=insurer_name,
            policy_number=policy_number,
            policy_start=policy_start,
            policy_end=policy_end,
            coverage_limit_usd=coverage_limit_usd,
            current_premium_usd=current_premium_usd,
            ai_tools_used=ai_tools_used,
            ai_tools_list=ai_tools_list,
            ai_outputs_filed_in_court=ai_outputs_filed_in_court,
            citation_verification_process=citation_verification_process,
            hallucination_incidents_12mo=hallucination_incidents_12mo,
            ai_competence_certified=ai_competence_certified,
            heillon_compliance_score=heillon_compliance_score,
            score_breakdown=score_breakdown,
            score_date=now_str if heillon_compliance_score else None,
            score_certified_by="Heillon Legal" if heillon_compliance_score else None,
            base_risk_factor=base_risk_factor,
            ai_risk_adjustment=risk_adjustment,
            estimated_discount_pct=estimated_discount,
            ai_related_claims_count=ai_related_claims_count,
            ai_related_claims_usd=ai_related_claims_usd,
            created_by=created_by,
        )
        return {
            "insurance_id": insurance_id,
            "base_risk_factor": round(base_risk_factor, 3),
            "ai_risk_adjustment": round(risk_adjustment, 3),
            "estimated_discount_pct": estimated_discount,
        }

    def get(self, conn: Any, insurance_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, insurance_id)

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)


class HeilonComplianceScoreService:
    def __init__(self, repo: HeilonScoreRepository | None = None) -> None:
        self._repo = repo or HeilonScoreRepository()

    def compute(
        self,
        conn: Any,
        *,
        organization_id: str,
        ai_system_ref: str,
        ai_system_name: str = "",
        component_scores: dict | None = None,
        evidence_bundle: dict | None = None,
        computed_by: str = "system",
    ) -> dict[str, Any]:
        score_id = str(uuid.uuid4())
        scores = component_scores or {}

        # Weighted total (normalize weights sum to 100)
        total_weight = sum(SCORE_WEIGHTS.values())  # 110
        weighted_sum = sum(scores.get(k, 0) * w / 100 for k, w in SCORE_WEIGHTS.items())
        total_score = round(weighted_sum * 100 / total_weight)
        tier = tier_from_score(total_score)

        # Valid for 90 days
        valid_until = (datetime.now(UTC) + timedelta(days=90)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        self._repo.create(
            conn,
            score_id=score_id,
            organization_id=organization_id,
            ai_system_ref=ai_system_ref,
            ai_system_name=ai_system_name,
            component_scores=scores,
            total_score=total_score,
            certification_tier=tier.value,
            evidence_bundle=evidence_bundle,
            valid_until=valid_until,
            computed_by=computed_by,
        )
        return {
            "score_id": score_id,
            "total_score": total_score,
            "certification_tier": tier.value,
            "valid_until": valid_until,
            "component_scores": scores,
        }

    def get_latest(
        self, conn: Any, org_id: str, ai_system_ref: str
    ) -> dict[str, Any] | None:
        return self._repo.get_latest(conn, org_id, ai_system_ref)

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    @staticmethod
    def score_weights() -> dict[str, int]:
        return SCORE_WEIGHTS
