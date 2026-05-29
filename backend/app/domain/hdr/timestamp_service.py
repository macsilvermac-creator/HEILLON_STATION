"""RFC 3161 trusted timestamp issuance and verification primitives.

Provider routing:
  - ``TSA_PROVIDER=stub`` or ``FORCE_STUB_TIMESTAMP=True`` → deterministic stub (dev/test only).
  - ``TSA_PROVIDER=certisign`` → ICP-Brasil Certisign, fallback Serpro → FreeTSA.
  - ``TSA_PROVIDER=serpro``    → ICP-Brasil Serpro,    fallback Certisign → FreeTSA.
  - ``TSA_PROVIDER=freetsa``   → FreeTSA directly (no ICP-Brasil guarantee).
"""

from __future__ import annotations

import base64
import logging

import httpx

from app.core import config as runtime_config
from app.core.config import Settings
from app.core.security import generate_hash
from app.domain.hdr.icp_brasil import stamp_with_fallback, verify_icp_timestamp

_LOGGER = logging.getLogger(__name__)

STUB_PREFIX = b"STUBTSA1:"


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
    """Fetch a DER ``TimeStampResp`` from the configured TSA provider (Base64 text).

    Routing:
    1. If ``FORCE_STUB_TIMESTAMP`` or ``TSA_PROVIDER=='stub'``: return deterministic stub.
    2. Otherwise delegate to :func:`~app.domain.hdr.icp_brasil.stamp_with_fallback`,
       which tries the preferred provider then falls back through the chain.
    3. On total failure, degrade to stub only when ``allow_stub_fallback`` is ``True``.

    Args:
        data: Canonical bytes whose SHA-256 is imprinted into the TSA request.
        settings: Operational settings; uses ``get_settings()`` when omitted.
        client: Optional pooled httpx.Client reused by callers.
        allow_stub_fallback: When ``True``, degrades gracefully to deterministic stub stamps.

    Returns:
        Base64-encoded PKCS#11 response bytes (or stub token).

    Raises:
        RuntimeError: If ``allow_stub_fallback`` is ``False`` and every provider fails.
    """
    settings = settings or runtime_config.get_settings()

    use_stub = settings.FORCE_STUB_TIMESTAMP or settings.TSA_PROVIDER.lower() == "stub"
    if use_stub:
        _LOGGER.debug("TSA stub mode active — returning deterministic token.")
        return _stub_token(data)

    try:
        result = stamp_with_fallback(
            data,
            preferred_provider=settings.TSA_PROVIDER,
            client=client,
        )
        return result.token_b64
    except Exception as exc:  # noqa: BLE001
        message = (
            f"RFC3161 stamping failed ({exc.__class__.__name__}): "
            "enable allow_stub_fallback in controlled environments."
        )
        if allow_stub_fallback:
            _LOGGER.warning("%s — using deterministic stub stamp.", message)
            return _stub_token(data)
        raise RuntimeError(message) from exc


def verify_timestamp(data: bytes, timestamp_token: str) -> bool:
    """Validate token binding to ``SHA256(data)``.

    Handles both deterministic stub tokens (development) and real RFC 3161 DER tokens.

    Args:
        data: Original bytes imprinted at stamp time.
        timestamp_token: Base64 DER ``TimeStampResp`` or stub token.

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

    return verify_icp_timestamp(data, timestamp_token)


def deterministic_development_stamp(data: bytes) -> str:
    """Produce reproducible PKCS#11 stand-ins for deterministic regressions."""
    return _stub_token(data)
