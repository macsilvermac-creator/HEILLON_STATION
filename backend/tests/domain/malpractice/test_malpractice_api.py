"""Malpractice insurance + compliance scoring API tests — Fase 20."""

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
            DATABASE_URL=f"sqlite:///{(tmp_path / 'malp.db').as_posix()}",
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
            "email": f"{role}{suffix}@malp.test",
            "name": f"Test {role}",
            "password": "long-secure-pass-malp",
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
    def test_colorado_rights_no_auth(self, client):
        r = client.get("/api/v1/malpractice/colorado/rights")
        assert r.status_code == 200
        data = r.json()
        assert "disclosure" in data
        assert "explanation" in data
        assert "human_review" in data

    def test_ccpa_admt_rights_no_auth(self, client):
        r = client.get("/api/v1/malpractice/ccpa-admt/rights")
        assert r.status_code == 200
        data = r.json()
        assert "pre_use_notice" in data
        assert "opt_out" in data

    def test_score_weights_no_auth(self, client):
        r = client.get("/api/v1/malpractice/score/weights")
        assert r.status_code == 200
        data = r.json()
        assert "score_hdr_coverage" in data
        assert "score_iso42001" in data
        assert sum(data.values()) > 0


# ── Colorado SB 26-189 ────────────────────────────────────────────────────────


class TestColoradoSB26189:
    def test_fully_compliant_no_warnings(self, client):
        token = _token(client, "advogado", "co1")
        r = client.post(
            "/api/v1/malpractice/colorado",
            json={
                "ai_system_ref": "heillon-co-v1",
                "consequential_decision_type": "legal_services",
                "consumers_affected_count": 1000,
                "disclosure_provided": True,
                "disclosure_timing": "before",
                "disclosure_method": "in-app",
                "explanation_available": True,
                "explanation_process": "Request via portal within 30 days",
                "data_correction_available": True,
                "data_correction_process": "Submit correction request",
                "human_review_available": True,
                "human_review_process": "Escalation to licensed attorney",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "record_id" in data
        assert data["warnings"] == []
        assert data["rights_score"] == 4
        assert data["is_exempt"] is False

    def test_missing_rights_generate_warnings(self, client):
        token = _token(client, "advogado", "co2")
        r = client.post(
            "/api/v1/malpractice/colorado",
            json={
                "ai_system_ref": "co-partial",
                "consequential_decision_type": "employment",
                # All rights missing
                "disclosure_provided": False,
                "explanation_available": False,
                "data_correction_available": False,
                "human_review_available": False,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert len(data["warnings"]) == 4
        assert data["rights_score"] == 0

    def test_small_business_exempt(self, client):
        token = _token(client, "advogado", "co3")
        r = client.post(
            "/api/v1/malpractice/colorado",
            json={
                "ai_system_ref": "small-biz",
                "small_business_exempt": True,
                # No rights implemented — but exempt
                "disclosure_provided": False,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["warnings"] == []  # Exempt, no warnings
        assert data["is_exempt"] is True

    def test_list_colorado(self, client):
        token = _token(client, "advogado", "co4")
        for i in range(2):
            client.post(
                "/api/v1/malpractice/colorado",
                json={"ai_system_ref": f"co-{i}"},
                headers=_auth(token),
            )
        r = client.get("/api/v1/malpractice/colorado", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2


# ── CCPA ADMT ─────────────────────────────────────────────────────────────────


class TestCCPAADMT:
    def test_create_ccpa_admt_compliant(self, client):
        token = _token(client, "advogado", "admt1")
        r = client.post(
            "/api/v1/malpractice/ccpa-admt",
            json={
                "ai_system_ref": "heillon-ccpa-v1",
                "admt_purpose": "legal",
                "significant_decisions": True,
                "california_consumers": True,
                "pre_use_notice_provided": True,
                "pre_use_notice_content": "This service uses automated decision-making technology",
                "notice_delivery_method": "email + in-app",
                "opt_out_available": True,
                "opt_out_mechanism": "Settings > AI Preferences > Opt Out",
                "opt_out_response_days": 15,
                "global_opt_out_honored": True,
                "access_to_admt_logic": True,
                "access_process": "Request logic summary via privacy dashboard",
                "human_review_available": True,
                "human_review_process": "Attorney review within 5 business days",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "admt_id" in data
        assert data["warnings"] == []
        assert data["rights_compliance_score"] == 4

    def test_missing_notice_and_optout_warn(self, client):
        token = _token(client, "advogado", "admt2")
        r = client.post(
            "/api/v1/malpractice/ccpa-admt",
            json={
                "ai_system_ref": "ccpa-partial",
                "pre_use_notice_provided": False,  # Missing!
                "opt_out_available": False,         # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert len(r.json()["warnings"]) >= 2


# ── Malpractice Insurance ─────────────────────────────────────────────────────


class TestMalpracticeInsurance:
    def test_platinum_score_gives_20pct_discount(self, client):
        token = _token(client, "advogado", "ins1")
        r = client.post(
            "/api/v1/malpractice/insurance",
            json={
                "law_firm_name": "Silva & Associados",
                "bar_jurisdiction": "CA",
                "insurer_name": "LegalShield Insurance",
                "heillon_compliance_score": 93,
                "ai_tools_used": True,
                "ai_tools_list": ["Claude", "Harvey"],
                "citation_verification_process": True,
                "ai_competence_certified": True,
                "hallucination_incidents_12mo": 0,
                "current_premium_usd": 10000,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "insurance_id" in data
        assert data["ai_risk_adjustment"] < 0   # discount
        assert data["estimated_discount_pct"] == 20.0

    def test_hallucinations_add_surcharge(self, client):
        token = _token(client, "advogado", "ins2")
        r = client.post(
            "/api/v1/malpractice/insurance",
            json={
                "law_firm_name": "Reckless Partners",
                "heillon_compliance_score": 30,  # silver
                "hallucination_incidents_12mo": 3,  # 3 incidents!
                "ai_outputs_filed_in_court": True,
                "citation_verification_process": False,  # No verification!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["ai_risk_adjustment"] > 0  # surcharge
        assert data["base_risk_factor"] > 1.0


# ── Heillon Global Compliance Score ──────────────────────────────────────────


class TestHeilonComplianceScore:
    def test_compute_platinum_score(self, client):
        token = _token(client, "advogado", "sc1")
        r = client.post(
            "/api/v1/malpractice/score",
            json={
                "ai_system_ref": "heillon-legal-v1",
                "ai_system_name": "Heillon Legal AI",
                "score_hdr_coverage": 100,
                "score_citation_accuracy": 100,
                "score_hallucination": 100,
                "score_lgpd": 100,
                "score_gdpr_eu": 100,
                "score_gdpr_uk": 100,
                "score_ccpa": 100,
                "score_colorado": 100,
                "score_pdpl_uae": 100,
                "score_pdpa_sg": 100,
                "score_privacy_au": 100,
                "score_pipeda_ca": 100,
                "score_iso42001": 100,
                "score_iso27001": 100,
                "score_nist_rmf": 100,
                "score_euai_act": 100,
                "score_attorney_competence": 100,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "score_id" in data
        assert data["total_score"] == 100
        assert data["certification_tier"] == "platinum"

    def test_compute_bronze_score(self, client):
        token = _token(client, "advogado", "sc2")
        r = client.post(
            "/api/v1/malpractice/score",
            json={
                "ai_system_ref": "low-compliance-ai",
                "score_hdr_coverage": 10,
                "score_citation_accuracy": 20,
                # All others default to 0
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["total_score"] < 50
        assert data["certification_tier"] in ("bronze", "unrated")

    def test_get_latest_score(self, client):
        token = _token(client, "advogado", "sc3")
        ai_ref = "heillon-score-test"
        client.post(
            "/api/v1/malpractice/score",
            json={"ai_system_ref": ai_ref, "score_hdr_coverage": 80,
                  "score_iso42001": 75},
            headers=_auth(token),
        )
        r = client.get(f"/api/v1/malpractice/score/latest/{ai_ref}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["ai_system_ref"] == ai_ref

    def test_list_scores(self, client):
        token = _token(client, "advogado", "sc4")
        for i in range(2):
            client.post(
                "/api/v1/malpractice/score",
                json={"ai_system_ref": f"sys-{i}"},
                headers=_auth(token),
            )
        r = client.get("/api/v1/malpractice/score", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_unauthenticated_denied(self, client):
        r = client.get("/api/v1/malpractice/colorado")
        assert r.status_code == 401
