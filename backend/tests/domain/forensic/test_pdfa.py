"""PDF/A export regressions (XMP markers + structure)."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

import pytest
from pypdf import PdfReader

from app.domain.forensic.models import AuditManifest
from app.domain.forensic.pdfa_service import PDFA1bService


def _pdf_extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "".join((p.extract_text() or "") for p in reader.pages)


@pytest.fixture()
def pdfa_service() -> PDFA1bService:
    return PDFA1bService()


@pytest.fixture()
def sample_manifest() -> AuditManifest:
    return AuditManifest(
        package_id="fpkg_test123",
        mission_id="test-mission",
        chain_root="a" * 64,
        chain_tail="b" * 64,
        total_hdrs=2,
        generated_at=datetime.now(timezone.utc),
        generated_by="Perito QA",
        integrity_hash="c" * 64,
        verification_url="https://example.com/api/v1/verify/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    )


def test_pdfa_has_xmp_metadata(
    pdfa_service: PDFA1bService,
    hdr_service_fixture,
    sample_agent_stack,
    sample_manifest: AuditManifest,
) -> None:
    hdr_primary = hdr_service_fixture.generate_hdr(
        hdr_type="ocr",
        mission_id="pdfa_suite",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )
    downstream = hdr_service_fixture.generate_hdr(
        hdr_type="analysis",
        mission_id="pdfa_suite",
        previous_hdr=hdr_primary.hdr_id,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )
    pdf_bytes = pdfa_service.generate_executive_report(
        "test-mission",
        [hdr_primary, downstream],
        sample_manifest,
    )
    raw = pdf_bytes.decode("latin-1", errors="ignore").lower()
    assert "xpacket" in raw or "x:xmpmeta" in raw or "pdfaid:part" in raw
    assert "executive summary" in _pdf_extract_text(pdf_bytes).lower()


def test_pdfa_has_pdf_header(
    pdfa_service: PDFA1bService,
    hdr_service_fixture,
    sample_agent_stack,
    sample_manifest: AuditManifest,
) -> None:
    hdr_primary = hdr_service_fixture.generate_hdr(
        hdr_type="ocr",
        mission_id="pdfa_hdr",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )
    pdf_bytes = pdfa_service.generate_executive_report("test-mission", [hdr_primary], sample_manifest)
    assert pdf_bytes[:5] == b"%PDF-"


def test_pdfa_has_required_sections(
    pdfa_service: PDFA1bService,
    hdr_service_fixture,
    sample_agent_stack,
    sample_manifest: AuditManifest,
) -> None:
    hdr_primary = hdr_service_fixture.generate_hdr(
        hdr_type="ocr",
        mission_id="pdfa_sections",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )
    pdf_bytes = pdfa_service.generate_executive_report("test-mission", [hdr_primary], sample_manifest)
    pdf_text = _pdf_extract_text(pdf_bytes)
    assert "EXECUTIVE SUMMARY" in pdf_text
    assert "CHAIN OF CUSTODY" in pdf_text
    assert "INTEGRITY VERIFICATION" in pdf_text


def test_pdfa_with_signature(
    pdfa_service: PDFA1bService,
    hdr_service_fixture,
    sample_agent_stack,
    sample_manifest: AuditManifest,
) -> None:
    hdr_primary = hdr_service_fixture.generate_hdr(
        hdr_type="ocr",
        mission_id="pdfa_sig",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )
    signature_info = {
        "signer_name": "Perito Test",
        "signature_hex": "a" * 128,
        "public_key_pem": "-----BEGIN PUBLIC KEY-----\nTEST\n-----END PUBLIC KEY-----",
    }
    pdf_bytes = pdfa_service.generate_executive_report(
        "test-mission",
        [hdr_primary],
        sample_manifest,
        signature_info=signature_info,
    )
    pdf_text = _pdf_extract_text(pdf_bytes)
    assert "DIGITAL SIGNATURE" in pdf_text
    assert "Ed25519" in pdf_text
