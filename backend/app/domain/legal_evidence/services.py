"""Legal evidence services — FRE 707 + Citations + Hallucination."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.legal_evidence.models import (
    ABA_AI_COMPETENCE_RULES,
    STATE_AI_CLE_REQUIREMENTS,
)
from app.domain.legal_evidence.repository import (
    AICompetenceRepository,
    CitationVerificationRepository,
    FRE707Repository,
    HallucinationRepository,
)


class FRE707Service:
    def __init__(self, repo: FRE707Repository | None = None) -> None:
        self._repo = repo or FRE707Repository()

    def register(
        self,
        conn: Any,
        *,
        organization_id: str,
        case_ref: str,
        court: str = "",
        jurisdiction: str = "federal",
        document_ref: str,
        document_type: str = "",
        ai_system_name: str = "",
        ai_system_version: str = "",
        ai_provider: str = "",
        ai_model_id: str = "",
        training_data_cutoff: str | None = None,
        training_data_description: str = "",
        methodology_disclosed: bool = False,
        reliable_principles: bool = False,
        principles_applied: bool = False,
        opinion_not_speculative: bool = False,
        validation_method: str = "",
        error_rate_known: bool = False,
        error_rate_value: float | None = None,
        peer_reviewed: bool = False,
        human_attorney_reviewed: bool = False,
        human_reviewer_id: str | None = None,
        daubert_analysis: str = "",
        admissibility_opinion: str = "pending",
        admissibility_conditions: str = "",
        opposing_counsel_notified: bool = False,
        hdr_id: str | None = None,
        hash_sha256: str = "",
        created_by: str,
    ) -> dict[str, Any]:
        evidence_id = str(uuid.uuid4())
        # FRE 702 checklist score (0-4)
        fre702_score = sum(
            [
                methodology_disclosed,
                reliable_principles,
                principles_applied,
                opinion_not_speculative,
            ]
        )
        self._repo.create(
            conn,
            evidence_id=evidence_id,
            organization_id=organization_id,
            case_ref=case_ref,
            court=court,
            jurisdiction=jurisdiction,
            document_ref=document_ref,
            document_type=document_type,
            ai_system_name=ai_system_name,
            ai_system_version=ai_system_version,
            ai_provider=ai_provider,
            ai_model_id=ai_model_id,
            training_data_cutoff=training_data_cutoff,
            training_data_description=training_data_description,
            methodology_disclosed=methodology_disclosed,
            reliable_principles=reliable_principles,
            principles_applied=principles_applied,
            opinion_not_speculative=opinion_not_speculative,
            validation_method=validation_method,
            error_rate_known=error_rate_known,
            error_rate_value=error_rate_value,
            peer_reviewed=peer_reviewed,
            human_attorney_reviewed=human_attorney_reviewed,
            human_reviewer_id=human_reviewer_id,
            daubert_analysis=daubert_analysis,
            admissibility_opinion=admissibility_opinion,
            admissibility_conditions=admissibility_conditions,
            opposing_counsel_notified=opposing_counsel_notified,
            hdr_id=hdr_id,
            hash_sha256=hash_sha256,
            created_by=created_by,
        )
        return {
            "evidence_id": evidence_id,
            "fre702_score": fre702_score,
            "fre702_max": 4,
            "daubert_ready": fre702_score == 4,
        }

    def get(self, conn: Any, evidence_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, evidence_id)

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    def update_admissibility(
        self,
        conn: Any,
        evidence_id: str,
        *,
        admissibility_opinion: str,
        court_ruling: str | None = None,
        conditions: str = "",
    ) -> dict[str, Any]:
        self._repo.update_admissibility(
            conn,
            evidence_id,
            admissibility_opinion=admissibility_opinion,
            court_ruling=court_ruling,
            conditions=conditions,
        )
        return {
            "evidence_id": evidence_id,
            "admissibility_opinion": admissibility_opinion,
        }


class CitationVerificationService:
    def __init__(self, repo: CitationVerificationRepository | None = None) -> None:
        self._repo = repo or CitationVerificationRepository()

    def verify(
        self,
        conn: Any,
        *,
        organization_id: str,
        document_ref: str,
        case_ref: str = "",
        citation_text: str = "",
        citation_type: str = "case",
        cited_court: str = "",
        cited_year: str = "",
        reporter: str = "",
        volume: str = "",
        page_start: str = "",
        url: str = "",
        verified_by: str,
        verification_method: str = "manual",
        verification_db: str = "",
        verification_date: str = "",
        citation_exists: bool = False,
        proposition_accurate: bool = False,
        quote_accurate: bool = False,
        case_still_good_law: bool = True,
        is_hallucination: bool = False,
        hallucination_type: str | None = None,
        hallucination_severity: str = "none",
        hallucination_notes: str = "",
        filed_with_court: bool = False,
        corrective_action_taken: bool = False,
        corrective_action_desc: str = "",
        bar_complaint_risk: str = "none",
    ) -> dict[str, Any]:
        citation_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            citation_id=citation_id,
            organization_id=organization_id,
            document_ref=document_ref,
            case_ref=case_ref,
            citation_text=citation_text,
            citation_type=citation_type,
            cited_court=cited_court,
            cited_year=cited_year,
            reporter=reporter,
            volume=volume,
            page_start=page_start,
            url=url,
            verified_by=verified_by,
            verification_method=verification_method,
            verification_db=verification_db,
            verification_date=verification_date,
            citation_exists=citation_exists,
            proposition_accurate=proposition_accurate,
            quote_accurate=quote_accurate,
            case_still_good_law=case_still_good_law,
            is_hallucination=is_hallucination,
            hallucination_type=hallucination_type,
            hallucination_severity=hallucination_severity,
            hallucination_notes=hallucination_notes,
            filed_with_court=filed_with_court,
            corrective_action_taken=corrective_action_taken,
            corrective_action_desc=corrective_action_desc,
            bar_complaint_risk=bar_complaint_risk,
        )
        accuracy_flags = [citation_exists, proposition_accurate, case_still_good_law]
        accuracy_score = round(
            sum(1 for f in accuracy_flags if f) / len(accuracy_flags) * 100
        )
        return {
            "citation_id": citation_id,
            "is_hallucination": is_hallucination,
            "hallucination_severity": hallucination_severity,
            "accuracy_score": accuracy_score,
        }

    def get(self, conn: Any, citation_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, citation_id)

    def list_by_doc(
        self, conn: Any, org_id: str, document_ref: str
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_doc(conn, org_id, document_ref)

    def list_hallucinations(self, conn: Any, org_id: str) -> list[dict[str, Any]]:
        return self._repo.list_hallucinations(conn, org_id)


class HallucinationService:
    def __init__(self, repo: HallucinationRepository | None = None) -> None:
        self._repo = repo or HallucinationRepository()

    def report(
        self,
        conn: Any,
        *,
        organization_id: str,
        citation_id: str | None = None,
        document_ref: str = "",
        case_ref: str = "",
        incident_type: str = "citation",
        ai_system: str = "",
        ai_model: str = "",
        original_output: str = "",
        correct_info: str = "",
        severity: str = "medium",
        filed_with_court: bool = False,
        court_sanction: str | None = None,
        financial_impact: float | None = None,
        client_notified: bool = False,
        bar_reported: bool = False,
        root_cause: str = "",
        prevention_measure: str = "",
        workflow_updated: bool = False,
        created_by: str,
    ) -> dict[str, Any]:
        incident_id = str(uuid.uuid4())
        self._repo.create(
            conn,
            incident_id=incident_id,
            organization_id=organization_id,
            citation_id=citation_id,
            document_ref=document_ref,
            case_ref=case_ref,
            incident_type=incident_type,
            ai_system=ai_system,
            ai_model=ai_model,
            original_output=original_output,
            correct_info=correct_info,
            severity=severity,
            filed_with_court=filed_with_court,
            court_sanction=court_sanction,
            financial_impact=financial_impact,
            client_notified=client_notified,
            bar_reported=bar_reported,
            root_cause=root_cause,
            prevention_measure=prevention_measure,
            workflow_updated=workflow_updated,
            created_by=created_by,
        )
        return {"incident_id": incident_id, "severity": severity}

    def get(self, conn: Any, incident_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, incident_id)

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    def resolve(
        self, conn: Any, incident_id: str, *, resolved_by: str
    ) -> dict[str, Any]:
        self._repo.resolve(conn, incident_id, resolved_by=resolved_by)
        return {"incident_id": incident_id, "status": "resolved"}


class AICompetenceService:
    def __init__(self, repo: AICompetenceRepository | None = None) -> None:
        self._repo = repo or AICompetenceRepository()

    def issue_certificate(
        self,
        conn: Any,
        *,
        organization_id: str,
        attorney_id: str,
        attorney_name: str = "",
        bar_number: str = "",
        jurisdiction: str = "",
        training_provider: str = "",
        training_course: str = "",
        cle_credits_earned: float = 0,
        training_date: str = "",
        training_topics: list | None = None,
        ai_systems_covered: list | None = None,
        competence_areas: list | None = None,
        aba_rule_1_1_compliant: bool = False,
        state_bar_compliant: bool = False,
        renewal_due_date: str | None = None,
        issued_by: str = "",
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        cert_id = str(uuid.uuid4())
        cert_number = f"HEILLON-COMP-{cert_id[:8].upper()}"
        self._repo.create(
            conn,
            cert_id=cert_id,
            organization_id=organization_id,
            attorney_id=attorney_id,
            attorney_name=attorney_name,
            bar_number=bar_number,
            jurisdiction=jurisdiction,
            training_provider=training_provider,
            training_course=training_course,
            cle_credits_earned=cle_credits_earned,
            training_date=training_date,
            training_topics=training_topics,
            ai_systems_covered=ai_systems_covered,
            competence_areas=competence_areas,
            aba_rule_1_1_compliant=aba_rule_1_1_compliant,
            state_bar_compliant=state_bar_compliant,
            renewal_due_date=renewal_due_date,
            certificate_number=cert_number,
            issued_by=issued_by or "Heillon Legal",
            expires_at=expires_at,
        )
        return {
            "cert_id": cert_id,
            "certificate_number": cert_number,
            "aba_rule_1_1_compliant": aba_rule_1_1_compliant,
        }

    def get(self, conn: Any, cert_id: str) -> dict[str, Any] | None:
        return self._repo.get(conn, cert_id)

    def list_by_org(
        self, conn: Any, org_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_by_org(conn, org_id, skip=skip, limit=limit)

    @staticmethod
    def aba_rules() -> dict[str, str]:
        return ABA_AI_COMPETENCE_RULES

    @staticmethod
    def state_cle_requirements() -> dict[str, str]:
        return STATE_AI_CLE_REQUIREMENTS
