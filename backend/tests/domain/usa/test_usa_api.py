"""USA regulatory compliance tests — Fase 18.

Covers:
- Colorado AI Act: register high/limited risk systems, warnings, retire (admin)
- CCPA/CPRA: consent record, withdraw
- ABA compliance log: compliance score calculation
- NIST AI RMF: GOVERN/MAP/MEASURE/MANAGE maturity scoring
- ESIGN audit: event sequence, document-level trail
- Reference endpoints (no auth): ABA rules
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config as _cfg
from app.core.config import Settings


@pytest.fixture()
def usa_client(tmp_path, monkeypatch):
    from app.main import create_application

    def _settings() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'usa.db').as_posix()}",
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
    with TestClient(app) as client:
        yield client


def _token(client: TestClient, role: str = "advogado", suffix: str = "") -> str:
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{role}{suffix}@usa.test",
            "name": f"Test {role}",
            "password": "long-secure-pass-usa-test",
            "role": role,
            "organization_id": "org_default",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


# ── Colorado AI Act ────────────────────────────────────────────────────────────


class TestColoradoAIAct:
    def test_register_limited_risk(self, usa_client):
        token = _token(usa_client, "admin", "co1")
        r = usa_client.post(
            "/api/v1/usa/colorado/ai-records",
            json={
                "ai_system_name": "Heillon Legal AI",
                "ai_system_version": "1.0",
                "risk_tier": "limited",
                "deployer_name": "Heillon Ltda",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "record_id" in data
        assert data["risk_tier"] == "limited"
        assert data["warnings"] == []

    def test_register_high_risk_generates_warnings(self, usa_client):
        token = _token(usa_client, "admin", "co2")
        r = usa_client.post(
            "/api/v1/usa/colorado/ai-records",
            json={
                "ai_system_name": "Legal Decision AI",
                "risk_tier": "high",
                "high_risk_category": "legal_services",
                "consequential_decision_desc": "Assists in case outcome prediction",
                # Missing: impact_assessment, bias_audit, consumer notification, opt-out
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert len(data["warnings"]) >= 3  # 4 warnings expected

    def test_register_high_risk_compliant(self, usa_client):
        token = _token(usa_client, "admin", "co3")
        r = usa_client.post(
            "/api/v1/usa/colorado/ai-records",
            json={
                "ai_system_name": "Compliant Legal AI",
                "risk_tier": "high",
                "high_risk_category": "legal_services",
                "impact_assessment_done": True,
                "impact_assessment_date": "2026-01-15",
                "bias_audit_done": True,
                "bias_audit_provider": "Third-Party Auditor Inc.",
                "consumer_notification_text": "You have the right to know this AI is used.",
                "opt_out_mechanism": "https://optout.heillon.com",
                "appeal_process_available": True,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["warnings"] == []

    def test_list_records(self, usa_client):
        token = _token(usa_client, "admin", "co4")
        usa_client.post(
            "/api/v1/usa/colorado/ai-records",
            json={"ai_system_name": "AI System A", "risk_tier": "limited"},
            headers=_auth(token),
        )
        r = usa_client.get("/api/v1/usa/colorado/ai-records", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_filter_by_risk_tier(self, usa_client):
        token = _token(usa_client, "admin", "co5")
        usa_client.post(
            "/api/v1/usa/colorado/ai-records",
            json={"ai_system_name": "High Risk AI", "risk_tier": "high"},
            headers=_auth(token),
        )
        usa_client.post(
            "/api/v1/usa/colorado/ai-records",
            json={"ai_system_name": "Limited AI", "risk_tier": "limited"},
            headers=_auth(token),
        )
        r = usa_client.get(
            "/api/v1/usa/colorado/ai-records?risk_tier=high",
            headers=_auth(token),
        )
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        assert all(i["risk_tier"] == "high" for i in items)

    def test_retire_requires_admin(self, usa_client):
        token_adv = _token(usa_client, "advogado", "co6")
        token_adm = _token(usa_client, "admin", "co7")
        r_create = usa_client.post(
            "/api/v1/usa/colorado/ai-records",
            json={"ai_system_name": "Old AI", "risk_tier": "limited"},
            headers=_auth(token_adm),
        )
        record_id = r_create.json()["record_id"]
        # Non-admin cannot retire
        r1 = usa_client.post(
            f"/api/v1/usa/colorado/ai-records/{record_id}/retire",
            headers=_auth(token_adv),
        )
        assert r1.status_code == 403
        # Admin can retire
        r2 = usa_client.post(
            f"/api/v1/usa/colorado/ai-records/{record_id}/retire",
            headers=_auth(token_adm),
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "retired"


# ── CCPA / CPRA ───────────────────────────────────────────────────────────────


class TestCCPAConsent:
    def test_record_opt_out_consent(self, usa_client):
        token = _token(usa_client, "advogado", "ccpa1")
        r = usa_client.post(
            "/api/v1/usa/ccpa/consent",
            json={
                "consumer_id": "consumer-123",
                "consumer_email": "consumer@california.com",
                "consumer_state": "CA",
                "data_categories": ["browsing_history", "purchase_history"],
                "processing_purposes": ["targeted_advertising", "analytics"],
                "consent_type": "do_not_sell",
                "sale_of_personal_info_consent": False,
                "sharing_for_cross_context": False,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        assert "consent_id" in r.json()

    def test_record_sensitive_data_consent(self, usa_client):
        token = _token(usa_client, "advogado", "ccpa2")
        r = usa_client.post(
            "/api/v1/usa/ccpa/consent",
            json={
                "consumer_id": "consumer-456",
                "consumer_email": "c2@ca.com",
                "consent_type": "opt_in",
                "sensitive_data_consent": True,
                "automated_decision_consent": True,
                "consent_text": "I consent to processing of my sensitive data for AI decisions.",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201

    def test_withdraw_consent(self, usa_client):
        token = _token(usa_client, "advogado", "ccpa3")
        r_create = usa_client.post(
            "/api/v1/usa/ccpa/consent",
            json={"consumer_id": "c789", "consumer_email": "c3@ca.com"},
            headers=_auth(token),
        )
        consent_id = r_create.json()["consent_id"]
        r_withdraw = usa_client.post(
            f"/api/v1/usa/ccpa/consent/{consent_id}/withdraw",
            json={"reason": "Consumer requested deletion per CCPA §1798.105"},
            headers=_auth(token),
        )
        assert r_withdraw.status_code == 200
        assert r_withdraw.json()["status"] == "withdrawn"


# ── ABA Compliance ────────────────────────────────────────────────────────────


class TestABACompliance:
    def test_aba_rules_reference_no_auth(self, usa_client):
        r = usa_client.get("/api/v1/usa/aba/rules")
        assert r.status_code == 200
        rules = r.json()
        assert "1.1" in rules
        assert "1.6" in rules
        assert "5.3" in rules

    def test_log_full_compliance(self, usa_client):
        token = _token(usa_client, "advogado", "aba1")
        r = usa_client.post(
            "/api/v1/usa/aba/compliance",
            json={
                "matter_ref": "matter-2026-001",
                "attorney_name": "Jane Smith, Esq.",
                "ai_tool_name": "Heillon Legal AI",
                "ai_tool_version": "1.0",
                "ai_tool_provider": "Heillon",
                "rule_11_competence": True,
                "rule_16_confidentiality": True,
                "rule_34_fairness": True,
                "rule_53_supervision": True,
                "client_disclosure_made": True,
                "state_bar": "CA",
                "output_reviewed": True,
                "review_notes": "Reviewed all AI suggestions before filing.",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "log_id" in data
        assert data["compliance_score"] == 100  # All 6 flags set

    def test_log_partial_compliance_score(self, usa_client):
        token = _token(usa_client, "advogado", "aba2")
        r = usa_client.post(
            "/api/v1/usa/aba/compliance",
            json={
                "matter_ref": "matter-2026-002",
                "rule_11_competence": True,
                "rule_16_confidentiality": True,
                "rule_53_supervision": True,
                # Missing: rule_34, client_disclosure, output_reviewed → 3/6 = 50%
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["compliance_score"] == 50


# ── NIST AI RMF ───────────────────────────────────────────────────────────────


class TestNISTAIRMF:
    def test_create_full_rmf_record(self, usa_client):
        token = _token(usa_client, "admin", "nist1")
        r = usa_client.post(
            "/api/v1/usa/nist/rmf",
            json={
                "ai_system_ref": "heillon-legal-v1",
                "ai_system_name": "Heillon Legal AI",
                "govern_policies_defined": True,
                "govern_roles_assigned": True,
                "govern_risk_tolerance_set": True,
                "govern_training_completed": True,
                "map_intended_use": "AI-assisted legal document analysis",
                "map_context_established": True,
                "map_risks_identified": [{"risk": "bias", "likelihood": "low"}],
                "map_stakeholders_consulted": True,
                "measure_metrics_defined": True,
                "measure_testing_completed": True,
                "measure_bias_evaluated": True,
                "measure_trustworthiness": 4,
                "manage_risk_responses": [
                    {"response": "mitigate", "control": "human review"}
                ],
                "manage_monitoring_plan": "Monthly performance reviews",
                "manage_incident_plan": "24h response team",
                "profile_tier": "tier-3",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "rmf_id" in data
        assert data["profile_tier"] == "tier-3"
        assert data["maturity_score"] == 100  # All criteria met

    def test_create_partial_rmf_record(self, usa_client):
        token = _token(usa_client, "admin", "nist2")
        r = usa_client.post(
            "/api/v1/usa/nist/rmf",
            json={
                "ai_system_ref": "heillon-legal-v0",
                "govern_policies_defined": True,
                "govern_roles_assigned": True,
                "profile_tier": "tier-1",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["maturity_score"] < 100
        assert data["function_scores"]["GOVERN"] == 2
        assert data["function_scores"]["MAP"] == 0

    def test_get_rmf_record(self, usa_client):
        token = _token(usa_client, "admin", "nist3")
        r_create = usa_client.post(
            "/api/v1/usa/nist/rmf",
            json={"ai_system_ref": "sys-abc"},
            headers=_auth(token),
        )
        rmf_id = r_create.json()["rmf_id"]
        r = usa_client.get(f"/api/v1/usa/nist/rmf/{rmf_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["ai_system_ref"] == "sys-abc"


# ── ESIGN Audit ───────────────────────────────────────────────────────────────


class TestESIGNAudit:
    def test_log_event_sequence(self, usa_client):
        token = _token(usa_client, "advogado", "esign1")
        doc_ref = "settlement-2026-001"

        events = [
            ("document_created", 1),
            ("invitation_sent", 2),
            ("document_viewed", 3),
            ("signed", 4),
            ("completed", 5),
        ]
        for event_type, seq in events:
            r = usa_client.post(
                "/api/v1/usa/esign/audit",
                json={
                    "event_type": event_type,
                    "actor_email": "attorney@firma.com",
                    "document_ref": doc_ref,
                    "event_sequence": seq,
                },
                headers=_auth(token),
            )
            assert r.status_code == 201

        r_trail = usa_client.get(
            f"/api/v1/usa/esign/audit/document/{doc_ref}",
            headers=_auth(token),
        )
        assert r_trail.status_code == 200
        trail = r_trail.json()
        assert len(trail) == 5
        # Must be sorted by sequence
        seqs = [e["event_sequence"] for e in trail]
        assert seqs == sorted(seqs)

    def test_event_hash_generated(self, usa_client):
        token = _token(usa_client, "advogado", "esign2")
        r = usa_client.post(
            "/api/v1/usa/esign/audit",
            json={
                "event_type": "signed",
                "actor_email": "signer@firm.com",
                "document_ref": "doc-esign-001",
                "document_hash": "a" * 64,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert "audit_id" in data
        assert len(data["event_hash"]) == 64  # SHA-256

    def test_unauthenticated_denied(self, usa_client):
        r = usa_client.get("/api/v1/usa/colorado/ai-records")
        assert r.status_code == 401
