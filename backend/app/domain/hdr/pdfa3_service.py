"""PDF/A-3 document service — embeds cryptographic chain attachments.

ISO 19005-3 (PDF/A-3) extends PDF/A-2 by allowing embedded file attachments
with an explicit Associated Files (AF) relationship.  This makes the forensic
package self-contained as a legal artefact: the ``chains.json`` chain evidence
is physically embedded inside the PDF/A-3 envelope, conforming to
ETSI EN 319 100 and ICP-Brasil qualified signature requirements.

Key differences from PDF/A-1B:
- ``pdfaid:part = 3``, ``pdfaid:conformance = B`` in XMP
- Embedded files via ``/EmbeddedFiles`` Names tree + ``/AF`` array in catalog
- Each embedded file carries an ``AFRelationship`` key (``/Data``)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

_LOG = logging.getLogger(__name__)

try:
    import pikepdf

    _PIKEPDF_OK = True
except ImportError:  # pragma: no cover
    _PIKEPDF_OK = False


# ── XMP template ──────────────────────────────────────────────────────────────

_PDFA3_XMP_TEMPLATE = """\
<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Heillon Legal F15">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:dc="http://purl.org/dc/elements/1.1/">
      <pdfaid:part>3</pdfaid:part>
      <pdfaid:conformance>B</pdfaid:conformance>
      <xmp:CreatorTool>Heillon Legal Platform — ICP-Brasil F15</xmp:CreatorTool>
      <xmp:CreateDate>{create_date}</xmp:CreateDate>
      <xmp:ModifyDate>{modify_date}</xmp:ModifyDate>
      <dc:title>
        <rdf:Alt><rdf:li xml:lang="x-default">{title}</rdf:li></rdf:Alt>
      </dc:title>
      <dc:creator>
        <rdf:Seq><rdf:li>{creator}</rdf:li></rdf:Seq>
      </dc:creator>
      <dc:description>
        <rdf:Alt><rdf:li xml:lang="x-default">{description}</rdf:li></rdf:Alt>
      </dc:description>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="r"?>
"""


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class EmbeddedAttachment:
    """A file to embed inside the PDF/A-3 envelope."""

    filename: str
    data: bytes
    mime_type: str = "application/json"
    description: str = ""


@dataclass
class PDFA3Result:
    """Outcome of a PDF/A-3 upgrade operation."""

    pdf_bytes: bytes
    checksum: str  # SHA-256 hex of the resulting PDF
    attachments: list[dict[str, Any]] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _iso_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _pdf_date(iso: str) -> str:
    """Convert ``2026-05-25T12:00:00Z`` → ``D:20260525120000Z``."""
    clean = iso.replace("-", "").replace(":", "").replace("T", "").replace("Z", "")[:14]
    return f"D:{clean}Z"


def _escape_xmp(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ── Service ───────────────────────────────────────────────────────────────────


class PDFA3Service:
    """Upgrade a PDF/A-1B document to PDF/A-3 with embedded file attachments.

    Primary use-case: take a forensic executive report (PDF/A-1B) and embed
    the cryptographic ``chains.json`` as a ``/Data`` AF attachment, producing
    a legally self-contained PDF/A-3 package.
    """

    def upgrade_to_pdfa3(
        self,
        source_pdf: bytes,
        attachments: list[EmbeddedAttachment],
        *,
        title: str = "Heillon Forensic Package",
        creator: str = "Heillon Legal Platform",
        description: str = "ICP-Brasil PDF/A-3 with embedded chain evidence",
    ) -> PDFA3Result:
        """Embed *attachments* into *source_pdf* and upgrade XMP to PDF/A-3.

        Args:
            source_pdf: Raw PDF bytes (ideally PDF/A-1B or compatible).
            attachments: Files to embed with ``/Data`` AF relationship.
            title: Document title for XMP metadata.
            creator: Creator string for XMP metadata.
            description: Document description for XMP metadata.

        Returns:
            :class:`PDFA3Result` with PDF bytes and SHA-256 checksum.

        Raises:
            RuntimeError: When pikepdf is not installed.
        """
        if not _PIKEPDF_OK:
            raise RuntimeError(
                "pikepdf is required for PDF/A-3 generation. "
                "Install it via: pip install pikepdf"
            )

        now_iso = _iso_now()
        pdf = pikepdf.Pdf.open(BytesIO(source_pdf))

        af_refs: list[Any] = []
        filespec_pairs: list[Any] = []  # flat [name, filespec, …] for Names tree
        attach_meta: list[dict[str, Any]] = []

        for att in attachments:
            att_checksum = hashlib.sha256(att.data).hexdigest()
            checksum_bytes = bytes.fromhex(att_checksum)

            # ── EmbeddedFile stream ──
            ef_stream = pikepdf.Stream(pdf, att.data)
            ef_stream["/Type"] = pikepdf.Name("/EmbeddedFile")
            # Encode mime_type for PDF Name: replace "/" with "#2F"
            safe_mime = att.mime_type.replace("/", "#2F")
            ef_stream["/Subtype"] = pikepdf.Name(f"/{safe_mime}")
            ef_stream["/Params"] = pikepdf.Dictionary(
                Size=len(att.data),
                CheckSum=pikepdf.String(checksum_bytes),
                ModDate=pikepdf.String(_pdf_date(now_iso)),
                CreationDate=pikepdf.String(_pdf_date(now_iso)),
            )
            ef_ref = pdf.make_indirect(ef_stream)

            # ── Filespec dictionary ──
            file_spec = pikepdf.Dictionary(
                Type=pikepdf.Name("/Filespec"),
                F=pikepdf.String(att.filename),
                UF=pikepdf.String(att.filename),
                Desc=pikepdf.String(att.description or att.filename),
                EF=pikepdf.Dictionary(F=ef_ref, UF=ef_ref),
                AFRelationship=pikepdf.Name("/Data"),
            )
            fs_ref = pdf.make_indirect(file_spec)
            af_refs.append(fs_ref)
            filespec_pairs.extend([pikepdf.String(att.filename), fs_ref])

            attach_meta.append(
                {
                    "name": att.filename,
                    "description": att.description,
                    "checksum": att_checksum,
                    "size": len(att.data),
                    "mime_type": att.mime_type,
                }
            )

        # ── Attach to document catalog ──
        # /AF array
        pdf.Root["/AF"] = pikepdf.Array(af_refs)

        # /Names/EmbeddedFiles Names tree
        existing_names = pdf.Root.get("/Names")
        if existing_names is None or not isinstance(existing_names, pikepdf.Dictionary):
            names_dict = pikepdf.Dictionary()
        else:
            names_dict = existing_names
        names_dict["/EmbeddedFiles"] = pikepdf.Dictionary(
            Names=pikepdf.Array(filespec_pairs)
        )
        pdf.Root["/Names"] = names_dict

        # ── Upgrade XMP to PDF/A-3 ──
        xmp_xml = _PDFA3_XMP_TEMPLATE.format(
            create_date=now_iso,
            modify_date=now_iso,
            title=_escape_xmp(title),
            creator=_escape_xmp(creator),
            description=_escape_xmp(description),
        )
        xmp_bytes = xmp_xml.encode("utf-8")
        xmp_stream = pikepdf.Stream(pdf, xmp_bytes)
        xmp_stream["/Type"] = pikepdf.Name("/Metadata")
        xmp_stream["/Subtype"] = pikepdf.Name("/XML")
        pdf.Root["/Metadata"] = pdf.make_indirect(xmp_stream)

        # ── Serialise ──
        out = BytesIO()
        pdf.save(out)
        pdf_bytes = out.getvalue()
        checksum = hashlib.sha256(pdf_bytes).hexdigest()

        _LOG.info(
            "PDF/A-3 upgrade complete — %d attachment(s), checksum=%s…",
            len(attachments),
            checksum[:16],
        )
        return PDFA3Result(
            pdf_bytes=pdf_bytes, checksum=checksum, attachments=attach_meta
        )

    def embed_chain_json(
        self,
        source_pdf: bytes,
        chain_json: str | bytes,
        *,
        title: str = "Heillon Forensic Package",
        creator: str = "Heillon Legal Platform",
    ) -> PDFA3Result:
        """Convenience wrapper: embed a single ``chains.json`` attachment.

        Args:
            source_pdf: Source PDF bytes to upgrade.
            chain_json: Serialised JSON chain (str or bytes).
            title: Document title for XMP.
            creator: Creator string for XMP.
        """
        chain_bytes = (
            chain_json.encode("utf-8") if isinstance(chain_json, str) else chain_json
        )
        att = EmbeddedAttachment(
            filename="chains.json",
            data=chain_bytes,
            mime_type="application/json",
            description="HDR Cryptographic Chain — ICP-Brasil Evidence",
        )
        return self.upgrade_to_pdfa3(
            source_pdf,
            [att],
            title=title,
            creator=creator,
            description="PDF/A-3 forensic package with embedded ICP-Brasil chain evidence",
        )
