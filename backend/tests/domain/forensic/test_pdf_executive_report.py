"""PDF executive dossier regressions."""

from __future__ import annotations

from app.domain.forensic.pdf_service import render_hdr_lineage_pdf


def test_pdf_lineage_starts_with_magic_bytes(hdr_service_fixture, sample_agent_stack):
    svc = hdr_service_fixture
    hdr_primary = svc.generate_hdr(
        hdr_type="ocr",
        mission_id="pdf_suite",
        previous_hdr=None,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )
    downstream = svc.generate_hdr(
        hdr_type="analysis",
        mission_id="pdf_suite",
        previous_hdr=hdr_primary.hdr_id,
        allow_stub_fallback=True,
        **sample_agent_stack,
    )

    bundle = render_hdr_lineage_pdf(
        mission_id="pdf_suite",
        hdr_sequence=[hdr_primary, downstream],
        generated_by="perito_pdf_qa",
    )

    assert bundle.startswith(b"%PDF")
