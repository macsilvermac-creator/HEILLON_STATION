"""USA regulatory compliance services — Fase 18."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.usa.models import (
    ABA_RULES,
    ColoradoRiskTier,
    NISTProfileTier,
)
from app.domain.usa.repository import (
    ABAComplianceRepository,
    CCPAConsentRepository,
    ColoradoAIRepository,
    ESIGNAuditRepository,
    NISTRMFRepository,
)


# ── Colorado AI Act ────────────────────────────────────────────────────────────


class ColoradoAIService:
    def __init__(self, repo: ColoradoAIRepository | None = None) -> None:
        self._repo = repo or ColoradoAIRepository()

    def register(
        self,
        conn: Any,
        *,
        organization_id: str,
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
    ) -> dict[str, Any]:
        valid_tiers = {t.value for t in ColoradoRiskTier}
        if risk_tier not in valid_tiers:
            raise ValueError(f"risk_tier must be one of {sorted(valid_tiers)}")

        record_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            record_id=record_id,
            organization_id=organization_id,
            ai_system_name=ai_system_name,
            ai_system_version=ai_system_version,
            developer_name=developer_name,
            deployer_name=deployer_name,
            risk_tier=risk_tier,
            high_risk_category=high_risk_category,
            consequential_decision_desc=consequential_decision_desc,
            impact_assessment_done=impact_assessment_done,
            impact_assessment_date=impact_assessment_date,
            impact_assessment_ref=impact_assessment_ref,
            bias_audit_done=bias_audit_done,
            bias_audit_date=bias_audit_date,
            bias_audit_provider=bias_audit_provider,
            consumer_notification_text=consumer_notification_text,
            opt_out_mechanism=opt_out_mechanism,
            appeal_process_available=appeal_process_available,
            monitoring_plan=monitoring_plan,
            created_by=created_by,
        )

        # Compliance checklist for high-risk systems
        warnings: list[str] = []
        if risk_tier == "high":
            if not impact_assessment_done:
                warnings.append("Impact assessment required for high-risk AI (SB 205 §6-1-1703)")
            if not bias_audit_done:
                warnings.append("Bias audit required for high-risk AI (SB 205 §6-1-1703)")
            if not consumer_notification_text:
                warnings.append("Consumer notification text required (SB 205 §6-1-1702)")
            if not opt_out_mechanism:
                warnings.append("Opt-out mechanism required (SB 205 §6-1-1702)")

        return {"record_id": record_id, "risk_tier": risk_tier, "warnings": warnings}

    def get(self, conn: Any, record_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, record_id)

    def list_by_org(
        self,
        conn: Any,
        organization_id: str,
        *,
        risk_tier: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(
            conn, organization_id, risk_tier=risk_tier, skip=skip, limit=limit
        )

    def retire(self, conn: Any, record_id: str) -> None:
        self._repo.update_status(conn, record_id, "retired")


# ── CCPA / CPRA ───────────────────────────────────────────────────────────────


class CCPAConsentService:
    def __init__(self, repo: CCPAConsentRepository | None = None) -> None:
        self._repo = repo or CCPAConsentRepository()

    def record_consent(
        self,
        conn: Any,
        *,
        organization_id: str,
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
    ) -> str:
        consent_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            consent_id=consent_id,
            organization_id=organization_id,
            consumer_id=consumer_id,
            consumer_email=consumer_email,
            consumer_state=consumer_state,
            data_categories=data_categories,
            processing_purposes=processing_purposes,
            consent_type=consent_type,
            sensitive_data_consent=sensitive_data_consent,
            automated_decision_consent=automated_decision_consent,
            sale_of_personal_info_consent=sale_of_personal_info_consent,
            sharing_for_cross_context=sharing_for_cross_context,
            consent_text=consent_text,
            ip_address=ip_address,
            expires_at=expires_at,
        )
        return consent_id

    def get(self, conn: Any, consent_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, consent_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)

    def withdraw(self, conn: Any, consent_id: str, *, reason: str = "") -> None:
        self._repo.withdraw(conn, consent_id, reason=reason)


# ── ABA Compliance ────────────────────────────────────────────────────────────


class ABAComplianceService:
    """Log AI usage compliance checks per ABA Model Rules."""

    def __init__(self, repo: ABAComplianceRepository | None = None) -> None:
        self._repo = repo or ABAComplianceRepository()

    def log(
        self,
        conn: Any,
        *,
        organization_id: str,
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
    ) -> dict[str, Any]:
        log_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            log_id=log_id,
            organization_id=organization_id,
            matter_ref=matter_ref,
            attorney_id=attorney_id,
            attorney_name=attorney_name,
            ai_tool_name=ai_tool_name,
            ai_tool_version=ai_tool_version,
            ai_tool_provider=ai_tool_provider,
            rule_11_competence=rule_11_competence,
            rule_16_confidentiality=rule_16_confidentiality,
            rule_34_fairness=rule_34_fairness,
            rule_53_supervision=rule_53_supervision,
            client_disclosure_made=client_disclosure_made,
            state_bar=state_bar,
            state_specific_rule_ref=state_specific_rule_ref,
            state_specific_notes=state_specific_notes,
            output_reviewed=output_reviewed,
            review_notes=review_notes,
        )

        # Compliance score
        flags = [
            rule_11_competence, rule_16_confidentiality,
            rule_34_fairness, rule_53_supervision,
            client_disclosure_made, output_reviewed,
        ]
        score = sum(1 for f in flags if f)
        compliance_pct = round(score / len(flags) * 100)

        return {
            "log_id": log_id,
            "compliance_score": compliance_pct,
            "rules_checked": {
                "1.1_competence": rule_11_competence,
                "1.6_confidentiality": rule_16_confidentiality,
                "3.4_fairness": rule_34_fairness,
                "5.3_supervision": rule_53_supervision,
            },
        }

    def get(self, conn: Any, log_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, log_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)

    @staticmethod
    def aba_rules_reference() -> dict[str, str]:
        return ABA_RULES


# ── NIST AI RMF ───────────────────────────────────────────────────────────────


class NISTRMFService:
    def __init__(self, repo: NISTRMFRepository | None = None) -> None:
        self._repo = repo or NISTRMFRepository()

    def create(
        self,
        conn: Any,
        *,
        organization_id: str,
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
    ) -> dict[str, Any]:
        valid_tiers = {t.value for t in NISTProfileTier}
        if profile_tier not in valid_tiers:
            raise ValueError(f"profile_tier must be one of {sorted(valid_tiers)}")

        rmf_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            rmf_id=rmf_id,
            organization_id=organization_id,
            ai_system_ref=ai_system_ref,
            ai_system_name=ai_system_name,
            ai_system_version=ai_system_version,
            govern_policies_defined=govern_policies_defined,
            govern_roles_assigned=govern_roles_assigned,
            govern_risk_tolerance_set=govern_risk_tolerance_set,
            govern_training_completed=govern_training_completed,
            govern_notes=govern_notes,
            map_intended_use=map_intended_use,
            map_context_established=map_context_established,
            map_risks_identified=map_risks_identified,
            map_stakeholders_consulted=map_stakeholders_consulted,
            map_notes=map_notes,
            measure_metrics_defined=measure_metrics_defined,
            measure_testing_completed=measure_testing_completed,
            measure_bias_evaluated=measure_bias_evaluated,
            measure_performance_score=measure_performance_score,
            measure_trustworthiness=measure_trustworthiness,
            measure_notes=measure_notes,
            manage_risk_responses=manage_risk_responses,
            manage_residual_risks=manage_residual_risks,
            manage_monitoring_plan=manage_monitoring_plan,
            manage_incident_plan=manage_incident_plan,
            manage_notes=manage_notes,
            profile_tier=profile_tier,
            created_by=created_by,
        )

        # Maturity score across 4 functions
        govern_score = sum([
            govern_policies_defined, govern_roles_assigned,
            govern_risk_tolerance_set, govern_training_completed,
        ])
        map_score = sum([
            map_context_established, bool(map_risks_identified),
            map_stakeholders_consulted,
        ])
        measure_score = sum([
            measure_metrics_defined, measure_testing_completed, measure_bias_evaluated,
        ])
        manage_score = sum([
            bool(manage_risk_responses), bool(manage_monitoring_plan),
            bool(manage_incident_plan),
        ])
        total = govern_score + map_score + measure_score + manage_score
        max_total = 4 + 3 + 3 + 3

        return {
            "rmf_id": rmf_id,
            "profile_tier": profile_tier,
            "maturity_score": round(total / max_total * 100),
            "function_scores": {
                "GOVERN": govern_score,
                "MAP": map_score,
                "MEASURE": measure_score,
                "MANAGE": manage_score,
            },
        }

    def get(self, conn: Any, rmf_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, rmf_id)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)


# ── ESIGN Audit ───────────────────────────────────────────────────────────────


class ESIGNAuditService:
    def __init__(self, repo: ESIGNAuditRepository | None = None) -> None:
        self._repo = repo or ESIGNAuditRepository()

    def log_event(
        self,
        conn: Any,
        *,
        organization_id: str,
        event_type: str,
        actor_id: str,
        actor_name: str = "",
        actor_email: str,
        actor_ip: str | None = None,
        document_ref: str = "",
        document_hash: str | None = None,
        sig_id: str | None = None,
        event_sequence: int = 1,
        event_data: dict | None = None,
    ) -> dict[str, str]:
        audit_id = str(uuid.uuid4())
        event_hash = self._repo.create(
            conn,
            audit_id=audit_id,
            organization_id=organization_id,
            sig_id=sig_id,
            event_type=event_type,
            event_sequence=event_sequence,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_email=actor_email,
            actor_ip=actor_ip,
            document_ref=document_ref,
            document_hash=document_hash,
            event_data=event_data,
        )
        return {"audit_id": audit_id, "event_hash": event_hash}

    def list_by_doc(
        self, conn: Any, organization_id: str, document_ref: str
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_doc(conn, organization_id, document_ref)

    def list_by_org(
        self, conn: Any, organization_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, organization_id, skip=skip, limit=limit)
