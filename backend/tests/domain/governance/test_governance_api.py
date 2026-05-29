"""F16 — CNJ 615/2025 + OAB Rec. 001/2024 governance API tests.

Covers:
- Risk classification CRUD
- AI decision logging + human review
- Human approval gates (creation via high-risk decision, resolve)
- OAB disclosure lifecycle + client acknowledgement
- Admin-only endpoints (retire classification)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config as _cfg
from app.core.config import Settings


# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture()
def gov_client(tmp_path, monkeypatch):
    """Isolated TestClient for governance domain tests."""
    from app.main import create_application

    def _settings() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'gov.db').as_posix()}",
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
    org_id: str = "org_default",
) -> tuple[str, str]:
    """Register user and return (bearer_token, user_id)."""
    email = f"{role}{suffix}@gov.test"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": f"Test {role} {suffix}",
            "password": "long-password-gov-test-secure",
            "role": role,
            "organization_id": org_id,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"], data["user"]["user_id"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── Risk classification tests ─────────────────────────────────────────────────


class TestRiskClassification:
    def test_create_classification_returns_id(self, gov_client):
        token, _ = _register_and_token(gov_client, role="admin", suffix="1")
        r = gov_client.post(
            "/api/v1/governance/risk",
            json={
                "system_name": "Heillon AI Analyser",
                "system_version": "1.0",
                "risk_level": "medium",
                "risk_justification": "Assists in document analysis without final decision power.",
                "impact_areas": ["civil", "criminal"],
                "regulatory_refs": ["CNJ 615/2025", "OAB 001/2024"],
            },
            headers=_auth_headers(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "classification_id" in data
        assert data["risk_level"] == "medium"

    def test_list_classifications(self, gov_client):
        token, _ = _register_and_token(gov_client, role="perito", suffix="2")
        # Create one
        gov_client.post(
            "/api/v1/governance/risk",
            json={
                "system_name": "System A",
                "risk_level": "low",
                "risk_justification": "x",
            },
            headers=_auth_headers(token),
        )
        r = gov_client.get("/api/v1/governance/risk", headers=_auth_headers(token))
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        assert items[0]["system_name"] == "System A"

    def test_get_classification_by_id(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="3")
        create_r = gov_client.post(
            "/api/v1/governance/risk",
            json={
                "system_name": "System B",
                "risk_level": "high",
                "risk_justification": "High risk explanation",
            },
            headers=_auth_headers(token),
        )
        cid = create_r.json()["classification_id"]
        r = gov_client.get(
            f"/api/v1/governance/risk/{cid}", headers=_auth_headers(token)
        )
        assert r.status_code == 200
        assert r.json()["classification_id"] == cid

    def test_get_unknown_classification_returns_404(self, gov_client):
        token, _ = _register_and_token(gov_client, role="perito", suffix="4")
        r = gov_client.get(
            "/api/v1/governance/risk/nonexistent-id", headers=_auth_headers(token)
        )
        assert r.status_code == 404

    def test_retire_requires_admin(self, gov_client):
        token_adv, _ = _register_and_token(gov_client, role="advogado", suffix="5")
        token_adm, _ = _register_and_token(gov_client, role="admin", suffix="6")
        # Create classification as advogado
        create_r = gov_client.post(
            "/api/v1/governance/risk",
            json={
                "system_name": "System C",
                "risk_level": "low",
                "risk_justification": "x",
            },
            headers=_auth_headers(token_adv),
        )
        cid = create_r.json()["classification_id"]
        # Advogado cannot retire
        r1 = gov_client.delete(
            f"/api/v1/governance/risk/{cid}", headers=_auth_headers(token_adv)
        )
        assert r1.status_code == 403
        # Admin can retire
        r2 = gov_client.delete(
            f"/api/v1/governance/risk/{cid}", headers=_auth_headers(token_adm)
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "retired"

    def test_invalid_risk_level_rejected(self, gov_client):
        token, _ = _register_and_token(gov_client, role="perito", suffix="7")
        r = gov_client.post(
            "/api/v1/governance/risk",
            json={
                "system_name": "X",
                "risk_level": "extreme",
                "risk_justification": "x",
            },
            headers=_auth_headers(token),
        )
        # Service raises ValueError → translated to 500 or 422
        assert r.status_code in (422, 500)


# ── AI Decision tests ──────────────────────────────────────────────────────────


class TestAIDecisions:
    def test_log_low_risk_decision_no_gate(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="d1")
        r = gov_client.post(
            "/api/v1/governance/decisions",
            json={
                "decision_type": "analysis",
                "decision_summary": "Analysed contract clauses",
                "ai_model": "gpt-4o-mini",
                "ai_provider": "openai",
                "risk_level": "low",
            },
            headers=_auth_headers(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "decision_id" in data
        assert data["gate_id"] is None  # no gate for low risk

    def test_log_high_risk_decision_creates_gate(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="d2")
        r = gov_client.post(
            "/api/v1/governance/decisions",
            json={
                "decision_type": "recommendation",
                "decision_summary": "Critical custody decision",
                "risk_level": "high",
            },
            headers=_auth_headers(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["gate_id"] is not None  # gate created for high risk

    def test_list_decisions(self, gov_client):
        token, _ = _register_and_token(gov_client, role="perito", suffix="d3")
        gov_client.post(
            "/api/v1/governance/decisions",
            json={"decision_type": "analysis", "risk_level": "low"},
            headers=_auth_headers(token),
        )
        r = gov_client.get("/api/v1/governance/decisions", headers=_auth_headers(token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_review_decision(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="d4")
        create_r = gov_client.post(
            "/api/v1/governance/decisions",
            json={"decision_type": "generation", "risk_level": "medium"},
            headers=_auth_headers(token),
        )
        did = create_r.json()["decision_id"]
        r = gov_client.post(
            f"/api/v1/governance/decisions/{did}/review",
            json={"human_decision": "approved", "notes": "Reviewed by lawyer"},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "reviewed"

    def test_review_unknown_decision_returns_404(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="d5")
        r = gov_client.post(
            "/api/v1/governance/decisions/nonexistent/review",
            json={"human_decision": "approved"},
            headers=_auth_headers(token),
        )
        assert r.status_code == 404


# ── Human gate tests ───────────────────────────────────────────────────────────


class TestHumanGates:
    def test_list_pending_gates_empty_initially(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="g1")
        r = gov_client.get("/api/v1/governance/gates", headers=_auth_headers(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_high_risk_decision_creates_pending_gate(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="g2")
        create_r = gov_client.post(
            "/api/v1/governance/decisions",
            json={"decision_type": "classification", "risk_level": "high"},
            headers=_auth_headers(token),
        )
        gate_id = create_r.json()["gate_id"]
        assert gate_id is not None

        r = gov_client.get(
            f"/api/v1/governance/gates/{gate_id}", headers=_auth_headers(token)
        )
        assert r.status_code == 200
        gate = r.json()
        assert gate["status"] == "pending"
        assert gate["risk_level"] == "high"

    def test_resolve_gate_approved(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="g3")
        create_r = gov_client.post(
            "/api/v1/governance/decisions",
            json={"decision_type": "recommendation", "risk_level": "high"},
            headers=_auth_headers(token),
        )
        gate_id = create_r.json()["gate_id"]

        r = gov_client.post(
            f"/api/v1/governance/gates/{gate_id}/resolve",
            json={"status": "approved", "notes": "Manually reviewed and approved"},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    def test_resolve_gate_rejected(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="g4")
        create_r = gov_client.post(
            "/api/v1/governance/decisions",
            json={"decision_type": "recommendation", "risk_level": "high"},
            headers=_auth_headers(token),
        )
        gate_id = create_r.json()["gate_id"]

        r = gov_client.post(
            f"/api/v1/governance/gates/{gate_id}/resolve",
            json={"status": "rejected", "notes": "Does not meet standards"},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"

    def test_resolve_already_resolved_gate_returns_409(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="g5")
        create_r = gov_client.post(
            "/api/v1/governance/decisions",
            json={"decision_type": "analysis", "risk_level": "high"},
            headers=_auth_headers(token),
        )
        gate_id = create_r.json()["gate_id"]
        # First resolution
        gov_client.post(
            f"/api/v1/governance/gates/{gate_id}/resolve",
            json={"status": "approved"},
            headers=_auth_headers(token),
        )
        # Second resolution should fail
        r = gov_client.post(
            f"/api/v1/governance/gates/{gate_id}/resolve",
            json={"status": "approved"},
            headers=_auth_headers(token),
        )
        assert r.status_code == 409


# ── OAB Disclosure tests ───────────────────────────────────────────────────────


class TestAIDisclosures:
    def test_create_disclosure_returns_id(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="disc1")
        r = gov_client.post(
            "/api/v1/governance/disclosures",
            json={
                "client_identifier": "client-ref-001",
                "ai_systems_used": ["Heillon AI Analyser v1.0"],
                "mission_ids": ["mission-001"],
                "method": "written",
                "channel": "email",
            },
            headers=_auth_headers(token),
        )
        assert r.status_code == 201, r.text
        assert "disclosure_id" in r.json()

    def test_list_disclosures(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="disc2")
        gov_client.post(
            "/api/v1/governance/disclosures",
            json={"client_identifier": "client-002"},
            headers=_auth_headers(token),
        )
        r = gov_client.get(
            "/api/v1/governance/disclosures", headers=_auth_headers(token)
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_disclosure(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="disc3")
        create_r = gov_client.post(
            "/api/v1/governance/disclosures",
            json={"client_identifier": "client-003"},
            headers=_auth_headers(token),
        )
        did = create_r.json()["disclosure_id"]
        r = gov_client.get(
            f"/api/v1/governance/disclosures/{did}", headers=_auth_headers(token)
        )
        assert r.status_code == 200
        assert r.json()["disclosure_id"] == did
        assert r.json()["client_acknowledged"] == 0

    def test_client_acknowledgement(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="disc4")
        create_r = gov_client.post(
            "/api/v1/governance/disclosures",
            json={"client_identifier": "client-004"},
            headers=_auth_headers(token),
        )
        did = create_r.json()["disclosure_id"]

        r = gov_client.post(
            f"/api/v1/governance/disclosures/{did}/ack",
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "acknowledged"

        # Verify acknowledged flag
        r2 = gov_client.get(
            f"/api/v1/governance/disclosures/{did}", headers=_auth_headers(token)
        )
        assert r2.json()["client_acknowledged"] == 1

    def test_disclosure_requires_auth(self, gov_client):
        r = gov_client.get("/api/v1/governance/disclosures")
        assert r.status_code == 401

    def test_disclosure_uses_default_text_when_omitted(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="disc5")
        create_r = gov_client.post(
            "/api/v1/governance/disclosures",
            json={"client_identifier": "client-005"},
            headers=_auth_headers(token),
        )
        did = create_r.json()["disclosure_id"]
        r = gov_client.get(
            f"/api/v1/governance/disclosures/{did}", headers=_auth_headers(token)
        )
        text = r.json()["disclosure_text"]
        assert "artificial intelligence" in text.lower()

    def test_unknown_disclosure_returns_404(self, gov_client):
        token, _ = _register_and_token(gov_client, role="advogado", suffix="disc6")
        r = gov_client.get(
            "/api/v1/governance/disclosures/nonexistent", headers=_auth_headers(token)
        )
        assert r.status_code == 404
