"""Signatures domain tests — universal document signature lifecycle.

Covers:
- Record signature (all jurisdictions: BR / EU / US / UAE)
- Delivery / receipt acknowledgment chain
- List by org, list by document hash
- Revoke (admin only)
- Standards reference endpoint (no auth)
- Hash validation (64 chars required)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config as _cfg
from app.core.config import Settings

_DOC_HASH = "a" * 64


@pytest.fixture()
def sig_client(tmp_path, monkeypatch):
    from app.main import create_application

    def _settings() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'sig.db').as_posix()}",
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
            "email": f"{role}{suffix}@sig.test",
            "name": f"Test {role}",
            "password": "long-secure-pass-sig-test",
            "role": role,
            "organization_id": "org_default",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Standards reference ────────────────────────────────────────────────────────


def test_standards_no_auth(sig_client):
    r = sig_client.get("/api/v1/signatures/standards")
    assert r.status_code == 200
    standards = r.json()
    assert len(standards) == 4
    jurs = {s["jurisdiction"] for s in standards}
    assert {"BR", "EU", "US", "UAE"} == jurs


# ── Record signature ───────────────────────────────────────────────────────────


class TestRecordSignature:
    def test_record_icp_brasil(self, sig_client):
        token = _token(sig_client, "advogado", "s1")
        r = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "laudo-001",
                "document_hash": _DOC_HASH,
                "document_title": "Laudo Pericial",
                "signatory_name": "Dr. João Silva",
                "signatory_email": "joao@oab.com",
                "signatory_role": "perito",
                "jurisdiction": "BR",
                "signature_standard": "ICP-Brasil",
                "signature_level": "QES",
                "certificate_issuer": "AC Certisign RFB G5",
                "action": "signed",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "sig_id" in data
        assert data["jurisdiction"] == "BR"
        assert data["signature_format"] == "CAdES-LTA"  # default for ICP-Brasil

    def test_record_eidas_qes(self, sig_client):
        token = _token(sig_client, "advogado", "s2")
        r = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "contract-eu-001",
                "document_hash": "b" * 64,
                "signatory_name": "Maria García",
                "signatory_email": "maria@firma.eu",
                "jurisdiction": "EU",
                "signature_standard": "eIDAS-QES",
                "signature_level": "QES",
                "action": "signed",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["signature_format"] == "PAdES-LTA"  # default for eIDAS
        assert "EU AI Act" in data["legal_value"] or "eIDAS" in data["legal_value"]

    def test_record_esign_us(self, sig_client):
        token = _token(sig_client, "advogado", "s3")
        r = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "settlement-us-001",
                "document_hash": "c" * 64,
                "signatory_name": "John Doe",
                "signatory_email": "john@lawfirm.com",
                "jurisdiction": "US",
                "signature_standard": "ESIGN",
                "signature_level": "advanced",
                "action": "signed",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["jurisdiction"] == "US"

    def test_record_uae_pass(self, sig_client):
        token = _token(sig_client, "advogado", "s4")
        r = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "power-of-attorney-ae-001",
                "document_hash": "d" * 64,
                "signatory_name": "Ahmed Al-Mansouri",
                "signatory_email": "ahmed@difc.ae",
                "jurisdiction": "UAE",
                "signature_standard": "UAE-PASS",
                "signature_level": "QES",
                "action": "signed",
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert "sig_id" in r.json()

    def test_invalid_hash_returns_422(self, sig_client):
        token = _token(sig_client, "advogado", "s5")
        r = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "doc-001",
                "document_hash": "short",
                "signatory_name": "X",
                "signatory_email": "x@x.com",
            },
            headers=_auth(token),
        )
        assert r.status_code == 422

    def test_invalid_jurisdiction_returns_422(self, sig_client):
        token = _token(sig_client, "advogado", "s6")
        r = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "doc-002",
                "document_hash": "e" * 64,
                "signatory_name": "X",
                "signatory_email": "x@x.com",
                "jurisdiction": "MARS",
            },
            headers=_auth(token),
        )
        assert r.status_code == 422


# ── Acknowledgment chain ───────────────────────────────────────────────────────


class TestAcknowledgmentChain:
    def test_sent_delivered_signed_chain(self, sig_client):
        token = _token(sig_client, "advogado", "ack1")

        # 1. Record send
        r_send = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "petition-001",
                "document_hash": "f" * 64,
                "signatory_name": "Dr. Advogado",
                "signatory_email": "adv@firma.com",
                "jurisdiction": "BR",
                "signature_standard": "ICP-Brasil",
                "action": "sent",
            },
            headers=_auth(token),
        )
        assert r_send.status_code == 201
        sig_id = r_send.json()["sig_id"]

        # 2. Acknowledge delivery
        r_ack = sig_client.post(
            f"/api/v1/signatures/{sig_id}/acknowledge",
            json={
                "acknowledged_name": "Tribunal SP",
                "acknowledged_email": "tribu@tjsp.jus.br",
                "action": "received",
                "notes": "Petição recebida às 14h30",
            },
            headers=_auth(token),
        )
        assert r_ack.status_code == 201
        ack_data = r_ack.json()
        assert "ack_id" in ack_data
        assert len(ack_data["ack_hash"]) == 64  # SHA-256 hex

        # 3. List acks
        r_list = sig_client.get(
            f"/api/v1/signatures/{sig_id}/acks",
            headers=_auth(token),
        )
        assert r_list.status_code == 200
        acks = r_list.json()
        assert len(acks) == 1
        assert acks[0]["action"] == "received"

    def test_countersigned_ack(self, sig_client):
        token = _token(sig_client, "advogado", "ack2")
        r = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "contract-002",
                "document_hash": "9" * 64,
                "signatory_name": "Part A",
                "signatory_email": "a@a.com",
                "jurisdiction": "EU",
                "signature_standard": "eIDAS-QES",
                "action": "signed",
            },
            headers=_auth(token),
        )
        sig_id = r.json()["sig_id"]
        r_ack = sig_client.post(
            f"/api/v1/signatures/{sig_id}/acknowledge",
            json={
                "acknowledged_name": "Part B",
                "action": "countersigned",
            },
            headers=_auth(token),
        )
        assert r_ack.status_code == 201
        assert r_ack.json()["action"] == "countersigned"


# ── List / Get ─────────────────────────────────────────────────────────────────


class TestListGet:
    def test_list_signatures(self, sig_client):
        token = _token(sig_client, "advogado", "lst1")
        for i in range(3):
            sig_client.post(
                "/api/v1/signatures",
                json={
                    "document_ref": f"doc-{i}",
                    "document_hash": str(i) * 64,
                    "signatory_name": "Signer",
                    "signatory_email": "s@s.com",
                    "jurisdiction": "BR",
                    "signature_standard": "ICP-Brasil",
                },
                headers=_auth(token),
            )
        r = sig_client.get("/api/v1/signatures", headers=_auth(token))
        assert r.status_code == 200
        assert len(r.json()) >= 3

    def test_filter_by_jurisdiction(self, sig_client):
        token = _token(sig_client, "advogado", "lst2")
        sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "eu-doc",
                "document_hash": "1" * 64,
                "signatory_name": "EU Signer",
                "signatory_email": "eu@eu.com",
                "jurisdiction": "EU",
                "signature_standard": "eIDAS-QES",
            },
            headers=_auth(token),
        )
        r = sig_client.get(
            "/api/v1/signatures?jurisdiction=EU",
            headers=_auth(token),
        )
        assert r.status_code == 200
        items = r.json()
        assert all(i["jurisdiction"] == "EU" for i in items)

    def test_list_by_document_hash(self, sig_client):
        token = _token(sig_client, "advogado", "lst3")
        doc_hash = "2" * 64
        sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "multi-sig-doc",
                "document_hash": doc_hash,
                "signatory_name": "Signer 1",
                "signatory_email": "s1@s.com",
                "jurisdiction": "BR",
                "signature_standard": "ICP-Brasil",
            },
            headers=_auth(token),
        )
        r = sig_client.get(
            f"/api/v1/signatures/document/{doc_hash}",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_signature(self, sig_client):
        token = _token(sig_client, "advogado", "lst4")
        r_create = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "get-test",
                "document_hash": "3" * 64,
                "signatory_name": "Signer",
                "signatory_email": "s@s.com",
                "jurisdiction": "US",
                "signature_standard": "ESIGN",
            },
            headers=_auth(token),
        )
        sig_id = r_create.json()["sig_id"]
        r = sig_client.get(f"/api/v1/signatures/{sig_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["sig_id"] == sig_id

    def test_unknown_returns_404(self, sig_client):
        token = _token(sig_client, "advogado", "lst5")
        r = sig_client.get("/api/v1/signatures/nonexistent", headers=_auth(token))
        assert r.status_code == 404


# ── Revoke (admin) ─────────────────────────────────────────────────────────────


class TestRevoke:
    def test_revoke_requires_admin(self, sig_client):
        token_adv = _token(sig_client, "advogado", "rev1")
        token_adm = _token(sig_client, "admin", "rev2")

        r_create = sig_client.post(
            "/api/v1/signatures",
            json={
                "document_ref": "revoke-test",
                "document_hash": "4" * 64,
                "signatory_name": "Signer",
                "signatory_email": "s@s.com",
                "jurisdiction": "BR",
                "signature_standard": "ICP-Brasil",
            },
            headers=_auth(token_adv),
        )
        sig_id = r_create.json()["sig_id"]

        # Non-admin cannot revoke
        r1 = sig_client.post(
            f"/api/v1/signatures/{sig_id}/revoke",
            headers=_auth(token_adv),
        )
        assert r1.status_code == 403

        # Admin can revoke
        r2 = sig_client.post(
            f"/api/v1/signatures/{sig_id}/revoke",
            headers=_auth(token_adm),
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "revoked"

    def test_unauthenticated_denied(self, sig_client):
        r = sig_client.get("/api/v1/signatures")
        assert r.status_code == 401
