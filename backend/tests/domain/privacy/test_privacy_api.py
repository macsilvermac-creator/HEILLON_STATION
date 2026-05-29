"""Fase 14 LGPD — Privacy domain HTTP API regressions.

Covers:
- DPO contact (public endpoint, no auth)
- DPO request submission (no auth)
- DPO request admin workflow (admin only)
- Consent CRUD (authenticated user)
- RIPD creation and download
- Security incident registration and workflow
- Access log purge (Marco Civil)
- Data portability export (ZIP)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.core.config import Settings
from app.main import create_application


# ─── fixture ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def privacy_client(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Isolated TestClient with its own SQLite DB for privacy tests."""

    def _settings() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{(tmp_path / 'priv.db').as_posix()}",
            EVIDENCE_DIR=tmp_path / "ev",
            FORENSICS_PACKAGE_DIR=tmp_path / "fp",
            FORCE_STUB_TIMESTAMP=True,
            DPO_NAME="DPO Teste",
            DPO_EMAIL="dpo@teste.heillon.com",
        )

    monkeypatch.setattr(config, "get_settings", _settings)
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
    role: str = "perito",
    suffix_extra: str = "",
    org_id: str = "org_default",
) -> tuple[str, str]:
    """Register a user and return (token, user_id).
    TokenResponse shape: {"access_token": ..., "user": {"user_id": ..., ...}}
    Using org_default so admin can see public DPO requests (which also land in org_default).
    """
    suffix = role[:3] + suffix_extra
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{suffix}@priv.test",
            "name": f"Teste {role}",
            "password": "s3cur3-p@ss-heillon",
            "role": role,
            "organization_id": org_id,
        },
    )
    assert reg.status_code == 200, reg.text
    data = reg.json()
    return data["access_token"], data["user"]["user_id"]


def _admin_headers(client: TestClient, suffix: str = "1") -> dict[str, str]:
    token, _ = _register_and_token(client, role="admin", suffix_extra=suffix)
    return {"Authorization": f"Bearer {token}"}


def _user_headers(client: TestClient, suffix: str = "1") -> dict[str, str]:
    token, _ = _register_and_token(client, role="perito", suffix_extra=suffix)
    return {"Authorization": f"Bearer {token}"}


# ─── DPO Contact ──────────────────────────────────────────────────────────────


def test_dpo_contact_public(privacy_client: TestClient):
    """GET /privacy/dpo-contact must work without authentication."""
    resp = privacy_client.get("/api/v1/privacy/dpo-contact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dpo_email"] == "dpo@teste.heillon.com"
    assert data["dpo_name"] == "DPO Teste"
    assert "privacy_policy_url" in data
    assert "request_form_url" in data


# ─── DPO Request ──────────────────────────────────────────────────────────────


def test_submit_dpo_request_no_auth(privacy_client: TestClient):
    """Data subjects can submit a rights request without authentication."""
    resp = privacy_client.post(
        "/api/v1/privacy/dpo-request",
        json={
            "requester_name": "Maria Silva",
            "requester_email": "maria@test.com",
            "request_type": "access",
            "description": "Quero saber quais dados pessoais estão armazenados sobre mim.",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "pending"
    assert data["request_type"] == "access"
    assert data["due_at"] is not None  # LGPD art. 19 — 15-day deadline set


def test_submit_dpo_request_invalid_email(privacy_client: TestClient):
    resp = privacy_client.post(
        "/api/v1/privacy/dpo-request",
        json={
            "requester_name": "Test",
            "requester_email": "not-an-email",
            "request_type": "deletion",
            "description": "Quero excluir meus dados pessoais da plataforma.",
        },
    )
    assert resp.status_code == 422


def test_list_dpo_requests_requires_admin(privacy_client: TestClient):
    headers = _user_headers(privacy_client, suffix="2")
    resp = privacy_client.get("/api/v1/privacy/dpo-requests", headers=headers)
    assert resp.status_code == 403


def test_admin_can_list_and_update_dpo_request(privacy_client: TestClient):
    # Submit a request first
    privacy_client.post(
        "/api/v1/privacy/dpo-request",
        json={
            "requester_name": "João Pereira",
            "requester_email": "joao@test.com",
            "request_type": "portability",
            "description": "Solicito portabilidade dos meus dados para outro sistema.",
        },
    )

    # List as admin
    headers = _admin_headers(privacy_client, suffix="3")
    list_resp = privacy_client.get("/api/v1/privacy/dpo-requests", headers=headers)
    assert list_resp.status_code == 200
    requests = list_resp.json()
    assert len(requests) >= 1
    request_id = requests[0]["request_id"]

    # Update the request
    upd = privacy_client.put(
        f"/api/v1/privacy/dpo-requests/{request_id}",
        json={"status": "in_progress", "response_notes": "A analisar"},
        headers=headers,
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "in_progress"

    # Complete the request
    done = privacy_client.put(
        f"/api/v1/privacy/dpo-requests/{request_id}",
        json={"status": "completed", "response_notes": "Dados exportados e enviados."},
        headers=headers,
    )
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
    assert done.json()["completed_at"] is not None


# ─── Consent ──────────────────────────────────────────────────────────────────


def test_consent_crud_lifecycle(privacy_client: TestClient):
    headers = _user_headers(privacy_client)

    # Get empty bundle
    bundle = privacy_client.get("/api/v1/privacy/consent", headers=headers)
    assert bundle.status_code == 200
    assert bundle.json()["records"] == []

    # Grant analytics consent
    grant = privacy_client.post(
        "/api/v1/privacy/consent",
        json={"purpose": "analytics", "granted": True},
        headers=headers,
    )
    assert grant.status_code == 200
    assert grant.json()["granted"] is True
    assert grant.json()["purpose"] == "analytics"
    assert grant.json()["granted_at"] is not None

    # Revoke analytics
    revoke = privacy_client.post(
        "/api/v1/privacy/consent",
        json={"purpose": "analytics", "granted": False},
        headers=headers,
    )
    assert revoke.status_code == 200
    assert revoke.json()["granted"] is False
    assert revoke.json()["revoked_at"] is not None

    # Grant marketing
    privacy_client.post(
        "/api/v1/privacy/consent",
        json={"purpose": "marketing", "granted": True},
        headers=headers,
    )

    # Revoke all
    revoke_all = privacy_client.delete("/api/v1/privacy/consent", headers=headers)
    assert revoke_all.status_code == 200
    revoked = revoke_all.json()
    assert all(r["granted"] is False for r in revoked)


# ─── RIPD ─────────────────────────────────────────────────────────────────────


def test_create_and_download_ripd(privacy_client: TestClient):
    headers = _user_headers(privacy_client)

    ripd_payload = {
        "title": "RIPD — Ingestão de Evidências",
        "processing_type": "ingestion",
        "legal_basis": "contract",
        "purpose": "Tratamento de evidências jurídicas submetidas pelo utilizador para custódia criptográfica.",
        "data_categories": [
            "dados de identificação",
            "documentos jurídicos",
            "metadados de ficheiro",
        ],
        "data_lifecycle": "Mínimo 5 anos para valor probatório; eliminação após prazo legal.",
        "recipients": ["Tribunal de Justiça (mediante ordem judicial)"],
        "risks_identified": [
            "Acesso não autorizado a documentos sensíveis",
            "Perda de integridade dos hashes",
        ],
        "safeguards": [
            "Cifra AES-256-GCM em repouso",
            "SHA-256 com timestamp RFC3161",
            "Controle de acesso JWT",
        ],
    }

    # Create
    create = privacy_client.post(
        "/api/v1/privacy/ripd", json=ripd_payload, headers=headers
    )
    assert create.status_code == 201, create.text
    report = create.json()
    assert report["status"] == "draft"
    assert report["processing_type"] == "ingestion"
    assert report["legal_basis"] == "contract"
    ripd_id = report["ripd_id"]

    # Get
    get = privacy_client.get(f"/api/v1/privacy/ripd/{ripd_id}", headers=headers)
    assert get.status_code == 200
    assert get.json()["ripd_id"] == ripd_id

    # List
    lst = privacy_client.get("/api/v1/privacy/ripd", headers=headers)
    assert lst.status_code == 200
    assert any(r["ripd_id"] == ripd_id for r in lst.json())

    # Download PDF
    pdf = privacy_client.get(
        f"/api/v1/privacy/ripd/{ripd_id}/download", headers=headers
    )
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] in (
        "application/pdf",
        "application/pdf; charset=utf-8",
    )
    assert len(pdf.content) > 100  # at minimum a PDF or text payload


# ─── Security Incidents (ANPD Res. 15/2024) ──────────────────────────────────


def test_incident_lifecycle(privacy_client: TestClient):
    admin_h = _admin_headers(privacy_client, suffix="4")
    user_h = _user_headers(privacy_client, suffix="5")

    # Register incident (any authenticated user)
    create = privacy_client.post(
        "/api/v1/security/incident",
        json={
            "category": "data_leak",
            "description": "Registado acesso não autorizado a ficheiros de evidências. IP suspeito identificado nos logs.",
            "severity": "high",
            "affected_subjects_count": 12,
            "affected_data_types": ["documentos jurídicos", "dados de identificação"],
            "potential_harm": "Exposição de documentos em processo judicial em curso.",
            "containment_measures": "IP bloqueado. Sessões encerradas. Tokens revogados.",
        },
        headers=user_h,
    )
    assert create.status_code == 201, create.text
    incident = create.json()
    assert incident["status"] == "detected"
    assert incident["is_overdue_anpd"] is False  # just created, not yet overdue
    assert incident["anpd_notification_due_at"] is not None
    incident_id = incident["incident_id"]

    # List (admin only)
    lst = privacy_client.get("/api/v1/security/incidents", headers=admin_h)
    assert lst.status_code == 200
    assert any(i["incident_id"] == incident_id for i in lst.json())

    # Non-admin cannot list
    lst_fail = privacy_client.get("/api/v1/security/incidents", headers=user_h)
    assert lst_fail.status_code == 403

    # Advance to evaluating
    upd = privacy_client.put(
        f"/api/v1/security/incidents/{incident_id}",
        json={"status": "evaluating"},
        headers=admin_h,
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "evaluating"

    # Mark ANPD notified
    import datetime

    notif_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    anpd_upd = privacy_client.put(
        f"/api/v1/security/incidents/{incident_id}",
        json={
            "status": "anpd_notified",
            "anpd_notified_at": notif_ts,
            "anpd_notification_ref": "ANPD-2026-00001",
        },
        headers=admin_h,
    )
    assert anpd_upd.status_code == 200
    assert anpd_upd.json()["anpd_notified_at"] is not None
    assert anpd_upd.json()["anpd_notification_ref"] == "ANPD-2026-00001"

    # Get ANPD notification draft
    notif = privacy_client.get(
        f"/api/v1/security/incidents/{incident_id}/notification",
        headers=admin_h,
    )
    assert notif.status_code == 200
    draft = notif.json()["anpd_notification_draft"]
    assert "ANPD" in draft
    assert "data_leak" in draft


# ─── Log Purge (Marco Civil) ──────────────────────────────────────────────────


def test_log_purge_admin_only(privacy_client: TestClient):
    user_h = _user_headers(privacy_client, suffix="6")
    admin_h = _admin_headers(privacy_client, suffix="7")

    # Non-admin forbidden
    fail = privacy_client.post("/api/v1/privacy/purge-logs", headers=user_h)
    assert fail.status_code == 403

    # Admin succeeds
    ok = privacy_client.post("/api/v1/privacy/purge-logs", headers=admin_h)
    assert ok.status_code == 200
    result = ok.json()
    assert "purged_count" in result
    assert result["purged_count"] >= 0


# ─── Portability export (LGPD art. 18 V) ─────────────────────────────────────


def test_portability_export_zip(privacy_client: TestClient):
    headers = _user_headers(privacy_client)

    resp = privacy_client.get("/api/v1/privacy/export", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert len(resp.content) > 50  # non-empty ZIP

    import io
    import zipfile

    buf = io.BytesIO(resp.content)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
    assert "profile.json" in names
    assert "consent.json" in names
    assert "README.txt" in names
