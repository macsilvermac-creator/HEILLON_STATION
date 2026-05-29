"""F17 — EU AI Act + eIDAS 2.0 + ISO 27001 API tests.

Covers:
- EU AI Act Annex IV technical documentation CRUD
- Conformity assessment marking
- GDPR/LGPD DPIA creation and approval
- eIDAS 2.0 QES signature record
- ISO 27001 ISMS risk register (score-based level assignment)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config as _cfg
from app.core.config import Settings


# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture()
def euai_client(tmp_path, monkeypatch):
    """Isolated TestClient for euaiact domain tests."""
    from app.main import create_application

    def _settings() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'euai.db').as_posix()}",
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


def _register_and_token(
    client: TestClient,
    *,
    role: str = "advogado",
    suffix: str = "",
) -> tuple[str, str]:
    email = f"{role}{suffix}@euai.test"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": f"Test {role} {suffix}",
            "password": "long-secure-password-euai-test",
            "role": role,
            "organization_id": "org_default",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"], data["user"]["user_id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── EU AI Act Technical Documentation ─────────────────────────────────────────


class TestEUAITechDocs:
    def test_create_tech_doc(self, euai_client):
        token, _ = _register_and_token(euai_client, role="admin", suffix="td1")
        r = euai_client.post(
            "/api/v1/euaiact/tech-docs",
            json={
                "system_name": "Heillon Legal AI",
                "system_version": "1.0",
                "risk_category": "high",
                "annex_iii_category": "administration_justice",
                "intended_purpose": "AI-assisted legal document analysis",
                "human_oversight": {"measures": ["mandatory review", "audit logs"]},
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "doc_id" in data
        assert data["status"] == "draft"

    def test_list_tech_docs(self, euai_client):
        token, _ = _register_and_token(euai_client, role="perito", suffix="td2")
        euai_client.post(
            "/api/v1/euaiact/tech-docs",
            json={"system_name": "Sys A", "risk_category": "limited"},
            headers=_auth(token),
        )
        r = euai_client.get("/api/v1/euaiact/tech-docs", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_tech_doc_with_summary(self, euai_client):
        token, _ = _register_and_token(euai_client, role="advogado", suffix="td3")
        create_r = euai_client.post(
            "/api/v1/euaiact/tech-docs",
            json={"system_name": "Sys B", "risk_category": "high"},
            headers=_auth(token),
        )
        doc_id = create_r.json()["doc_id"]
        r = euai_client.get(f"/api/v1/euaiact/tech-docs/{doc_id}", headers=_auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["doc_id"] == doc_id
        assert "EU AI Act" in data["_summary"]

    def test_activate_tech_doc(self, euai_client):
        token, _ = _register_and_token(euai_client, role="admin", suffix="td4")
        create_r = euai_client.post(
            "/api/v1/euaiact/tech-docs",
            json={"system_name": "Sys C", "risk_category": "high"},
            headers=_auth(token),
        )
        doc_id = create_r.json()["doc_id"]
        r = euai_client.post(
            f"/api/v1/euaiact/tech-docs/{doc_id}/activate", headers=_auth(token)
        )
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    def test_mark_conformity(self, euai_client):
        token, _ = _register_and_token(euai_client, role="admin", suffix="td5")
        create_r = euai_client.post(
            "/api/v1/euaiact/tech-docs",
            json={"system_name": "Sys D", "risk_category": "high"},
            headers=_auth(token),
        )
        doc_id = create_r.json()["doc_id"]
        r = euai_client.post(
            f"/api/v1/euaiact/tech-docs/{doc_id}/conformity",
            json={"notified_body": "BSI — Germany"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["conformity_assessed"] == "true"

    def test_unknown_doc_returns_404(self, euai_client):
        token, _ = _register_and_token(euai_client, role="perito", suffix="td6")
        r = euai_client.get(
            "/api/v1/euaiact/tech-docs/nonexistent", headers=_auth(token)
        )
        assert r.status_code == 404

    def test_invalid_risk_category_returns_422(self, euai_client):
        token, _ = _register_and_token(euai_client, role="perito", suffix="td7")
        r = euai_client.post(
            "/api/v1/euaiact/tech-docs",
            json={"system_name": "X", "risk_category": "extreme"},
            headers=_auth(token),
        )
        assert r.status_code == 422


# ── DPIA Tests ─────────────────────────────────────────────────────────────────


class TestDPIA:
    def test_create_dpia(self, euai_client):
        token, _ = _register_and_token(euai_client, role="advogado", suffix="dp1")
        r = euai_client.post(
            "/api/v1/euaiact/dpia",
            json={
                "processing_name": "AI Legal Document Analysis",
                "processing_purpose": "Assist lawyers in document review",
                "legal_basis": "legitimate_interest",
                "data_categories": ["legal_documents", "personal_data"],
                "data_subjects": ["clients", "opposing_parties"],
                "necessity_assessment": "Processing is necessary for AI-assisted analysis",
                "proportionality_check": "Data minimisation applied; only necessary fields processed",
                "risks_identified": [
                    {"risk": "data leak", "likelihood": "low", "impact": "high"}
                ],
                "mitigations": [{"measure": "encryption", "residual_risk": "very_low"}],
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        assert "dpia_id" in r.json()

    def test_list_dpias(self, euai_client):
        token, _ = _register_and_token(euai_client, role="advogado", suffix="dp2")
        euai_client.post(
            "/api/v1/euaiact/dpia",
            json={"processing_name": "Processing A"},
            headers=_auth(token),
        )
        r = euai_client.get("/api/v1/euaiact/dpia", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_dpia(self, euai_client):
        token, _ = _register_and_token(euai_client, role="advogado", suffix="dp3")
        create_r = euai_client.post(
            "/api/v1/euaiact/dpia",
            json={"processing_name": "Processing B"},
            headers=_auth(token),
        )
        dpia_id = create_r.json()["dpia_id"]
        r = euai_client.get(f"/api/v1/euaiact/dpia/{dpia_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["status"] == "draft"

    def test_approve_dpia_requires_admin(self, euai_client):
        token_adv, _ = _register_and_token(euai_client, role="advogado", suffix="dp4")
        token_adm, _ = _register_and_token(euai_client, role="admin", suffix="dp5")
        create_r = euai_client.post(
            "/api/v1/euaiact/dpia",
            json={"processing_name": "Processing C"},
            headers=_auth(token_adv),
        )
        dpia_id = create_r.json()["dpia_id"]
        # Non-admin cannot approve
        r1 = euai_client.post(
            f"/api/v1/euaiact/dpia/{dpia_id}/approve", headers=_auth(token_adv)
        )
        assert r1.status_code == 403
        # Admin can approve
        r2 = euai_client.post(
            f"/api/v1/euaiact/dpia/{dpia_id}/approve", headers=_auth(token_adm)
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "approved"


# ── eIDAS QES Tests ────────────────────────────────────────────────────────────


class TestEIDASQES:
    def test_record_qes(self, euai_client):
        token, _ = _register_and_token(euai_client, role="advogado", suffix="q1")
        r = euai_client.post(
            "/api/v1/euaiact/qes",
            json={
                "document_type": "expert_report",
                "document_ref": "exp-report-001",
                "document_hash": "a" * 64,
                "signatory_name": "Dr. Advogado Silva",
                "signatory_email": "advogado@firma.com",
                "qtsp_provider": "Certisign",
                "qtsp_country": "BR",
                "signature_format": "PAdES-LTA",
                "signature_level": "QES",
                "eudi_wallet_used": False,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        assert "qes_id" in r.json()

    def test_list_qes(self, euai_client):
        token, _ = _register_and_token(euai_client, role="advogado", suffix="q2")
        euai_client.post(
            "/api/v1/euaiact/qes",
            json={
                "document_type": "contract",
                "document_ref": "contract-001",
                "document_hash": "b" * 64,
                "signatory_name": "Test User",
                "signatory_email": "test@test.com",
            },
            headers=_auth(token),
        )
        r = euai_client.get("/api/v1/euaiact/qes", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_invalid_document_hash_returns_422(self, euai_client):
        token, _ = _register_and_token(euai_client, role="advogado", suffix="q3")
        r = euai_client.post(
            "/api/v1/euaiact/qes",
            json={
                "document_type": "contract",
                "document_ref": "r001",
                "document_hash": "too-short",  # not 64 chars
                "signatory_name": "X",
                "signatory_email": "x@x.com",
            },
            headers=_auth(token),
        )
        assert r.status_code == 422


# ── ISO 27001 ISMS Risk Tests ──────────────────────────────────────────────────


class TestISMSRisks:
    def test_register_risk_computes_level(self, euai_client):
        token, _ = _register_and_token(euai_client, role="admin", suffix="isms1")
        r = euai_client.post(
            "/api/v1/euaiact/isms/risks",
            json={
                "asset": "Client legal documents",
                "threat": "Unauthorized access via compromised API key",
                "vulnerability": "API keys stored in plaintext config",
                "likelihood": 3,
                "impact": 4,
                "control_ref": "A.8.1",
                "control_description": "Asset inventory and access control",
                "treatment_option": "mitigate",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "risk_id" in data
        assert data["risk_score"] == 12  # 3 × 4
        assert data["risk_level"] == "high"  # score 10-14

    def test_risk_level_low(self, euai_client):
        token, _ = _register_and_token(euai_client, role="admin", suffix="isms2")
        r = euai_client.post(
            "/api/v1/euaiact/isms/risks",
            json={
                "asset": "Office WiFi",
                "threat": "Guest network eavesdropping",
                "likelihood": 1,
                "impact": 2,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["risk_level"] == "low"  # score 2

    def test_risk_level_critical(self, euai_client):
        token, _ = _register_and_token(euai_client, role="admin", suffix="isms3")
        r = euai_client.post(
            "/api/v1/euaiact/isms/risks",
            json={
                "asset": "Production database",
                "threat": "SQL injection attack",
                "likelihood": 5,
                "impact": 5,
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["risk_level"] == "critical"  # score 25

    def test_list_risks_filtered_by_level(self, euai_client):
        token, _ = _register_and_token(euai_client, role="admin", suffix="isms4")
        euai_client.post(
            "/api/v1/euaiact/isms/risks",
            json={"asset": "A", "threat": "T", "likelihood": 5, "impact": 5},
            headers=_auth(token),
        )
        r = euai_client.get(
            "/api/v1/euaiact/isms/risks?risk_level=critical",
            headers=_auth(token),
        )
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        assert all(i["risk_level"] == "critical" for i in items)

    def test_close_risk_requires_admin(self, euai_client):
        token_adv, _ = _register_and_token(euai_client, role="advogado", suffix="isms5")
        token_adm, _ = _register_and_token(euai_client, role="admin", suffix="isms6")
        create_r = euai_client.post(
            "/api/v1/euaiact/isms/risks",
            json={"asset": "B", "threat": "T2", "likelihood": 2, "impact": 2},
            headers=_auth(token_adm),
        )
        risk_id = create_r.json()["risk_id"]
        # Non-admin cannot close
        r1 = euai_client.post(
            f"/api/v1/euaiact/isms/risks/{risk_id}/close", headers=_auth(token_adv)
        )
        assert r1.status_code == 403
        # Admin can close
        r2 = euai_client.post(
            f"/api/v1/euaiact/isms/risks/{risk_id}/close", headers=_auth(token_adm)
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "closed"

    def test_get_risk_returns_details(self, euai_client):
        token, _ = _register_and_token(euai_client, role="admin", suffix="isms7")
        create_r = euai_client.post(
            "/api/v1/euaiact/isms/risks",
            json={
                "asset": "API Gateway",
                "threat": "DDoS",
                "likelihood": 4,
                "impact": 3,
                "control_ref": "A.12.6",
                "treatment_option": "transfer",
            },
            headers=_auth(token),
        )
        risk_id = create_r.json()["risk_id"]
        r = euai_client.get(
            f"/api/v1/euaiact/isms/risks/{risk_id}", headers=_auth(token)
        )
        assert r.status_code == 200
        data = r.json()
        assert data["risk_id"] == risk_id
        assert data["control_ref"] == "A.12.6"
        assert data["treatment_option"] == "transfer"

    def test_unauthenticated_access_denied(self, euai_client):
        r = euai_client.get("/api/v1/euaiact/isms/risks")
        assert r.status_code == 401
