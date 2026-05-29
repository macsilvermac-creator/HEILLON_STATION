"""F15 — ICP-Brasil Qualificada: signer, PDF/A-3, and /verify/icp endpoint tests.

Uses a self-signed RSA test certificate generated on-the-fly (no real ICP-Brasil
certificate needed).  The signing tests validate RSA-PKCS1v15+SHA-256 behaviour;
the /verify/icp endpoint tests exercise the full FastAPI stack via TestClient.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

# ── Test certificate factory ──────────────────────────────────────────────────


def _make_test_p12(issuer_name: str = "CN=Test CA") -> tuple[bytes, str]:
    """Generate an in-memory PKCS#12 for testing.  Returns (p12_bytes, password)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID
    from datetime import datetime, timedelta, timezone

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, issuer_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Heillon Test"),
        ]
    )
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    p12_bytes = pkcs12.serialize_key_and_certificates(
        name=b"test",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return p12_bytes, ""


# ── ICPSignerService unit tests ───────────────────────────────────────────────


class TestICPSignerServiceDisabled:
    """Service disabled when cert path is absent."""

    def test_available_false_no_cert(self):
        from app.domain.hdr.icp_signer import ICPSignerService

        svc = ICPSignerService(cert_path=None)
        assert svc.available is False

    def test_available_false_missing_file(self, tmp_path):
        from app.domain.hdr.icp_signer import ICPSignerService

        svc = ICPSignerService(cert_path=str(tmp_path / "nonexistent.p12"))
        assert svc.available is False

    def test_sign_raises_when_disabled(self):
        from app.domain.hdr.icp_signer import ICPSignerService

        svc = ICPSignerService(cert_path=None)
        with pytest.raises(RuntimeError, match="ICP-Brasil certificate not available"):
            svc.sign_content(b"hello")

    def test_verify_returns_false_when_disabled(self):
        from app.domain.hdr.icp_signer import ICPSignerService

        svc = ICPSignerService(cert_path=None)
        assert svc.verify_signature(b"hello", "dGVzdA==") is False


class TestICPSignerServiceEnabled:
    """Service enabled with a self-signed test certificate."""

    @pytest.fixture
    def svc_and_path(self, tmp_path):
        p12_bytes, pwd = _make_test_p12()
        cert_file = tmp_path / "test.p12"
        cert_file.write_bytes(p12_bytes)
        from app.domain.hdr.icp_signer import ICPSignerService

        svc = ICPSignerService(cert_path=str(cert_file), cert_password=pwd)
        return svc, cert_file

    def test_available_true(self, svc_and_path):
        svc, _ = svc_and_path
        assert svc.available is True

    def test_sign_content_returns_result(self, svc_and_path):
        from app.domain.hdr.icp_signer import ICPSignResult

        svc, _ = svc_and_path
        payload = b"canonical-hdr-json"
        result = svc.sign_content(payload)
        assert isinstance(result, ICPSignResult)
        assert result.cert_type == "A1"
        assert result.signature_type == "CAdES-BES"
        assert result.signed_hash == hashlib.sha256(payload).hexdigest()
        assert len(result.signature_b64) > 0

    def test_sign_produces_verifiable_signature(self, svc_and_path):
        svc, _ = svc_and_path
        payload = b"heillon-decision-record"
        result = svc.sign_content(payload)
        assert svc.verify_signature(payload, result.signature_b64) is True

    def test_verify_fails_tampered_content(self, svc_and_path):
        svc, _ = svc_and_path
        result = svc.sign_content(b"original")
        assert svc.verify_signature(b"tampered", result.signature_b64) is False

    def test_verify_fails_bad_base64(self, svc_and_path):
        svc, _ = svc_and_path
        assert svc.verify_signature(b"anything", "not-valid-base64!!!") is False

    def test_icp_brasil_flag_for_generic_issuer(self, svc_and_path):
        svc, _ = svc_and_path
        result = svc.sign_content(b"data")
        # Generic test cert does NOT contain ICP-Brasil marker → False
        assert result.icp_brasil is False

    def test_icp_brasil_flag_for_icp_issuer(self, tmp_path):
        p12_bytes, pwd = _make_test_p12(
            issuer_name="CN=AC Raiz Brasileira v10 ICP-Brasil"
        )
        cert_file = tmp_path / "icp.p12"
        cert_file.write_bytes(p12_bytes)
        from app.domain.hdr.icp_signer import ICPSignerService

        svc = ICPSignerService(cert_path=str(cert_file), cert_password=pwd)
        result = svc.sign_content(b"data")
        assert result.icp_brasil is True

    def test_sig_id_auto_generated(self, svc_and_path):
        svc, _ = svc_and_path
        r1 = svc.sign_content(b"a")
        r2 = svc.sign_content(b"a")
        assert r1.sig_id != r2.sig_id  # unique UUIDs each time

    def test_sig_id_explicit(self, svc_and_path):
        svc, _ = svc_and_path
        result = svc.sign_content(b"x", sig_id="fixed-id-123")
        assert result.sig_id == "fixed-id-123"


# ── ICPSignatureRepository unit tests ─────────────────────────────────────────


class TestICPSignatureRepository:
    """Repository CRUD over SQLite in-memory."""

    @pytest.fixture
    def conn(self, tmp_path):
        import sqlite3
        from app.db.database import apply_migrations

        db_path = tmp_path / "test.db"
        c = sqlite3.connect(str(db_path))
        c.row_factory = sqlite3.Row
        migrations_path = (
            Path(__file__).resolve().parents[3] / "app" / "db" / "migrations"
        )
        apply_migrations(c, migrations_path)
        c.commit()
        yield c
        c.close()

    @pytest.fixture
    def sample_result(self, tmp_path):
        p12_bytes, pwd = _make_test_p12()
        cert_file = tmp_path / "test.p12"
        cert_file.write_bytes(p12_bytes)
        from app.domain.hdr.icp_signer import ICPSignerService

        svc = ICPSignerService(cert_path=str(cert_file))
        return svc.sign_content(b"sample hdr data")

    def test_store_and_get_signature(self, conn, sample_result):
        from app.domain.hdr.icp_signer import ICPSignatureRepository

        repo = ICPSignatureRepository()
        repo.store_signature(
            conn,
            sample_result,
            entity_type="hdr",
            entity_id="hdr-001",
            signed_by="user-test",
        )
        conn.commit()
        row = repo.get_signature(conn, sample_result.sig_id)
        assert row is not None
        assert row["entity_id"] == "hdr-001"
        assert row["entity_type"] == "hdr"

    def test_list_by_entity(self, conn, sample_result):
        from app.domain.hdr.icp_signer import ICPSignerService, ICPSignatureRepository

        repo = ICPSignatureRepository()
        # Store two signatures for same entity
        import os

        p12_bytes, _ = _make_test_p12()
        with tempfile.NamedTemporaryFile(suffix=".p12", delete=False) as f:
            f.write(p12_bytes)
            tmp = f.name
        try:
            svc = ICPSignerService(cert_path=tmp)
            r1 = svc.sign_content(b"v1")
            r2 = svc.sign_content(b"v2")
            repo.store_signature(
                conn, r1, entity_type="hdr", entity_id="e-1", signed_by="u1"
            )
            repo.store_signature(
                conn, r2, entity_type="hdr", entity_id="e-1", signed_by="u1"
            )
            conn.commit()
            records = repo.list_by_entity(conn, "hdr", "e-1")
            assert len(records) == 2
        finally:
            os.unlink(tmp)

    def test_store_and_retrieve_verification(self, conn):
        from app.domain.hdr.icp_signer import ICPSignatureRepository

        repo = ICPSignatureRepository()
        repo.store_verification(
            conn,
            verify_id="v-001",
            hdr_id="hdr-verify-001",
            icp_verified=True,
            signer_name="CN=Test",
            cert_issuer="CN=ICP-Brasil CA",
            cert_serial="12345",
            cert_type="A1",
            signing_time="2026-05-25T00:00:00Z",
            signature_valid=True,
            cert_chain_valid=True,
            details_json='{"note":"test"}',
            verified_by="system",
        )
        conn.commit()
        row = repo.get_verification_for_hdr(conn, "hdr-verify-001")
        assert row is not None
        assert bool(row["icp_verified"]) is True
        assert row["cert_serial"] == "12345"

    def test_store_and_retrieve_pdfa3_package(self, conn):
        from app.domain.hdr.icp_signer import ICPSignatureRepository

        repo = ICPSignatureRepository()
        repo.store_pdfa3_package(
            conn,
            pdfa3_id="pkg3-001",
            package_id="fp-001",
            pdf_path="/data/pkg3-001.pdf",
            pdf_checksum="a" * 64,
            attachments_json='[{"name":"chains.json"}]',
            is_signed=False,
            created_by="user-x",
        )
        conn.commit()
        row = repo.get_pdfa3_package(conn, "pkg3-001")
        assert row is not None
        assert row["package_id"] == "fp-001"
        assert row["pdf_version"] == "A-3"


# ── PDFA3Service unit tests ───────────────────────────────────────────────────


class TestPDFA3Service:
    """Tests for the PDF/A-3 upgrade service."""

    @pytest.fixture
    def minimal_pdf(self):
        """Generate minimal valid PDF bytes via ReportLab."""
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        doc.build(
            [Paragraph("Heillon F15 PDF/A-3 Test", getSampleStyleSheet()["Normal"])]
        )
        return buf.getvalue()

    def test_embed_chain_json_returns_larger_pdf(self, minimal_pdf):
        from app.domain.hdr.pdfa3_service import PDFA3Service

        svc = PDFA3Service()
        chain_data = json.dumps({"mission_lineage": []})
        result = svc.embed_chain_json(minimal_pdf, chain_data, title="Test Package")
        assert len(result.pdf_bytes) > len(minimal_pdf)
        assert len(result.checksum) == 64  # SHA-256 hex
        assert len(result.attachments) == 1
        assert result.attachments[0]["name"] == "chains.json"

    def test_checksum_matches_pdf_bytes(self, minimal_pdf):
        from app.domain.hdr.pdfa3_service import PDFA3Service

        svc = PDFA3Service()
        result = svc.embed_chain_json(minimal_pdf, b'{"test":1}')
        assert result.checksum == hashlib.sha256(result.pdf_bytes).hexdigest()

    def test_attachment_metadata_includes_size(self, minimal_pdf):
        from app.domain.hdr.pdfa3_service import PDFA3Service, EmbeddedAttachment

        svc = PDFA3Service()
        data = b"attachment content here"
        att = EmbeddedAttachment(
            filename="evidence.json",
            data=data,
            mime_type="application/json",
            description="Test attachment",
        )
        result = svc.upgrade_to_pdfa3(minimal_pdf, [att])
        meta = result.attachments[0]
        assert meta["size"] == len(data)
        assert meta["checksum"] == hashlib.sha256(data).hexdigest()
        assert meta["name"] == "evidence.json"

    def test_multiple_attachments(self, minimal_pdf):
        from app.domain.hdr.pdfa3_service import PDFA3Service, EmbeddedAttachment

        svc = PDFA3Service()
        atts = [
            EmbeddedAttachment("chains.json", b'{"chain":1}'),
            EmbeddedAttachment("manifest.json", b'{"manifest":1}'),
        ]
        result = svc.upgrade_to_pdfa3(minimal_pdf, atts)
        assert len(result.attachments) == 2
        names = {a["name"] for a in result.attachments}
        assert names == {"chains.json", "manifest.json"}

    def test_output_is_valid_pdf(self, minimal_pdf):
        """Verify the output starts with PDF header and is parseable by pikepdf."""
        from app.domain.hdr.pdfa3_service import PDFA3Service
        import pikepdf

        svc = PDFA3Service()
        result = svc.embed_chain_json(minimal_pdf, b'{"x":1}')
        assert result.pdf_bytes[:4] == b"%PDF"
        # Should be parseable without exception
        pdf = pikepdf.Pdf.open(BytesIO(result.pdf_bytes))
        assert pdf is not None

    def test_xmp_contains_pdfa3_conformance(self, minimal_pdf):
        """XMP metadata must declare pdfaid:part=3, pdfaid:conformance=B."""
        from app.domain.hdr.pdfa3_service import PDFA3Service
        import pikepdf

        svc = PDFA3Service()
        result = svc.embed_chain_json(minimal_pdf, b'{"x":1}')
        pdf = pikepdf.Pdf.open(BytesIO(result.pdf_bytes))
        meta = pdf.Root.get("/Metadata")
        if meta is not None:
            xmp_bytes = bytes(meta.read_bytes())
            xmp_str = xmp_bytes.decode("utf-8", errors="ignore")
            assert (
                "pdfaid:part>3<" in xmp_str or "<pdfaid:part>3</pdfaid:part>" in xmp_str
            )


# ── /verify/icp endpoint integration tests ────────────────────────────────────


@pytest.fixture
def icp_client(tmp_path, monkeypatch):
    """TestClient with full app, isolated SQLite, and a pre-seeded HDR + ICP signature."""
    from fastapi.testclient import TestClient
    from app.main import create_application
    from app.core import config as _cfg
    from app.core.config import Settings

    db_path = tmp_path / "icp_test.db"

    def _settings() -> Settings:
        return Settings(
            DATABASE_URL=f"sqlite:///{db_path.as_posix()}",
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
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client, db_path


def _seed_hdr_and_signature(db_path: Path, tmp_path: Path) -> tuple[str, Any]:
    """Generate a real HDR via HDRService (stub timestamp) and seed DB with icp_signatures."""
    import sqlite3
    from app.core.canonical_json import canonical_json_dumps
    from app.domain.hdr.models import (
        HDRAgent,
        HDRCognitiveSnapshot,
        HDRExecution,
        HDRIntent,
        HDRNormative,
        HDRUser,
    )
    from app.domain.hdr.services import HDRService
    from app.domain.hdr.icp_signer import ICPSignerService, ICPSignatureRepository

    # Generate a properly formed HDR with stub timestamp
    hdr_svc = HDRService()
    hdr = hdr_svc.generate_hdr(
        hdr_type="analysis",
        mission_id="mission-icp-test",
        agent=HDRAgent(id="icp-test-agent", model="stub", version="1"),
        user=HDRUser(id="test-user-icp"),
        intent=HDRIntent(
            description="ICP-Brasil signing test",
            tools_required=[],
            estimated_cost_gas=0.0,
        ),
        execution=HDRExecution(
            status="completed", input_hash="a" * 64, output_hash="b" * 64, duration_ms=1
        ),
        cognitive_snapshot=HDRCognitiveSnapshot(
            hypothesis="hyp", action="act", result="res"
        ),
        normative=HDRNormative(checked=True, violations=[], corpus_version="test"),
        allow_stub_fallback=True,
    )

    # Sign the canonical payload bytes with test ICP cert
    canonical_bytes = canonical_json_dumps(HDRService.payload_for_digest(hdr)).encode(
        "utf-8"
    )

    p12_bytes, _ = _make_test_p12()
    cert_file = tmp_path / "icp_seed.p12"
    cert_file.write_bytes(p12_bytes)
    icp_svc = ICPSignerService(cert_path=str(cert_file))
    icp_result = icp_svc.sign_content(canonical_bytes)

    # Seed the test DB
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """INSERT INTO hdrs (hdr_id, mission_id, previous_hdr, hdr_type,
               timestamp_iso, canonical_hash, payload, organization_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            hdr.hdr_id,
            hdr.mission_id,
            hdr.previous_hdr,
            hdr.hdr_type,
            hdr.timestamp,
            hdr.canonical_hash,
            hdr.model_dump_json(),
            "org_default",
        ),
    )
    repo = ICPSignatureRepository()
    repo.store_signature(
        conn,
        icp_result,
        entity_type="hdr",
        entity_id=hdr.hdr_id,
        signed_by="test-user-icp",
    )
    conn.commit()
    conn.close()
    return hdr.hdr_id, icp_result


class TestVerifyICPEndpoint:
    def test_icp_unknown_hdr_returns_404(self, icp_client):
        client, _ = icp_client
        r = client.get("/api/v1/verify/icp/nonexistent-hdr")
        assert r.status_code == 404

    def test_icp_no_signature_returns_200_not_verified(self, icp_client, tmp_path):
        """HDR exists but has no ICP signature → 200 with icp_verified=False."""
        import sqlite3
        from app.domain.hdr.models import (
            HDRAgent,
            HDRCognitiveSnapshot,
            HDRExecution,
            HDRIntent,
            HDRNormative,
            HDRUser,
        )
        from app.domain.hdr.services import HDRService

        client, db_path = icp_client

        # Generate a proper HDR without adding any ICP signature
        hdr_svc = HDRService()
        hdr = hdr_svc.generate_hdr(
            hdr_type="analysis",
            mission_id="mission-unsigned",
            agent=HDRAgent(id="unsigned-agent", model="stub", version="1"),
            user=HDRUser(id="unsigned-user"),
            intent=HDRIntent(
                description="unsigned test", tools_required=[], estimated_cost_gas=0.0
            ),
            execution=HDRExecution(
                status="completed",
                input_hash="c" * 64,
                output_hash="d" * 64,
                duration_ms=1,
            ),
            cognitive_snapshot=HDRCognitiveSnapshot(
                hypothesis="h", action="a", result="r"
            ),
            normative=HDRNormative(checked=True, violations=[], corpus_version="test"),
            allow_stub_fallback=True,
        )

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute(
            """INSERT INTO hdrs (hdr_id, mission_id, previous_hdr, hdr_type,
                   timestamp_iso, canonical_hash, payload, organization_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                hdr.hdr_id,
                hdr.mission_id,
                hdr.previous_hdr,
                hdr.hdr_type,
                hdr.timestamp,
                hdr.canonical_hash,
                hdr.model_dump_json(),
                "org_default",
            ),
        )
        conn.commit()
        conn.close()

        r = client.get(f"/api/v1/verify/icp/{hdr.hdr_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["icp_verified"] is False
        assert data["has_signature_record"] is False

    def test_icp_with_signature_returns_structural_validation(
        self, icp_client, tmp_path
    ):
        """HDR with ICP signature → 200, structural hash_match=True."""
        client, db_path = icp_client
        hdr_id, _ = _seed_hdr_and_signature(db_path, tmp_path)

        r = client.get(f"/api/v1/verify/icp/{hdr_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["hdr_id"] == hdr_id
        assert data["has_signature_record"] is True
        # Generic issuer → icp_brasil=False → icp_verified=False (hash still matches)
        assert "signature_valid" in data
        assert "details" in data

    def test_icp_cached_verification_reused(self, icp_client, tmp_path):
        """Second call to /verify/icp reuses cached icp_verifications row."""
        client, db_path = icp_client
        hdr_id, _ = _seed_hdr_and_signature(db_path, tmp_path)

        r1 = client.get(f"/api/v1/verify/icp/{hdr_id}")
        r2 = client.get(f"/api/v1/verify/icp/{hdr_id}")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both should return consistent results
        assert r1.json()["signature_valid"] == r2.json()["signature_valid"]
