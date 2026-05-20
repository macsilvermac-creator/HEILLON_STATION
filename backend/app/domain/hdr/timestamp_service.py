"""RFC 3161 trusted timestamp issuance and verification primitives."""

from __future__ import annotations

import base64
import logging
from hashlib import sha256

import httpx
from asn1crypto import algos, tsp

from app.core import config as runtime_config
from app.core.config import Settings
from app.core.security import generate_hash

_LOGGER = logging.getLogger(__name__)

STUB_PREFIX = b"STUBTSA1:"


def _build_timestamp_req(data: bytes) -> tsp.TimeStampReq:
    """Compose a PKCS#11 ``TimeStampReq`` object stamping ``SHA256(data)``.

    Args:
        data: Raw bytes hashed into RFC 5652 ``MessageImprint``.

    Returns:
        Encodable ASN.1 request structure targeting the configured authority.
    """

    digest = sha256(data).digest()
    imprint = tsp.MessageImprint(
        {
            "hash_algorithm": algos.DigestAlgorithm({"algorithm": "sha256"}),
            "hashed_message": digest,
        }
    )
    return tsp.TimeStampReq({"version": 1, "message_imprint": imprint, "cert_req": True})


def _stub_token(data: bytes) -> str:
    """Return deterministic development-time token encoding ``STUBTSA1:`` semantics."""

    digest_ascii = generate_hash(data).encode("ascii")
    return base64.b64encode(STUB_PREFIX + digest_ascii).decode("ascii")


def get_timestamp(
    data: bytes,
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    allow_stub_fallback: bool = False,
) -> str:
    """Fetch a DER ``TimeStampResp`` from ``settings.TSA_URL`` (Base64 text).

    Args:
        data: Logical bytes hashed into PKCS#11 message imprint deterministically.
        settings: Operational settings overriding defaults for tests/DI scenarios.
        client: Optional pooled ``httpx`` client reused by callers.
        allow_stub_fallback: When ``True``, degrades gracefully to deterministic stub stamps.

    Returns:
        Base64-encoded PKCS#11 response bytes.

    Raises:
        RuntimeError: If ``allow_stub_fallback`` is ``False`` and transport/decoding fails.
    """

    settings = settings or runtime_config.get_settings()
    owns_client = client is None
    http_client = client or httpx.Client(timeout=30.0)

    request_der = _build_timestamp_req(data).dump()

    try:
        response = http_client.post(
            settings.TSA_URL,
            content=request_der,
            headers={"Content-Type": "application/timestamp-query"},
        )
        response.raise_for_status()
        tsp.TimeStampResp.load(response.content)
        return base64.b64encode(response.content).decode("ascii")
    except Exception as exc:  # noqa: BLE001
        message = (
            f"RFC3161 stamping failed ({exc.__class__.__name__}): "
            "enable allow_stub_fallback in controlled environments."
        )
        if allow_stub_fallback:
            _LOGGER.warning("%s — using deterministic stub stamp.", message)
            return _stub_token(data)
        raise RuntimeError(message) from exc
    finally:
        if owns_client:
            http_client.close()


def verify_timestamp(data: bytes, timestamp_token: str) -> bool:
    """Validate token binding to ``SHA256(data)``.

    Args:
        data: Original hashed bytes imprinted inside the PKCS#11 request.
        timestamp_token: Base64 PKCS#11 response or deterministic stub emitted in tests.

    Returns:
        ``True`` whenever structural parsing succeeds and digests reconcile.
    """

    try:
        der = base64.b64decode(timestamp_token.encode("ascii"), validate=True)
    except Exception:
        return False

    if der.startswith(STUB_PREFIX):
        remainder = der[len(STUB_PREFIX) :]
        try:
            remote_digest_ascii = remainder.decode("ascii")
        except UnicodeDecodeError:
            return False
        return remote_digest_ascii == generate_hash(data)

    try:
        tsr_native = tsp.TimeStampResp.load(der).native
        if tsr_native["status"]["status"] != "granted":
            return False
        tst_native = tsr_native["time_stamp_token"]["content"]["encap_content_info"]["content"]
        remote_digest = tst_native["message_imprint"]["hashed_message"]
    except Exception:  # noqa: BLE001
        return False

    return remote_digest == sha256(data).digest()


def deterministic_development_stamp(data: bytes) -> str:
    """Produce reproducible PKCS#11 stand-ins for deterministic regressions."""

    return _stub_token(data)
