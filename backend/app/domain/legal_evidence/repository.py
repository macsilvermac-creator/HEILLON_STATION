"""Legal evidence repository layer — FRE 707 + Citations + Hallucination."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class FRE707Repository:
    def create(self, conn: Any, *, evidence_id: str, organization_id: str,
               case_ref: str, court: str = "", jurisdiction: str = "federal",
               document_ref: str, document_type: str = "",
               ai_system_name: str = "", ai_system_version: str = "",
               ai_provider: str = "", ai_model_id: str = "",
               training_data_cutoff: str | None = None,
               training_data_description: str = "",
               methodology_disclosed: bool = False, reliable_principles: bool = False,
               principles_applied: bool = False, opinion_not_speculative: bool = False,
               validation_method: str = "", error_rate_known: bool = False,
               error_rate_value: float | None = None, peer_reviewed: bool = False,
               human_attorney_reviewed: bool = False, human_reviewer_id: str | None = None,
               daubert_analysis: str = "",
               admissibility_opinion: str = "pending",
               admissibility_conditions: str = "",
               opposing_counsel_notified: bool = False, court_ruling: str | None = None,
               hdr_id: str | None = None, generation_timestamp: str = "",
               hash_sha256: str = "", created_by: str) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO fre707_evidence_records (
                evidence_id, organization_id, case_ref, court, jurisdiction,
                document_ref, document_type,
                ai_system_name, ai_system_version, ai_provider, ai_model_id,
                training_data_cutoff, training_data_description,
                methodology_disclosed, reliable_principles, principles_applied,
                opinion_not_speculative,
                validation_method, error_rate_known, error_rate_value,
                peer_reviewed, human_attorney_reviewed, human_reviewer_id,
                daubert_analysis, admissibility_opinion, admissibility_conditions,
                opposing_counsel_notified, court_ruling,
                hdr_id, generation_timestamp, hash_sha256, chain_of_custody_intact,
                status, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                evidence_id, organization_id, case_ref, court, jurisdiction,
                document_ref, document_type,
                ai_system_name, ai_system_version, ai_provider, ai_model_id,
                training_data_cutoff, training_data_description,
                int(methodology_disclosed), int(reliable_principles),
                int(principles_applied), int(opinion_not_speculative),
                validation_method, int(error_rate_known), error_rate_value,
                int(peer_reviewed), int(human_attorney_reviewed), human_reviewer_id,
                daubert_analysis, admissibility_opinion, admissibility_conditions,
                int(opposing_counsel_notified), court_ruling,
                hdr_id, generation_timestamp or now, hash_sha256, 1,
                "draft", created_by, now, now,
            ),
        )

    def get(self, conn: Any, evidence_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM fre707_evidence_records WHERE evidence_id=?", (evidence_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM fre707_evidence_records
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_admissibility(self, conn: Any, evidence_id: str, *,
                             admissibility_opinion: str,
                             court_ruling: str | None = None,
                             conditions: str = "") -> None:
        now = _now()
        conn.execute(
            """UPDATE fre707_evidence_records
               SET admissibility_opinion=?, court_ruling=?, admissibility_conditions=?,
                   status=?, updated_at=?
               WHERE evidence_id=?""",
            (admissibility_opinion, court_ruling, conditions,
             "admitted" if admissibility_opinion == "admissible" else "draft",
             now, evidence_id),
        )


class CitationVerificationRepository:
    def create(self, conn: Any, *, citation_id: str, organization_id: str,
               document_ref: str, case_ref: str = "",
               citation_text: str = "", citation_type: str = "case",
               cited_court: str = "", cited_year: str = "",
               reporter: str = "", volume: str = "", page_start: str = "",
               url: str = "",
               verified_by: str, verification_method: str = "manual",
               verification_db: str = "", verification_date: str = "",
               citation_exists: bool = False, proposition_accurate: bool = False,
               quote_accurate: bool = False, case_still_good_law: bool = True,
               is_hallucination: bool = False, hallucination_type: str | None = None,
               hallucination_severity: str = "none", hallucination_notes: str = "",
               filed_with_court: bool = False,
               corrective_action_taken: bool = False,
               corrective_action_desc: str = "",
               bar_complaint_risk: str = "none") -> None:
        now = _now()
        conn.execute(
            """INSERT INTO citation_verifications (
                citation_id, organization_id, document_ref, case_ref,
                citation_text, citation_type, cited_court, cited_year,
                reporter, volume, page_start, url,
                verified_by, verification_method, verification_db, verification_date,
                citation_exists, proposition_accurate, quote_accurate, case_still_good_law,
                is_hallucination, hallucination_type, hallucination_severity, hallucination_notes,
                filed_with_court, corrective_action_taken, corrective_action_desc,
                bar_complaint_risk, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                citation_id, organization_id, document_ref, case_ref,
                citation_text, citation_type, cited_court, cited_year,
                reporter, volume, page_start, url,
                verified_by, verification_method, verification_db,
                verification_date or now,
                int(citation_exists), int(proposition_accurate),
                int(quote_accurate), int(case_still_good_law),
                int(is_hallucination), hallucination_type,
                hallucination_severity, hallucination_notes,
                int(filed_with_court), int(corrective_action_taken),
                corrective_action_desc, bar_complaint_risk, now,
            ),
        )

    def get(self, conn: Any, citation_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM citation_verifications WHERE citation_id=?", (citation_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_doc(self, conn: Any, org_id: str, document_ref: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM citation_verifications
               WHERE organization_id=? AND document_ref=? ORDER BY created_at DESC""",
            (org_id, document_ref),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_hallucinations(self, conn: Any, org_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM citation_verifications
               WHERE organization_id=? AND is_hallucination=1 ORDER BY created_at DESC""",
            (org_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class HallucinationRepository:
    def create(self, conn: Any, *, incident_id: str, organization_id: str,
               citation_id: str | None, document_ref: str = "",
               case_ref: str = "", incident_type: str = "citation",
               ai_system: str = "", ai_model: str = "",
               original_output: str = "", correct_info: str = "",
               severity: str = "medium", filed_with_court: bool = False,
               court_sanction: str | None = None, financial_impact: float | None = None,
               client_notified: bool = False, bar_reported: bool = False,
               root_cause: str = "", prevention_measure: str = "",
               workflow_updated: bool = False, created_by: str) -> None:
        now = _now()
        conn.execute(
            """INSERT INTO hallucination_incidents (
                incident_id, organization_id, citation_id, document_ref, case_ref,
                incident_type, ai_system, ai_model,
                original_output, correct_info,
                severity, filed_with_court, court_sanction, financial_impact,
                client_notified, bar_reported,
                root_cause, prevention_measure, workflow_updated,
                status, created_by, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                incident_id, organization_id, citation_id, document_ref, case_ref,
                incident_type, ai_system, ai_model,
                original_output, correct_info,
                severity, int(filed_with_court), court_sanction, financial_impact,
                int(client_notified), int(bar_reported),
                root_cause, prevention_measure, int(workflow_updated),
                "open", created_by, now,
            ),
        )

    def get(self, conn: Any, incident_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM hallucination_incidents WHERE incident_id=?", (incident_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM hallucination_incidents
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]

    def resolve(self, conn: Any, incident_id: str, *, resolved_by: str) -> None:
        now = _now()
        conn.execute(
            """UPDATE hallucination_incidents
               SET status='resolved', resolved_at=?, resolved_by=?
               WHERE incident_id=?""",
            (now, resolved_by, incident_id),
        )


class AICompetenceRepository:
    def create(self, conn: Any, *, cert_id: str, organization_id: str,
               attorney_id: str, attorney_name: str = "", bar_number: str = "",
               jurisdiction: str = "", training_provider: str = "",
               training_course: str = "", cle_credits_earned: float = 0,
               training_date: str = "", training_topics: list | None = None,
               ai_systems_covered: list | None = None,
               competence_areas: list | None = None,
               aba_rule_1_1_compliant: bool = False,
               state_bar_compliant: bool = False,
               renewal_due_date: str | None = None,
               certificate_number: str = "", issued_by: str = "",
               expires_at: str | None = None) -> None:
        import json
        now = _now()
        conn.execute(
            """INSERT INTO ai_competence_certificates (
                cert_id, organization_id, attorney_id, attorney_name, bar_number,
                jurisdiction, training_provider, training_course, cle_credits_earned,
                training_date, training_topics, ai_systems_covered, competence_areas,
                aba_rule_1_1_compliant, state_bar_compliant, renewal_due_date,
                certificate_number, issued_by, issued_at, expires_at, revoked, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                cert_id, organization_id, attorney_id, attorney_name, bar_number,
                jurisdiction, training_provider, training_course, cle_credits_earned,
                training_date, json.dumps(training_topics or []),
                json.dumps(ai_systems_covered or []),
                json.dumps(competence_areas or []),
                int(aba_rule_1_1_compliant), int(state_bar_compliant),
                renewal_due_date, certificate_number, issued_by, now, expires_at, 0, now,
            ),
        )

    def get(self, conn: Any, cert_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM ai_competence_certificates WHERE cert_id=?", (cert_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_org(self, conn: Any, org_id: str, *, skip: int = 0,
                    limit: int = 50) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM ai_competence_certificates
               WHERE organization_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (org_id, limit, skip),
        ).fetchall()
        return [dict(r) for r in rows]
