"""Text extraction from evidence files (PDF, DOCX, plain text).

Supports:
- PDF  → PyMuPDF (fitz) with pypdf fallback
- DOCX → python-docx
- TXT/CSV/MD → raw UTF-8 decode
- All others → empty string (binary files are still hashed normally)
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)

_MAX_CHARS = 32_000  # keep HDR cognitive snapshot manageable


def extract_text(filename: str, raw_bytes: bytes) -> str:
    """Return up to _MAX_CHARS of plain text from *raw_bytes*.

    Never raises — extraction failures return an empty string so ingestion
    continues even when a document parser is missing or the file is corrupt.
    """

    name_lower = (filename or "").lower()

    if name_lower.endswith(".pdf"):
        return _extract_pdf(raw_bytes)
    if name_lower.endswith(".docx"):
        return _extract_docx(raw_bytes)
    if any(
        name_lower.endswith(ext)
        for ext in (".txt", ".md", ".csv", ".log", ".json", ".xml")
    ):
        return _extract_plain(raw_bytes)

    return ""


def _extract_pdf(raw_bytes: bytes) -> str:
    try:
        import fitz  # PyMuPDF

        with fitz.open(stream=raw_bytes, filetype="pdf") as doc:
            parts: list[str] = []
            total = 0
            for page in doc:
                text = page.get_text()
                parts.append(text)
                total += len(text)
                if total >= _MAX_CHARS:
                    break
        return "\n".join(parts)[:_MAX_CHARS]
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("PyMuPDF extraction failed: %s", exc)

    # pypdf fallback
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw_bytes))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
            if sum(len(p) for p in parts) >= _MAX_CHARS:
                break
        return "\n".join(parts)[:_MAX_CHARS]
    except Exception as exc:
        logger.warning("pypdf extraction failed: %s", exc)

    return ""


def _extract_docx(raw_bytes: bytes) -> str:
    try:
        from docx import Document

        doc = Document(io.BytesIO(raw_bytes))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(parts)[:_MAX_CHARS]
    except Exception as exc:
        logger.warning("python-docx extraction failed: %s", exc)
    return ""


def _extract_plain(raw_bytes: bytes) -> str:
    try:
        return raw_bytes.decode("utf-8", errors="replace")[:_MAX_CHARS]
    except Exception:
        return ""
