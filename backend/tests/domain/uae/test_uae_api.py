"""UAE regulatory compliance tests — Fase 19.

Covers:
- UAE PDPL: consent, children data warning, cross-border transfer warning, withdraw
- UAE AI Governance: ethics score, seal eligibility, apply seal (admin)
- UAE AI Ethics 7 pillars reference (no auth)
- DIFC requirements reference (no auth)
- UAE PASS signatures: record, list, get
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config as _cfg
from app.core.config import Settings


@pytest.fixture()
def uae_client(tmp_path, monkeypatch):
    from app.main import create_application

    def _settings() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'uae.db').as_posix()}",
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
            "email": f"{role}{suffix}@uae.test",
            "name": f"Test {role}",
            "password": "long-secure-pass-uae-test",
            "role": role,
            "organization_id": "org_default",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


# ── UAE PDPL Consent ──────────────────────────────────────────────────────────


class TestUAEPDPLConsent:
    def test_create_basic_consent(self, uae_client):
        token = _token(uae_client, "advogado", "pdpl1")
        r = uae_client.post(
            "/api/v1/uae/pdpl/consent",
            json={
                "data_subject_id": "subject-001",
                "data_subject_name": "Ahmed Al-Mansouri",
                "data_subject_email": "ahmed@example.ae",
                "data_subject_nationality": "Emirati",
                "data_categories": ["identity", "legal_documents"],
                "processing_purposes": ["case_management", "compliance"],
                "legal_basis": "contract",
                "language": "ar",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "consent_id" in data
        assert data["warnings"] == []

    def test_children_data_without_guardian_generates_warning(self, uae_client):
        token = _token(uae_client, "advogado", "pdpl2")
        r = uae_client.post(
            "/api/v1/uae/pdpl/consent",
            json={
                "data_subject_id": "minor-001",
                "data_subject_name": "Young Person",
                "children_data": True,
                "guardian_consent_obtained": False,  # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert any("Guardian" in w for w in r.json()["warnings"])

    def test_cross_border_without_safeguards_generates_warning(self, uae_client):
        token = _token(uae_client, "advogado", "pdpl3")
        r = uae_client.post(
            "/api/v1/uae/pdpl/consent",
            json={
                "data_subject_id": "subject-002",
                "data_subject_name": "Maria Silva",
                "cross_border_transfer": True,
                "transfer_destination_country": "BR",
                "transfer_safeguards": "",  # Missing!
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert any("transfer" in w.lower() for w in r.json()["warnings"])

    def test_difc_jurisdiction_flagged(self, uae_client):
        token = _token(uae_client, "advogado", "pdpl4")
        r = uae_client.post(
            "/api/v1/uae/pdpl/consent",
            json={
                "data_subject_id": "difc-subject-001",
                "data_subject_name": "DIFC Client",
                "difc_jurisdiction": True,
                "legal_basis": "contract",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        consent_id = r.json()["consent_id"]
        r_get = uae_client.get(
            f"/api/v1/uae/pdpl/consent/{consent_id}",
            headers=_auth(token),
        )
        assert r_get.json()["difc_jurisdiction"] == 1

    def test_withdraw_consent(self, uae_client):
        token = _token(uae_client, "advogado", "pdpl5")
        r_create = uae_client.post(
            "/api/v1/uae/pdpl/consent",
            json={
                "data_subject_id": "subject-003",
                "data_subject_name": "Fatima Al-Hassan",
            },
            headers=_auth(token),
        )
        consent_id = r_create.json()["consent_id"]
        r_withdraw = uae_client.post(
            f"/api/v1/uae/pdpl/consent/{consent_id}/withdraw",
            json={"reason": "Data subject requested deletion per PDPL Art. 16"},
            headers=_auth(token),
        )
        assert r_withdraw.status_code == 200
        assert r_withdraw.json()["status"] == "withdrawn"

    def test_invalid_legal_basis_returns_422(self, uae_client):
        token = _token(uae_client, "advogado", "pdpl6")
        r = uae_client.post(
            "/api/v1/uae/pdpl/consent",
            json={
                "data_subject_id": "s001",
                "data_subject_name": "Test",
                "legal_basis": "guessing",  # Invalid
            },
            headers=_auth(token),
        )
        assert r.status_code == 422


# ── UAE AI Governance ──────────────────────────────────────────────────────────


class TestUAEAIGovernance:
    def test_ethics_principles_no_auth(self, uae_client):
        r = uae_client.get("/api/v1/uae/governance/ethics-principles")
        assert r.status_code == 200
        principles = r.json()
        assert len(principles) == 7
        assert "ethics_human_centered" in principles
        assert "ethics_sustainability" in principles

    def test_difc_requirements_no_auth(self, uae_client):
        r = uae_client.get("/api/v1/uae/governance/difc-requirements")
        assert r.status_code == 200
        reqs = r.json()
        assert "lawful_basis" in reqs

    def test_register_all_ethics_principles(self, uae_client):
        token = _token(uae_client, "admin", "gov1")
        r = uae_client.post(
            "/api/v1/uae/governance",
            json={
                "ai_system_name": "Heillon Legal AI",
                "ai_system_version": "1.0",
                "ai_system_purpose": "AI-assisted legal analysis for UAE market",
                "ethics_human_centered": True,
                "ethics_fairness": True,
                "ethics_transparency": True,
                "ethics_safety_reliability": True,
                "ethics_privacy_security": True,
                "ethics_accountability": True,
                "ethics_sustainability": True,
                "sector": "legal",
                "jurisdiction_ae": "difc",
                "difc_compliant": True,
                "risk_level": "low",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "gov_id" in data
        assert data["ethics_score"] == 100
        assert data["seal_eligible"] is True

    def test_partial_ethics_not_seal_eligible(self, uae_client):
        token = _token(uae_client, "admin", "gov2")
        r = uae_client.post(
            "/api/v1/uae/governance",
            json={
                "ai_system_name": "Partial AI",
                "ethics_human_centered": True,
                "ethics_fairness": True,
                "ethics_transparency": True,
                # Only 3/7 principles → 43% → not seal eligible
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["ethics_score"] < 86
        assert data["seal_eligible"] is False

    def test_apply_seal_requires_admin(self, uae_client):
        token_adv = _token(uae_client, "advogado", "gov3")
        token_adm = _token(uae_client, "admin", "gov4")

        r_create = uae_client.post(
            "/api/v1/uae/governance",
            json={
                "ai_system_name": "Seal Test AI",
                "ethics_human_centered": True,
                "ethics_fairness": True,
                "ethics_transparency": True,
                "ethics_safety_reliability": True,
                "ethics_privacy_security": True,
                "ethics_accountability": True,
                "ethics_sustainability": True,
            },
            headers=_auth(token_adm),
        )
        gov_id = r_create.json()["gov_id"]

        # Non-admin cannot apply seal
        r1 = uae_client.post(
            f"/api/v1/uae/governance/{gov_id}/seal",
            json={"seal_reference": "SEAL-2026-001", "seal_category": "commercial"},
            headers=_auth(token_adv),
        )
        assert r1.status_code == 403

        # Admin can apply seal
        r2 = uae_client.post(
            f"/api/v1/uae/governance/{gov_id}/seal",
            json={"seal_reference": "SEAL-2026-001", "seal_category": "commercial"},
            headers=_auth(token_adm),
        )
        assert r2.status_code == 200
        assert r2.json()["ai_seal_applied"] == "true"
        assert r2.json()["seal_reference"] == "SEAL-2026-001"

    def test_list_governance_records(self, uae_client):
        token = _token(uae_client, "admin", "gov5")
        for i in range(2):
            uae_client.post(
                "/api/v1/uae/governance",
                json={"ai_system_name": f"AI System {i}", "jurisdiction_ae": "federal"},
                headers=_auth(token),
            )
        r = uae_client.get("/api/v1/uae/governance", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 2


# ── UAE PASS Signatures ────────────────────────────────────────────────────────


class TestUAEPassSignatures:
    def test_record_uae_pass_signature(self, uae_client):
        token = _token(uae_client, "advogado", "pass1")
        r = uae_client.post(
            "/api/v1/uae/pass/sign",
            json={
                "document_ref": "power-of-attorney-001",
                "document_hash": "a" * 64,
                "document_title": "Power of Attorney",
                "signatory_name": "Ahmed Al-Rashid",
                "signatory_email": "ahmed@difc.ae",
                "signatory_emirates_id": "784-1990-1234567-1",
                "uae_pass_verified": True,
                "uae_pass_identity_level": "qualified",
                "uae_pass_session_ref": "uaepass-session-abc123",
                "trust_service_provider": "TDRA",
                "trust_service_level": "qualified",
                "signature_format": "PAdES-LTA",
                "signature_level": "QES",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "sig_id" in data
        assert data["signature_level"] == "QES"

    def test_record_advanced_signature(self, uae_client):
        token = _token(uae_client, "advogado", "pass2")
        r = uae_client.post(
            "/api/v1/uae/pass/sign",
            json={
                "document_ref": "nda-001",
                "document_hash": "b" * 64,
                "signatory_name": "Omar Al-Farsi",
                "signatory_email": "omar@adgm.ae",
                "trust_service_provider": "Etisalat",
                "trust_service_level": "advanced",
                "signature_level": "AES",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201

    def test_invalid_hash_returns_422(self, uae_client):
        token = _token(uae_client, "advogado", "pass3")
        r = uae_client.post(
            "/api/v1/uae/pass/sign",
            json={
                "document_ref": "doc-001",
                "document_hash": "tooshort",
                "signatory_name": "X",
                "signatory_email": "x@x.ae",
            },
            headers=_auth(token),
        )
        assert r.status_code == 422

    def test_list_uae_pass_signatures(self, uae_client):
        token = _token(uae_client, "advogado", "pass4")
        uae_client.post(
            "/api/v1/uae/pass/sign",
            json={
                "document_ref": "doc-list-1",
                "document_hash": "c" * 64,
                "signatory_name": "Signer",
                "signatory_email": "s@ae.ae",
            },
            headers=_auth(token),
        )
        r = uae_client.get("/api/v1/uae/pass/sign", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_uae_pass_signature(self, uae_client):
        token = _token(uae_client, "advogado", "pass5")
        r_create = uae_client.post(
            "/api/v1/uae/pass/sign",
            json={
                "document_ref": "get-test-001",
                "document_hash": "d" * 64,
                "signatory_name": "Get Signer",
                "signatory_email": "gs@ae.ae",
            },
            headers=_auth(token),
        )
        sig_id = r_create.json()["sig_id"]
        r = uae_client.get(f"/api/v1/uae/pass/sign/{sig_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["sig_id"] == sig_id

    def test_unauthenticated_denied(self, uae_client):
        r = uae_client.get("/api/v1/uae/pdpl/consent")
        assert r.status_code == 401
