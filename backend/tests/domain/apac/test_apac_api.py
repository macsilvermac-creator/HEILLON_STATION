"""APAC privacy compliance API tests — UK / Canada / Singapore / Australia — Fase 20."""

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
            DATABASE_URL=f"sqlite:///{(tmp_path / 'apac.db').as_posix()}",
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
            "email": f"{role}{suffix}@apac.test",
            "name": f"Test {role}",
            "password": "long-secure-pass-apac",
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
    def test_uk_ico_exemptions_no_auth(self, client):
        r = client.get("/api/v1/apac/uk/ico-exemptions")
        assert r.status_code == 200
        data = r.json()
        assert "small_business" in data

    def test_sg_agentic_obligations_no_auth(self, client):
        r = client.get("/api/v1/apac/singapore/agentic-obligations")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 5
        assert "accountability" in data
        assert "transparency" in data

    def test_au_privacy_principles_no_auth(self, client):
        r = client.get("/api/v1/apac/australia/privacy-principles")
        assert r.status_code == 200
        data = r.json()
        assert "APP1" in data
        assert len(data) == 13


# ── UK GDPR ───────────────────────────────────────────────────────────────────


class TestUKGDPR:
    def test_create_uk_gdpr_registered(self, client):
        token = _token(client, "advogado", "uk1")
        r = client.post(
            "/api/v1/apac/uk",
            json={
                "ai_system_ref": "heillon-uk-v1",
                "ai_system_name": "Heillon Legal UK",
                "ico_reference": "ZB123456",
                "ico_registered": True,
                "data_protection_fee_paid": True,
                "lawful_basis": "legitimate_interests",
                "ai_code_applicable": True,
                "transparency_notice_published": True,
                "human_review_available": True,
                "dpo_required": True,
                "dpo_name": "Jane Smith",
                "eu_transfer_mechanism": "idta",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "record_id" in data
        assert data["warnings"] == []

    def test_unregistered_ico_generates_warning(self, client):
        token = _token(client, "advogado", "uk2")
        r = client.post(
            "/api/v1/apac/uk",
            json={
                "ai_system_ref": "uk-unregistered",
                "ico_registered": False,  # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert len(r.json()["warnings"]) > 0
        assert any("ICO" in w for w in r.json()["warnings"])

    def test_profiling_without_basis_generates_warning(self, client):
        token = _token(client, "advogado", "uk3")
        r = client.post(
            "/api/v1/apac/uk",
            json={
                "ai_system_ref": "profiling-ai",
                "ico_registered": True,
                "profiling_used": True,
                "profiling_basis": "",  # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert any("profiling" in w.lower() for w in r.json()["warnings"])

    def test_list_uk_gdpr(self, client):
        token = _token(client, "advogado", "uk4")
        for i in range(2):
            client.post(
                "/api/v1/apac/uk",
                json={"ai_system_ref": f"uk-{i}"},
                headers=_auth(token),
            )
        r = client.get("/api/v1/apac/uk", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2


# ── Canada ────────────────────────────────────────────────────────────────────


class TestCanadaPrivacy:
    def test_create_canada_aida(self, client):
        token = _token(client, "advogado", "ca1")
        r = client.post(
            "/api/v1/apac/canada",
            json={
                "ai_system_ref": "heillon-ca-v1",
                "provincial_law": "federal",
                "aida_applicable": True,
                "high_impact_system": True,
                "high_impact_categories": ["legal_services", "employment"],
                "impact_assessment_done": True,
                "mitigation_measures": ["human oversight", "audit trail"],
                "incident_reporting_process": "72h to OPC for major breaches",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "record_id" in data
        assert data["warnings"] == []

    def test_aida_missing_impact_assessment_warns(self, client):
        token = _token(client, "advogado", "ca2")
        r = client.post(
            "/api/v1/apac/canada",
            json={
                "ai_system_ref": "ca-no-impact",
                "aida_applicable": True,
                "high_impact_system": True,
                "impact_assessment_done": False,  # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert any("AIDA" in w for w in r.json()["warnings"])

    def test_quebec_law25_requires_officer(self, client):
        token = _token(client, "advogado", "ca3")
        r = client.post(
            "/api/v1/apac/canada",
            json={
                "ai_system_ref": "ca-quebec",
                "law_25_quebec": True,
                "q25_privacy_officer": "",  # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert any("Law 25" in w for w in r.json()["warnings"])


# ── Singapore ─────────────────────────────────────────────────────────────────


class TestSingaporePDPA:
    def test_create_agentic_ai_full_compliance(self, client):
        token = _token(client, "advogado", "sg1")
        r = client.post(
            "/api/v1/apac/singapore",
            json={
                "ai_system_ref": "heillon-sg-v1",
                "pdpa_dpo_designated": True,
                "pdpa_dpo_name": "Wei Chen",
                "pdpa_dpo_registered": True,
                "data_protection_policy_published": True,
                "consent_purpose_specific": True,
                "notification_given": True,
                "agentic_ai_applicable": True,
                "agentic_human_oversight": True,
                "agentic_oversight_desc": "Human-in-the-loop for all decisions",
                "agentic_disclosure": True,
                "agentic_disclosure_text": "You are interacting with an AI agent",
                "agentic_consent_scope": "Consent for automated data access",
                "agentic_data_minimised": True,
                "agentic_incident_plan": "24h incident response protocol",
                "pdpc_model_governance_aligned": True,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "record_id" in data
        assert data["warnings"] == []
        assert data["agentic_compliance_score"] == 5

    def test_agentic_without_oversight_warns(self, client):
        token = _token(client, "advogado", "sg2")
        r = client.post(
            "/api/v1/apac/singapore",
            json={
                "ai_system_ref": "sg-no-oversight",
                "agentic_ai_applicable": True,
                "agentic_human_oversight": False,  # Missing!
                "agentic_disclosure": False,  # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert len(r.json()["warnings"]) >= 2
        assert r.json()["agentic_compliance_score"] == 0

    def test_list_singapore(self, client):
        token = _token(client, "advogado", "sg3")
        for i in range(2):
            client.post(
                "/api/v1/apac/singapore",
                json={"ai_system_ref": f"sg-{i}"},
                headers=_auth(token),
            )
        r = client.get("/api/v1/apac/singapore", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2


# ── Australia ─────────────────────────────────────────────────────────────────


class TestAustraliaPrivacy:
    def test_create_australia_full_apps(self, client):
        token = _token(client, "advogado", "au1")
        r = client.post(
            "/api/v1/apac/australia",
            json={
                "ai_system_ref": "heillon-au-v1",
                "annual_turnover_aud": 50000000,
                "acts_covered": True,
                "app1_privacy_policy": True,
                "app5_collection_notice": True,
                "app6_primary_purpose_only": True,
                "app11_security_measures": "AES-256 encryption, MFA, pen testing",
                "app12_access_process": "Subject access requests within 30 days",
                "app13_correction_process": "Correction requests within 14 days",
                "adm_used": True,
                "adm_description": "AI-assisted legal document analysis",
                "adm_explanation_available": True,
                "adm_human_review_available": True,
                "adm_meaningful_impact": True,
                "ndb_scheme_applicable": True,
                "breach_assessment_process": "30-day OAIC notification",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "record_id" in data
        assert data["warnings"] == []
        assert data["app_coverage_score"] == 100

    def test_adm_meaningful_without_explanation_warns(self, client):
        token = _token(client, "advogado", "au2")
        r = client.post(
            "/api/v1/apac/australia",
            json={
                "ai_system_ref": "au-adm-no-explain",
                "adm_used": True,
                "adm_meaningful_impact": True,
                "adm_explanation_available": False,  # Missing!
                "adm_human_review_available": False,  # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert len(r.json()["warnings"]) >= 2

    def test_get_australia_record(self, client):
        token = _token(client, "advogado", "au3")
        r_create = client.post(
            "/api/v1/apac/australia",
            json={"ai_system_ref": "au-get-test"},
            headers=_auth(token),
        )
        record_id = r_create.json()["record_id"]
        r = client.get(f"/api/v1/apac/australia/{record_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["record_id"] == record_id

    def test_unauthenticated_denied(self, client):
        r = client.get("/api/v1/apac/uk")
        assert r.status_code == 401
