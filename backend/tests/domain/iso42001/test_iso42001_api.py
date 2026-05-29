"""ISO 42001 AIMS + FRIA API tests — Fase 20."""

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
            DATABASE_URL=f"sqlite:///{(tmp_path / 'iso42001.db').as_posix()}",
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
            "email": f"{role}{suffix}@iso.test",
            "name": f"Test {role}",
            "password": "long-secure-pass-iso",
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
    def test_annex_controls_no_auth(self, client):
        r = client.get("/api/v1/iso42001/annex-controls")
        assert r.status_code == 200
        data = r.json()
        assert "A.2" in data
        assert "A.9" in data
        assert len(data) == 8

    def test_eu_charter_rights_no_auth(self, client):
        r = client.get("/api/v1/iso42001/eu-charter-rights")
        assert r.status_code == 200
        data = r.json()
        assert "right_dignity" in data
        assert "right_nondiscrimination" in data
        assert len(data) == 8


# ── AIMS Records ──────────────────────────────────────────────────────────────


class TestAIMSRecords:
    def test_create_basic_aims(self, client):
        token = _token(client, "admin", "1")
        r = client.post(
            "/api/v1/iso42001/aims",
            json={
                "ai_system_ref": "heillon-legal-v1",
                "ai_system_name": "Heillon Legal AI",
                "c4_ai_policy_defined": True,
                "c5_top_mgmt_commitment": True,
                "c5_roles_defined": True,
                "c6_risks_assessed": True,
                "c7_resources_allocated": True,
                "c8_operational_controls": True,
                "c8_human_oversight_active": True,
                "c9_internal_audit_done": True,
                "annex_a2": True,
                "annex_a3": True,
                "annex_a4": True,
                "annex_a5": True,
                "annex_a6": True,
                "annex_a7": True,
                "annex_a8": True,
                "annex_a9": True,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "aims_id" in data
        assert data["conformity_score"] > 0
        assert data["certification_status"] == "not_started"

    def test_full_compliance_score(self, client):
        token = _token(client, "admin", "2")
        r = client.post(
            "/api/v1/iso42001/aims",
            json={
                "ai_system_ref": "test-full",
                "c4_ai_policy_defined": True,
                "c5_top_mgmt_commitment": True,
                "c5_roles_defined": True,
                "c6_risks_assessed": True,
                "c6_opportunities_noted": True,
                "c6_objectives_set": ["obj-1"],
                "c7_resources_allocated": True,
                "c7_awareness_training": True,
                "c8_operational_controls": True,
                "c8_human_oversight_active": True,
                "c9_internal_audit_done": True,
                "c9_mgmt_review_done": True,
                "c10_continual_improvement_plan": "plan",
                "annex_a2": True,
                "annex_a3": True,
                "annex_a4": True,
                "annex_a5": True,
                "annex_a6": True,
                "annex_a7": True,
                "annex_a8": True,
                "annex_a9": True,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["conformity_score"] >= 95

    def test_list_aims(self, client):
        token = _token(client, "admin", "3")
        for i in range(2):
            client.post(
                "/api/v1/iso42001/aims",
                json={"ai_system_ref": f"system-{i}"},
                headers=_auth(token),
            )
        r = client.get("/api/v1/iso42001/aims", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_get_aims(self, client):
        token = _token(client, "admin", "4")
        r_create = client.post(
            "/api/v1/iso42001/aims",
            json={"ai_system_ref": "get-test"},
            headers=_auth(token),
        )
        aims_id = r_create.json()["aims_id"]
        r = client.get(f"/api/v1/iso42001/aims/{aims_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["aims_id"] == aims_id

    def test_update_certification_requires_admin(self, client):
        token_adv = _token(client, "advogado", "5a")
        token_adm = _token(client, "admin", "5b")
        r_create = client.post(
            "/api/v1/iso42001/aims",
            json={"ai_system_ref": "cert-test"},
            headers=_auth(token_adm),
        )
        aims_id = r_create.json()["aims_id"]
        # Non-admin cannot update certification
        r1 = client.post(
            f"/api/v1/iso42001/aims/{aims_id}/cert",
            json={"certification_status": "stage1_audit"},
            headers=_auth(token_adv),
        )
        assert r1.status_code == 403
        # Admin can
        r2 = client.post(
            f"/api/v1/iso42001/aims/{aims_id}/cert",
            json={
                "certification_status": "certified",
                "conformity_score": 92,
                "certification_body": "BSI Group",
                "certificate_number": "ISO42001-2026-001",
            },
            headers=_auth(token_adm),
        )
        assert r2.status_code == 200
        assert r2.json()["certification_status"] == "certified"

    def test_add_control_evidence(self, client):
        token = _token(client, "admin", "6")
        r_create = client.post(
            "/api/v1/iso42001/aims",
            json={"ai_system_ref": "control-test"},
            headers=_auth(token),
        )
        aims_id = r_create.json()["aims_id"]
        r = client.post(
            f"/api/v1/iso42001/aims/{aims_id}/control",
            json={
                "control_ref": "A.6",
                "evidence": "Data governance policy v3.2 approved by DPO",
                "status": "verified",
                "verified_by": "DPO Office",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["control_ref"] == "A.6"

    def test_invalid_control_ref_returns_422(self, client):
        token = _token(client, "admin", "7")
        r_create = client.post(
            "/api/v1/iso42001/aims",
            json={"ai_system_ref": "ctrl-invalid"},
            headers=_auth(token),
        )
        aims_id = r_create.json()["aims_id"]
        r = client.post(
            f"/api/v1/iso42001/aims/{aims_id}/control",
            json={"control_ref": "A.99", "evidence": "whatever"},
            headers=_auth(token),
        )
        assert r.status_code in (422, 400)

    def test_list_control_evidence(self, client):
        token = _token(client, "admin", "8")
        r_create = client.post(
            "/api/v1/iso42001/aims",
            json={"ai_system_ref": "ctrl-list"},
            headers=_auth(token),
        )
        aims_id = r_create.json()["aims_id"]
        for ctrl in ["A.2", "A.7", "A.9"]:
            client.post(
                f"/api/v1/iso42001/aims/{aims_id}/control",
                json={"control_ref": ctrl, "evidence": f"Evidence for {ctrl}"},
                headers=_auth(token),
            )
        r = client.get(
            f"/api/v1/iso42001/aims/{aims_id}/controls", headers=_auth(token)
        )
        assert r.status_code == 200
        assert len(r.json()) == 3


# ── FRIA Assessments ──────────────────────────────────────────────────────────


class TestFRIAAssessments:
    def test_create_fria_draft(self, client):
        token = _token(client, "advogado", "f1")
        r = client.post(
            "/api/v1/iso42001/fria",
            json={
                "ai_system_ref": "legal-ai-v1",
                "ai_system_name": "Heillon Legal AI",
                "intended_purpose": "AI-assisted legal document analysis for EU courts",
                "right_privacy": True,
                "right_nondiscrimination": True,
                "right_fair_trial": True,
                "impact_severity": "medium",
                "impact_likelihood": "medium",
                "impact_description": "Risk of automated decisions affecting legal proceedings",
                "vulnerable_groups_affected": True,
                "vulnerable_groups_desc": "Defendants in criminal proceedings",
                "technical_measures": ["human review gate", "audit trail"],
                "residual_risk_level": "low",
                "deployment_approved": False,
                "dpo_consulted": True,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "fria_id" in data
        assert data["status"] == "draft"
        assert data["deployment_blocked"] is False

    def test_unacceptable_risk_blocks_deployment(self, client):
        token = _token(client, "advogado", "f2")
        r = client.post(
            "/api/v1/iso42001/fria",
            json={
                "ai_system_ref": "risky-ai",
                "impact_severity": "very_high",
                "impact_likelihood": "certain",
                "residual_risk_level": "unacceptable",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["deployment_blocked"] is True

    def test_list_fria(self, client):
        token = _token(client, "advogado", "f3")
        for i in range(2):
            client.post(
                "/api/v1/iso42001/fria",
                json={"ai_system_ref": f"fria-{i}"},
                headers=_auth(token),
            )
        r = client.get("/api/v1/iso42001/fria", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_approve_fria_requires_admin(self, client):
        token_adv = _token(client, "advogado", "f4a")
        token_adm = _token(client, "admin", "f4b")
        r_create = client.post(
            "/api/v1/iso42001/fria",
            json={"ai_system_ref": "approve-test", "residual_risk_level": "low"},
            headers=_auth(token_adv),
        )
        fria_id = r_create.json()["fria_id"]
        # Non-admin fails
        r1 = client.post(
            f"/api/v1/iso42001/fria/{fria_id}/approve",
            json={"decision_notes": "Approved for deployment"},
            headers=_auth(token_adv),
        )
        assert r1.status_code == 403
        # Admin succeeds
        r2 = client.post(
            f"/api/v1/iso42001/fria/{fria_id}/approve",
            json={"decision_notes": "Approved for deployment"},
            headers=_auth(token_adm),
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "approved"

    def test_reject_fria(self, client):
        token = _token(client, "admin", "f5")
        r_create = client.post(
            "/api/v1/iso42001/fria",
            json={"ai_system_ref": "reject-test", "residual_risk_level": "high"},
            headers=_auth(token),
        )
        fria_id = r_create.json()["fria_id"]
        r = client.post(
            f"/api/v1/iso42001/fria/{fria_id}/reject",
            json={"decision_notes": "Residual risk unacceptably high"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"

    def test_unauthenticated_denied(self, client):
        r = client.get("/api/v1/iso42001/aims")
        assert r.status_code == 401
