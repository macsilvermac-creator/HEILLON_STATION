"""Legal evidence AI API tests — FRE 707, citations, hallucination — Fase 20."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config as _cfg
from app.core.config import Settings


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.main import create_application

    def _settings() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'legalev.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "ev",
            FORENSICS_PACKAGE_DIR=tmp_path / "fp",
            FORCE_STUB_TIMESTAMP=True,
        )

    monkeypatch.setattr(_cfg, "get_settings", _settings)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    s = _settings()
    s.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    s.FORENSICS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    app = create_application()
    with TestClient(app) as c:
        yield c


def _token(client, role="advogado", suffix=""):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{role}{suffix}@legalev.test",
            "name": f"Test {role}",
            "password": "long-secure-pass-evidence",
            "role": role,
            "organization_id": "org_default",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


# ── Reference endpoints (no auth) ─────────────────────────────────────────────


class TestReferenceEndpoints:
    def test_aba_rules_no_auth(self, client):
        r = client.get("/api/v1/legal-evidence/aba-rules")
        assert r.status_code == 200
        data = r.json()
        assert "1.1" in data
        assert "3.3" in data
        assert "5.3" in data

    def test_state_cle_no_auth(self, client):
        r = client.get("/api/v1/legal-evidence/state-cle")
        assert r.status_code == 200
        assert "CA" in r.json()


# ── FRE 707 Evidence ──────────────────────────────────────────────────────────


class TestFRE707:
    def test_register_fre707_basic(self, client):
        token = _token(client, "advogado", "1")
        r = client.post(
            "/api/v1/legal-evidence/fre707",
            json={
                "case_ref": "24-CV-1234",
                "court": "S.D.N.Y.",
                "jurisdiction": "federal",
                "document_ref": "brief-motion-dismiss-001",
                "document_type": "brief",
                "ai_system_name": "Claude 3",
                "ai_provider": "Anthropic",
                "methodology_disclosed": True,
                "reliable_principles": True,
                "principles_applied": True,
                "opinion_not_speculative": True,
                "human_attorney_reviewed": True,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "evidence_id" in data
        assert data["fre702_score"] == 4
        assert data["daubert_ready"] is True

    def test_partial_fre702_not_daubert_ready(self, client):
        token = _token(client, "advogado", "2")
        r = client.post(
            "/api/v1/legal-evidence/fre707",
            json={
                "case_ref": "24-CV-5678",
                "document_ref": "memo-001",
                "methodology_disclosed": True,
                # Only 1/4 FRE 702 criteria met
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["fre702_score"] == 1
        assert data["daubert_ready"] is False

    def test_update_admissibility_ruling(self, client):
        token = _token(client, "advogado", "3")
        r_create = client.post(
            "/api/v1/legal-evidence/fre707",
            json={"case_ref": "24-CV-9999", "document_ref": "doc-ruling"},
            headers=_auth(token),
        )
        ev_id = r_create.json()["evidence_id"]
        r = client.post(
            f"/api/v1/legal-evidence/fre707/{ev_id}/ruling",
            json={
                "admissibility_opinion": "admissible",
                "court_ruling": "Evidence admitted under FRE 702",
            },
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["admissibility_opinion"] == "admissible"

    def test_list_fre707(self, client):
        token = _token(client, "advogado", "4")
        for i in range(2):
            client.post(
                "/api/v1/legal-evidence/fre707",
                json={"case_ref": f"case-{i}", "document_ref": f"doc-{i}"},
                headers=_auth(token),
            )
        r = client.get("/api/v1/legal-evidence/fre707", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2


# ── Citation Verification ─────────────────────────────────────────────────────


class TestCitationVerification:
    def test_verify_valid_citation(self, client):
        token = _token(client, "advogado", "c1")
        r = client.post(
            "/api/v1/legal-evidence/citations",
            json={
                "document_ref": "brief-001",
                "case_ref": "24-CV-1234",
                "citation_text": "Twombly, 550 U.S. 544 (2007)",
                "citation_type": "case",
                "cited_court": "Supreme Court",
                "cited_year": "2007",
                "reporter": "U.S.",
                "volume": "550",
                "page_start": "544",
                "citation_exists": True,
                "proposition_accurate": True,
                "case_still_good_law": True,
                "verification_method": "westlaw",
                "verification_db": "WL 2024",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "citation_id" in data
        assert data["is_hallucination"] is False
        assert data["accuracy_score"] == 100

    def test_detect_hallucinated_citation(self, client):
        token = _token(client, "advogado", "c2")
        r = client.post(
            "/api/v1/legal-evidence/citations",
            json={
                "document_ref": "brief-hallucinated",
                "citation_text": "Smith v. Jones, 999 F.3d 123 (7th Cir. 2020)",
                "citation_exists": False,   # Case doesn't exist!
                "is_hallucination": True,
                "hallucination_type": "fabricated_citation",
                "hallucination_severity": "critical",
                "hallucination_notes": "Case not found in Westlaw or LexisNexis",
                "filed_with_court": True,
                "bar_complaint_risk": "high",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["is_hallucination"] is True
        assert data["hallucination_severity"] == "critical"

    def test_list_hallucinations(self, client):
        token = _token(client, "advogado", "c3")
        # Create one hallucination and one valid citation
        client.post(
            "/api/v1/legal-evidence/citations",
            json={"document_ref": "doc-hal", "is_hallucination": True,
                  "citation_exists": False, "hallucination_severity": "significant"},
            headers=_auth(token),
        )
        client.post(
            "/api/v1/legal-evidence/citations",
            json={"document_ref": "doc-valid", "citation_exists": True,
                  "is_hallucination": False},
            headers=_auth(token),
        )
        r = client.get("/api/v1/legal-evidence/citations/hallucinations", headers=_auth(token))
        assert r.status_code == 200
        hallucinations = r.json()
        assert len(hallucinations) == 1
        assert hallucinations[0]["is_hallucination"] == 1

    def test_list_citations_by_doc(self, client):
        token = _token(client, "advogado", "c4")
        doc_ref = "brief-main-argument"
        for i in range(3):
            client.post(
                "/api/v1/legal-evidence/citations",
                json={"document_ref": doc_ref, "citation_text": f"Citation {i}"},
                headers=_auth(token),
            )
        r = client.get(f"/api/v1/legal-evidence/citations/doc/{doc_ref}", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) == 3


# ── Hallucination Incidents ───────────────────────────────────────────────────


class TestHallucinationIncidents:
    def test_report_hallucination(self, client):
        token = _token(client, "advogado", "h1")
        r = client.post(
            "/api/v1/legal-evidence/hallucinations",
            json={
                "document_ref": "motion-dismiss-001",
                "case_ref": "24-CV-5555",
                "incident_type": "citation",
                "ai_system": "GPT-4",
                "ai_model": "gpt-4-0125-preview",
                "original_output": "Smith v. Jones, 999 F.3d 123 (fabricated)",
                "correct_info": "Case does not exist",
                "severity": "critical",
                "filed_with_court": True,
                "financial_impact": 5000.0,
                "root_cause": "AI hallucinated non-existent case precedent",
                "prevention_measure": "Added citation verification step before filing",
                "workflow_updated": True,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "incident_id" in data
        assert data["severity"] == "critical"

    def test_resolve_incident(self, client):
        token = _token(client, "advogado", "h2")
        r_create = client.post(
            "/api/v1/legal-evidence/hallucinations",
            json={"document_ref": "doc", "ai_system": "Test", "severity": "medium"},
            headers=_auth(token),
        )
        incident_id = r_create.json()["incident_id"]
        r = client.post(
            f"/api/v1/legal-evidence/hallucinations/{incident_id}/resolve",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"

    def test_list_incidents(self, client):
        token = _token(client, "advogado", "h3")
        for i in range(2):
            client.post(
                "/api/v1/legal-evidence/hallucinations",
                json={"document_ref": f"doc-{i}", "severity": "low"},
                headers=_auth(token),
            )
        r = client.get("/api/v1/legal-evidence/hallucinations", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2


# ── AI Competence Certificates ────────────────────────────────────────────────


class TestAICompetence:
    def test_issue_competence_certificate(self, client):
        token = _token(client, "admin", "k1")
        r = client.post(
            "/api/v1/legal-evidence/competence",
            json={
                "attorney_id": "atty-001",
                "attorney_name": "Maria Silva",
                "bar_number": "CA-123456",
                "jurisdiction": "CA",
                "training_provider": "State Bar of California",
                "training_course": "AI Ethics in Legal Practice 2026",
                "cle_credits_earned": 1.0,
                "training_date": "2026-03-15",
                "training_topics": ["AI tools", "citation verification", "confidentiality"],
                "ai_systems_covered": ["Claude", "GPT-4", "Gemini"],
                "competence_areas": ["research", "drafting"],
                "aba_rule_1_1_compliant": True,
                "state_bar_compliant": True,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "cert_id" in data
        assert data["certificate_number"].startswith("HEILLON-COMP-")
        assert data["aba_rule_1_1_compliant"] is True

    def test_list_and_get_certificate(self, client):
        token = _token(client, "admin", "k2")
        r_create = client.post(
            "/api/v1/legal-evidence/competence",
            json={
                "attorney_id": "atty-002",
                "attorney_name": "João Oliveira",
                "jurisdiction": "NY",
            },
            headers=_auth(token),
        )
        cert_id = r_create.json()["cert_id"]
        r_list = client.get("/api/v1/legal-evidence/competence", headers=_auth(token))
        assert r_list.status_code == 200
        assert len(r_list.json()) >= 1

        r_get = client.get(f"/api/v1/legal-evidence/competence/{cert_id}", headers=_auth(token))
        assert r_get.status_code == 200
        assert r_get.json()["cert_id"] == cert_id

    def test_unauthenticated_denied(self, client):
        r = client.get("/api/v1/legal-evidence/fre707")
        assert r.status_code == 401
