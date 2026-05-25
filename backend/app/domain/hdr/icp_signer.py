"""ICP-Brasil A1/A3 qualified signature service — CAdES-BES / PAdES-BES.

Soft-certificate (A1) signing via PKCS#12 file (RSA-PKCS1v15 + SHA-256).
When ``ICP_CERT_PATH`` is not configured, :attr:`ICPSignerService.available`
returns ``False`` and signing raises ``RuntimeError`` — callers must guard
before invoking :meth:`sign_content`.

Certificate chain legitimacy is established heuristically by checking
known ICP-Brasil CA name substrings in the issuer DN.  Full PKI trust
validation (root bundle + OCSP/CRL) is out-of-scope for MVP and will be
introduced in a future hardening phase.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)

# ICP-Brasil issuer heuristic markers (case-insensitive substring match)
_ICP_ISSUER_MARKERS: frozenset[str] = frozenset(
    {
        "icp-brasil",
        "serasa",
        "certisign",
        "serpro",
        "ac raiz",
        "ac-raiz",
        "rfb",
        "valid",
        "safeweb",
        "soluti",
        "digitalsign",
    }
)

try:
    from cryptography.hazmat.primitives import hashes as _hashes
    from cryptography.hazmat.primitives import serialization as _serialization
    from cryptography.hazmat.primitives.asymmetric import padding as _asym_padding
    from cryptography.hazmat.primitives.serialization import pkcs12 as _pkcs12

    _CRYPTO_OK = True
except ImportError:  # pragma: no cover
    _CRYPTO_OK = False


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class ICPSignResult:
    """Outcome of an ICP-Brasil signing operation."""

    sig_id: str
    cert_subject: str
    cert_issuer: str
    cert_serial: str
    cert_not_before: str
    cert_not_after: str
    cert_type: str       # 'A1' | 'A3'
    icp_brasil: bool     # True when issuer matches known ICP-Brasil CAs
    signature_type: str  # 'CAdES-BES' | 'PAdES-BES'
    signature_b64: str   # Base64-encoded RSA-SHA256 signature bytes
    signed_hash: str     # SHA-256 hex of the signed content


# ── Signer ─────────────────────────────────────────────────────────────────────


class ICPSignerService:
    """Soft-certificate (A1) ICP-Brasil signing service.

    Loads a PKCS#12 file from *cert_path* protected by *cert_password*.
    If the path is absent or the crypto library is unavailable the service
    is *disabled* — check :attr:`available` before calling :meth:`sign_content`.
    """

    def __init__(
        self,
        *,
        cert_path: str | None = None,
        cert_password: str = "",
    ) -> None:
        self._cert_path = cert_path
        self._cert_password = cert_password
        self._private_key: Any = None
        self._certificate: Any = None
        self._loaded: bool = False

    # ── Internal load ──────────────────────────────────────────────────────────

    def _load(self) -> bool:
        """Load PKCS#12 lazily; returns True when private key is ready."""
        if self._loaded:
            return self._private_key is not None

        self._loaded = True

        if not _CRYPTO_OK:
            _LOG.warning("cryptography package unavailable — ICP signing disabled.")
            return False

        if not self._cert_path:
            _LOG.info("ICP_CERT_PATH not configured — ICP signing disabled.")
            return False

        path = Path(self._cert_path)
        if not path.is_file():
            _LOG.warning("ICP certificate file not found: %s", self._cert_path)
            return False

        try:
            data = path.read_bytes()
            pwd = self._cert_password.encode("utf-8") if self._cert_password else None
            key, cert, _chain = _pkcs12.load_key_and_certificates(data, pwd)
            self._private_key = key
            self._certificate = cert
            _LOG.info(
                "ICP-Brasil A1 certificate loaded — subject: %s",
                cert.subject.rfc4514_string(),
            )
            return True
        except Exception as exc:  # noqa: BLE001
            _LOG.error(
                "Failed to load ICP-Brasil PKCS#12 from '%s': %s", self._cert_path, exc
            )
            return False

    # ── Certificate metadata helpers ──────────────────────────────────────────

    def _cert_info(self) -> dict[str, str]:
        cert = self._certificate
        try:
            nb = cert.not_valid_before_utc.isoformat().replace("+00:00", "Z")
            na = cert.not_valid_after_utc.isoformat().replace("+00:00", "Z")
        except AttributeError:
            # cryptography < 42 — naive datetimes in UTC
            from datetime import timezone

            nb = cert.not_valid_before.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            na = cert.not_valid_after.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        return {
            "subject": cert.subject.rfc4514_string(),
            "issuer": cert.issuer.rfc4514_string(),
            "serial": str(cert.serial_number),
            "not_before": nb,
            "not_after": na,
        }

    def _is_icp_brasil(self) -> bool:
        """Heuristic: True when issuer DN contains a known ICP-Brasil CA substring."""
        if self._certificate is None:
            return False
        issuer = self._certificate.issuer.rfc4514_string().lower()
        return any(m in issuer for m in _ICP_ISSUER_MARKERS)

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """True when a valid A1 certificate is loaded and ready for signing."""
        return self._load()

    def sign_content(
        self,
        content: bytes,
        *,
        sig_id: str | None = None,
        signature_type: str = "CAdES-BES",
    ) -> ICPSignResult:
        """Sign *content* with the loaded A1 certificate (RSA-PKCS1v15 + SHA-256).

        Args:
            content: Raw bytes to sign (document hash or canonical JSON payload).
            sig_id: Optional pre-assigned signature UUID; generated if omitted.
            signature_type: Label for the signature format (``CAdES-BES`` or ``PAdES-BES``).

        Returns:
            :class:`ICPSignResult` with all certificate metadata and Base64 signature.

        Raises:
            RuntimeError: When :attr:`available` is ``False``.
        """
        if not self._load():
            raise RuntimeError(
                "ICP-Brasil certificate not available. "
                "Configure ICP_CERT_PATH and ICP_CERT_PASSWORD environment variables."
            )

        content_hash = hashlib.sha256(content).hexdigest()
        sig_bytes = self._private_key.sign(
            content,
            _asym_padding.PKCS1v15(),
            _hashes.SHA256(),
        )
        sig_b64 = base64.b64encode(sig_bytes).decode("ascii")
        info = self._cert_info()

        return ICPSignResult(
            sig_id=sig_id or str(uuid.uuid4()),
            cert_subject=info["subject"],
            cert_issuer=info["issuer"],
            cert_serial=info["serial"],
            cert_not_before=info["not_before"],
            cert_not_after=info["not_after"],
            cert_type="A1",
            icp_brasil=self._is_icp_brasil(),
            signature_type=signature_type,
            signature_b64=sig_b64,
            signed_hash=content_hash,
        )

    def verify_signature(self, content: bytes, sig_b64: str) -> bool:
        """Verify *sig_b64* against *content* using the certificate's public key.

        Returns ``False`` on any failure (unavailable cert, bad encoding, invalid sig).
        """
        if not self._load():
            return False
        try:
            sig_bytes = base64.b64decode(sig_b64.encode("ascii"), validate=True)
            public_key = self._certificate.public_key()
            public_key.verify(
                sig_bytes,
                content,
                _asym_padding.PKCS1v15(),
                _hashes.SHA256(),
            )
            return True
        except Exception:  # noqa: BLE001
            return False


# ── Repository ─────────────────────────────────────────────────────────────────


class ICPSignatureRepository:
    """CRUD for ``icp_signatures``, ``icp_verifications``, and ``pdfa3_packages`` tables."""

    # ── icp_signatures ─────────────────────────────────────────────────────────

    def store_signature(
        self,
        conn: Any,
        result: ICPSignResult,
        *,
        entity_type: str,
        entity_id: str,
        organization_id: str = "org_default",
        signed_by: str,
        tsa_token_b64: str | None = None,
        tsa_provider: str | None = None,
        pdfa3_path: str | None = None,
        pdfa3_checksum: str | None = None,
    ) -> None:
        """Insert one ICP signature record."""
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        conn.execute(
            """
            INSERT INTO icp_signatures (
                sig_id, entity_type, entity_id, organization_id,
                cert_subject, cert_issuer, cert_serial,
                cert_not_before, cert_not_after, cert_type, icp_brasil,
                signature_type, signature_b64, signed_hash,
                signed_at, tsa_token_b64, tsa_provider,
                pdfa3_path, pdfa3_checksum, signed_by, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                result.sig_id, entity_type, entity_id, organization_id,
                result.cert_subject, result.cert_issuer, result.cert_serial,
                result.cert_not_before, result.cert_not_after,
                result.cert_type, int(result.icp_brasil),
                result.signature_type, result.signature_b64, result.signed_hash,
                now, tsa_token_b64, tsa_provider,
                pdfa3_path, pdfa3_checksum, signed_by, now,
            ),
        )

    def get_signature(self, conn: Any, sig_id: str) -> dict[str, Any] | None:
        """Retrieve one signature record by primary key."""
        row = conn.execute(
            "SELECT * FROM icp_signatures WHERE sig_id = ?", (sig_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_entity(
        self, conn: Any, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        """List all signatures for a given entity (hdr / forensic_package / ripd)."""
        rows = conn.execute(
            """SELECT * FROM icp_signatures
               WHERE entity_type=? AND entity_id=?
               ORDER BY created_at DESC""",
            (entity_type, entity_id),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── icp_verifications ──────────────────────────────────────────────────────

    def store_verification(
        self,
        conn: Any,
        *,
        verify_id: str,
        hdr_id: str,
        organization_id: str = "org_default",
        icp_verified: bool,
        signer_name: str | None,
        signer_cpf_cnpj: str | None = None,
        cert_issuer: str | None,
        cert_serial: str | None,
        cert_type: str | None,
        signing_time: str | None,
        signature_valid: bool,
        cert_chain_valid: bool,
        details_json: str = "{}",
        verified_by: str | None = None,
    ) -> None:
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        conn.execute(
            """
            INSERT INTO icp_verifications (
                verify_id, hdr_id, organization_id,
                icp_verified, signer_name, signer_cpf_cnpj,
                cert_issuer, cert_serial, cert_type, signing_time,
                signature_valid, cert_chain_valid, details_json,
                verified_at, verified_by
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                verify_id, hdr_id, organization_id,
                int(icp_verified), signer_name, signer_cpf_cnpj,
                cert_issuer, cert_serial, cert_type, signing_time,
                int(signature_valid), int(cert_chain_valid), details_json,
                now, verified_by,
            ),
        )

    def get_verification_for_hdr(
        self, conn: Any, hdr_id: str
    ) -> dict[str, Any] | None:
        """Return the most recent verification record for an HDR."""
        row = conn.execute(
            """SELECT * FROM icp_verifications
               WHERE hdr_id=? ORDER BY verified_at DESC LIMIT 1""",
            (hdr_id,),
        ).fetchone()
        return dict(row) if row else None

    # ── pdfa3_packages ──────────────────────────────────────────────────────────

    def store_pdfa3_package(
        self,
        conn: Any,
        *,
        pdfa3_id: str,
        package_id: str,
        organization_id: str = "org_default",
        pdf_path: str,
        pdf_checksum: str,
        attachments_json: str = "[]",
        is_signed: bool = False,
        sig_id: str | None = None,
        created_by: str,
    ) -> None:
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        conn.execute(
            """
            INSERT INTO pdfa3_packages (
                pdfa3_id, package_id, organization_id,
                pdf_path, pdf_checksum, pdf_version,
                attachments_json, is_signed, sig_id,
                created_at, created_by
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                pdfa3_id, package_id, organization_id,
                pdf_path, pdf_checksum, "A-3",
                attachments_json, int(is_signed), sig_id,
                now, created_by,
            ),
        )

    def get_pdfa3_package(self, conn: Any, pdfa3_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM pdfa3_packages WHERE pdfa3_id=?", (pdfa3_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_package(
        self, conn: Any, package_id: str
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            """SELECT * FROM pdfa3_packages WHERE package_id=?
               ORDER BY created_at DESC""",
            (package_id,),
        ).fetchall()
        return [dict(r) for r in rows]
