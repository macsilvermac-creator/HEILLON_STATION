"""PDF/A-1/B oriented forensic reports (ReportLab + XMP metadata embedding)."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timezone
from io import BytesIO
from typing import Any, Iterable, Optional

import pikepdf
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core import config as runtime_config
from app.domain.forensic.models import AuditManifest
from app.domain.forensic.pdf_metadata import PDFAMetadata
from app.domain.hdr.models import HDR


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _embed_xmp_metadata(pdf_bytes: bytes, xmp_xml: str) -> bytes:
    """Attach XMP packet as /Metadata stream (PDF 1.4+)."""

    src = BytesIO(pdf_bytes)
    pdf = pikepdf.Pdf.open(src)
    data = xmp_xml.encode("utf-8")
    stream = pikepdf.Stream(pdf, data)
    stream.Type = pikepdf.Name.Metadata
    stream.Subtype = pikepdf.Name.XML
    pdf.Root.Metadata = pdf.make_indirect(stream)
    out = BytesIO()
    pdf.save(out)
    return out.getvalue()


def _safe_text(value: str, max_len: int) -> str:
    chunk = value.replace("\n", " ")
    if len(chunk) > max_len:
        return chunk[: max_len - 1] + "…"
    return chunk


class PDFA1bService:
    """Generate PDF reports oriented toward PDF/A-1/B (XMP, embedded fonts when available)."""

    def __init__(self, font_dir: str | None = None) -> None:
        self.font_dir = font_dir or self._default_font_dir()
        self._register_fonts()

    @staticmethod
    def _default_font_dir() -> str:
        if sys.platform == "win32":
            return os.environ.get("WINDIR", r"C:\Windows") + os.sep + "Fonts"
        return "/usr/share/fonts"

    def _register_fonts(self) -> None:
        """Prefer DejaVu (Linux Docker) or Arial (Windows); fallback to standard Base-14 names."""

        self.font_regular = "Helvetica"
        self.font_bold = "Helvetica-Bold"
        self.font_mono = "Courier"

        dejavu = os.path.join(self.font_dir, "truetype", "dejavu")
        dj_paths = [
            ("DejaVuSans", os.path.join(dejavu, "DejaVuSans.ttf")),
            ("DejaVuSans-Bold", os.path.join(dejavu, "DejaVuSans-Bold.ttf")),
            ("DejaVuSansMono", os.path.join(dejavu, "DejaVuSansMono.ttf")),
        ]
        if os.path.isdir(dejavu) and all(os.path.isfile(p) for _, p in dj_paths):
            try:
                for reg_name, path in dj_paths:
                    pdfmetrics.registerFont(TTFont(reg_name, path))
                self.font_regular, self.font_bold, self.font_mono = dj_paths[0][0], dj_paths[1][0], dj_paths[2][0]
                return
            except OSError:
                pass

        if sys.platform == "win32":
            win = self.font_dir
            trio = [
                ("HeillonArial", os.path.join(win, "arial.ttf")),
                ("HeillonArialBd", os.path.join(win, "arialbd.ttf")),
                ("HeillonCour", os.path.join(win, "cour.ttf")),
            ]
            if all(os.path.isfile(p) for _, p in trio):
                try:
                    for reg_name, path in trio:
                        pdfmetrics.registerFont(TTFont(reg_name, path))
                    self.font_regular, self.font_bold, self.font_mono = trio[0][0], trio[1][0], trio[2][0]
                except OSError:
                    pass

    def generate_executive_report(
        self,
        mission_id: str,
        hdrs: list[HDR],
        manifest: AuditManifest | None,
        signature_info: Optional[dict[str, Any]] = None,
        *,
        generated_by_override: str | None = None,
    ) -> bytes:
        """Render PDF bytes with narrative, tables, and embedded XMP (PDF/A oriented)."""

        settings = runtime_config.get_settings()
        ordered = sorted(hdrs, key=lambda h: h.timestamp)
        tail = ordered[-1].hdr_id if ordered else ""
        root = ordered[0].hdr_id if ordered else ""
        base = (settings.VERIFICATION_PUBLIC_BASE or "").rstrip("/")
        verification_url = f"{base}/api/v1/verify/{tail}" if base else f"/api/v1/verify/{tail}"

        if manifest is not None:
            verification_url = manifest.verification_url

        pkg_id = manifest.package_id if manifest else "—"
        total_hdrs = manifest.total_hdrs if manifest is not None else len(ordered)
        generated_by = (manifest.generated_by if manifest is not None else "") or (generated_by_override or "")

        meta = PDFAMetadata(
            title=f"Heillon Forensic Evidence Report — {mission_id}",
            creator=generated_by or "Heillon Legal Platform",
            subject=f"Mission {mission_id}",
            description="Algorithmic chain of custody (HDR) export with verification references.",
        )

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            title=f"Forensic Evidence Report — {mission_id}",
            author=generated_by or "Heillon Legal Platform",
            subject=f"Chain of Custody Report for Mission {mission_id}",
            creator="Heillon Forensic Package Generator",
        )

        styles = self._create_styles()
        story: list[object] = []

        story.append(Spacer(1, 3 * cm))
        story.append(Paragraph("FORENSIC EVIDENCE REPORT", styles["cover-title"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Chain of Custody — Algorithmic Audit", styles["cover-subtitle"]))
        story.append(Spacer(1, 2 * cm))

        mission_info = [
            [Paragraph("<b>Mission ID:</b>", styles["label"]), Paragraph(mission_id, styles["value-mono"])],
            [Paragraph("<b>Generated by:</b>", styles["label"]), Paragraph(generated_by or "—", styles["value"])],
            [
                Paragraph("<b>Generated at:</b>", styles["label"]),
                Paragraph(datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"), styles["value"]),
            ],
            [Paragraph("<b>Total HDRs:</b>", styles["label"]), Paragraph(str(total_hdrs), styles["value"])],
            [Paragraph("<b>Package ID:</b>", styles["label"]), Paragraph(pkg_id, styles["value-mono"])],
        ]
        info_table = Table(mission_info, colWidths=[4 * cm, 12 * cm])
        info_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor("#1E2D4A")),
                ]
            )
        )
        story.append(info_table)
        story.append(PageBreak())

        story.append(Paragraph("EXECUTIVE SUMMARY", styles["section-title"]))
        story.append(Spacer(1, 0.5 * cm))
        summary_text = (
            f"This document constitutes the forensic evidence package for mission <b>{mission_id}</b>, "
            f"generated by the Heillon Legal Platform. The mission involved analysis of digital evidence "
            f"through a chain of {total_hdrs} algorithmic steps, each cryptographically recorded "
            "as a Heillon Decision Record (HDR) with SHA-256 hashing and RFC 3161 trusted timestamping. "
            "The complete chain of custody is presented below, along with integrity verification instructions."
        )
        story.append(Paragraph(summary_text, styles["body"]))
        story.append(Spacer(1, 1 * cm))

        story.append(Paragraph("KEY FINDINGS", styles["section-title"]))
        story.append(Spacer(1, 0.3 * cm))
        for i, hdr in enumerate(ordered[:12], 1):
            snap = hdr.cognitive_snapshot
            line = (
                f"<b>{i}.</b> {self._escape_html(snap.hypothesis)} → "
                f"{self._escape_html(snap.action)} — {self._escape_html(snap.result)}"
            )
            story.append(Paragraph(line, styles["body"]))
            story.append(Spacer(1, 0.15 * cm))
        if len(ordered) > 12:
            story.append(Paragraph("<i>Further steps omitted for brevity — see JSON annex.</i>", styles["body"]))
        story.append(Spacer(1, 0.8 * cm))

        story.append(Paragraph("CHAIN OF CUSTODY", styles["section-title"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(
            Paragraph(
                "Each row is an HDR (Heillon Decision Record) with an immutable SHA-256 hash.",
                styles["body"],
            )
        )
        story.append(Spacer(1, 0.3 * cm))

        table_data = [["Step", "Timestamp", "Agent", "Action", "HDR ID", "Status"]]
        for i, hdr in enumerate(ordered, 1):
            ts = hdr.timestamp[:19] if len(hdr.timestamp) >= 19 else hdr.timestamp
            table_data.append(
                [
                    str(i),
                    ts,
                    _safe_text(hdr.agent.id, 40),
                    _safe_text(hdr.intent.description, 50),
                    hdr.hdr_id[:12] + "…",
                    hdr.execution.status,
                ]
            )

        table = Table(
            table_data,
            colWidths=[0.8 * cm, 2.2 * cm, 2.2 * cm, 5.2 * cm, 3.3 * cm, 2 * cm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E2D4A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#D4AF37")),
                    ("FONTNAME", (0, 0), (-1, 0), self.font_bold),
                    ("FONTNAME", (0, 1), (-1, -1), self.font_mono),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#2A3F6A")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#0A0F1E"), HexColor("#0F1A2E")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 1 * cm))

        story.append(Paragraph("INTEGRITY VERIFICATION", styles["section-title"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(
            Paragraph(
                "The combined package integrity hash covers both this PDF and the canonical JSON lineage. "
                "To avoid circular updates, the authoritative hash is published in <b>manifest.json</b> "
                "and the forensic API — not embedded as a mutable field inside this PDF body.",
                styles["body"],
            )
        )
        story.append(Spacer(1, 0.4 * cm))

        integrity_info = [
            [
                Paragraph("<b>Verification URL:</b>", styles["label"]),
                Paragraph(self._escape_html(verification_url), styles["value-mono"]),
            ],
            [Paragraph("<b>Chain root:</b>", styles["label"]), Paragraph(root or "—", styles["value-mono"])],
            [Paragraph("<b>Chain tail:</b>", styles["label"]), Paragraph(tail or "—", styles["value-mono"])],
        ]
        integrity_table = Table(integrity_info, colWidths=[5 * cm, 11 * cm])
        integrity_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor("#1E2D4A")),
                ]
            )
        )
        story.append(integrity_table)
        story.append(Spacer(1, 0.5 * cm))
        story.append(
            Paragraph(
                "Use the Verification URL with the Heillon Verification Portal to validate SHA-256 hashes, "
                "RFC 3161 timestamps, and HDR chaining.",
                styles["body"],
            )
        )
        story.append(Spacer(1, 1 * cm))

        if signature_info:
            story.append(Paragraph("DIGITAL SIGNATURE", styles["section-title"]))
            story.append(Spacer(1, 0.5 * cm))
            sig_hex = str(signature_info.get("signature_hex", ""))
            preview = (sig_hex[:64] + "…") if len(sig_hex) > 64 else sig_hex
            signature_data = [
                [
                    Paragraph("<b>Signer:</b>", styles["label"]),
                    Paragraph(str(signature_info.get("signer_name", "Unknown")), styles["value"]),
                ],
                [Paragraph("<b>Algorithm:</b>", styles["label"]), Paragraph("Ed25519", styles["value"])],
                [Paragraph("<b>Signature (hex):</b>", styles["label"]), Paragraph(preview, styles["value-mono"])],
            ]
            sig_table = Table(signature_data, colWidths=[5 * cm, 11 * cm])
            sig_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor("#1E2D4A")),
                    ]
                )
            )
            story.append(sig_table)
            story.append(Spacer(1, 0.5 * cm))
            story.append(
                Paragraph(
                    "Detached manifest signatures ship alongside this dossier; verify using the published public key.",
                    styles["body"],
                )
            )

        story.append(Spacer(1, 2 * cm))
        story.append(
            Paragraph(
                f"© {datetime.now(timezone.utc).year} Heillon Legal Platform. ISO 19005-1 oriented PDF/A-1B export "
                "with embedded XMP metadata.",
                styles["footer"],
            )
        )

        doc.build(story)
        buffer.seek(0)
        raw_pdf = buffer.read()
        return _embed_xmp_metadata(raw_pdf, meta.to_xmp_xml())

    def _create_styles(self) -> dict[str, ParagraphStyle]:
        return {
            "cover-title": ParagraphStyle(
                "cover-title",
                fontName=self.font_bold,
                fontSize=28,
                leading=34,
                alignment=TA_CENTER,
                textColor=HexColor("#D4AF37"),
            ),
            "cover-subtitle": ParagraphStyle(
                "cover-subtitle",
                fontName=self.font_regular,
                fontSize=14,
                leading=20,
                alignment=TA_CENTER,
                textColor=HexColor("#8899AA"),
            ),
            "section-title": ParagraphStyle(
                "section-title",
                fontName=self.font_bold,
                fontSize=16,
                leading=22,
                textColor=HexColor("#D4AF37"),
                spaceAfter=12,
            ),
            "body": ParagraphStyle(
                "body",
                fontName=self.font_regular,
                fontSize=10,
                leading=16,
                alignment=TA_JUSTIFY,
                textColor=HexColor("#CCCCCC"),
            ),
            "label": ParagraphStyle(
                "label",
                fontName=self.font_regular,
                fontSize=10,
                leading=14,
                textColor=HexColor("#8899AA"),
            ),
            "value": ParagraphStyle(
                "value",
                fontName=self.font_regular,
                fontSize=10,
                leading=14,
                textColor=HexColor("#FFFFFF"),
            ),
            "value-mono": ParagraphStyle(
                "value-mono",
                fontName=self.font_mono,
                fontSize=9,
                leading=14,
                textColor=HexColor("#D4AF37"),
            ),
            "footer": ParagraphStyle(
                "footer",
                fontName=self.font_regular,
                fontSize=8,
                leading=12,
                alignment=TA_CENTER,
                textColor=HexColor("#556677"),
            ),
        }

    @staticmethod
    def _escape_html(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )


def render_hdr_lineage_pdf(
    *,
    mission_id: str,
    hdr_sequence: Iterable[HDR],
    generated_by: str,
    emitted_iso: str | None = None,
    manifest: AuditManifest | None = None,
    signature_info: Optional[dict[str, Any]] = None,
) -> bytes:
    """Public entry — same call sites as legacy ReportLab helper."""

    _ = emitted_iso  # emission stamp retained for API compatibility
    svc = PDFA1bService()
    hdrs = list(hdr_sequence)
    return svc.generate_executive_report(
        mission_id,
        hdrs,
        manifest,
        signature_info=signature_info,
        generated_by_override=generated_by,
    )
