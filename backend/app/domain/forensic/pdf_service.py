"""Forensic PDF lineage rendering — PDF/A-1B oriented implementation (XMP + embedded fonts when available)."""

from __future__ import annotations

from app.domain.forensic.pdfa_service import PDFA1bService, render_hdr_lineage_pdf

__all__ = ["PDFA1bService", "render_hdr_lineage_pdf"]
