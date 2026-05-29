"""XMP metadata helpers for PDF/A-1/B (ISO 19005-1) oriented exports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def _utc_iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (
        dt.astimezone(timezone.utc)
        .replace(microsecond=0)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


class PDFAMetadata:
    """XMP Metadata for PDF/A-1/B compliance (embedded as Metadata stream)."""

    def __init__(
        self,
        title: str,
        creator: str,
        subject: str = "",
        description: str = "",
        publisher: str = "Heillon Legal Platform",
        creation_date: Optional[datetime] = None,
    ) -> None:
        self.title = title
        self.creator = creator
        self.subject = subject
        self.description = description
        self.publisher = publisher
        self.creation_date = creation_date or datetime.now(timezone.utc)

    def to_xmp_xml(self) -> str:
        """Generate XMP metadata XML for embedding in PDF/A."""

        created = _utc_iso_z(self.creation_date)
        modified = _utc_iso_z(datetime.now(timezone.utc))

        subject_block = ""
        if self.subject.strip():
            subject_block = (
                f"<dc:subject>{self._escape_xml(self.subject)}</dc:subject>\n      "
            )

        return f"""<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Heillon PDF/A Generator">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:xmp="http://ns.adobe.com/xap/1.0/"
      xmlns:pdf="http://ns.adobe.com/pdf/1.3/"
      xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">
      <!-- Dublin Core -->
      <dc:title>{self._escape_xml(self.title)}</dc:title>
      <dc:creator>{self._escape_xml(self.creator)}</dc:creator>
      {subject_block}<dc:description>{self._escape_xml(self.description)}</dc:description>
      <dc:publisher>{self._escape_xml(self.publisher)}</dc:publisher>
      <!-- XMP -->
      <xmp:CreateDate>{created}</xmp:CreateDate>
      <xmp:ModifyDate>{modified}</xmp:ModifyDate>
      <xmp:CreatorTool>Heillon Forensic Package Generator v1.0</xmp:CreatorTool>
      <!-- PDF -->
      <pdf:Producer>Heillon Legal Platform</pdf:Producer>
      <pdf:Keywords>forensic evidence, chain of custody, HDR, legal</pdf:Keywords>
      <!-- PDF/A -->
      <pdfaid:part>1</pdfaid:part>
      <pdfaid:conformance>B</pdfaid:conformance>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""

    @staticmethod
    def _escape_xml(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
