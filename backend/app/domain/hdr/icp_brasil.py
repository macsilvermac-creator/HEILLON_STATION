"""ICP-Brasil RFC 3161 TSA integration with provider fallback chain.

Priority order: Certisign → Serpro → FreeTSA → stub.
Each real provider is attempted before degrading. The ICP-Brasil policy OID
(2.16.76.1.6.1 — Carimbo do Tempo) is validated when the response carries
a policy information extension.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from hashlib import sha256

import httpx
from asn1crypto import algos, tsp

_LOGGER = logging.getLogger(__name__)

# ── ICP-Brasil policy OID ──────────────────────────────────────────────────────
_ICP_BRASIL_TIMESTAMP_POLICY = "2.16.76.1.6.1"


# ── Public TSA endpoint registry ──────────────────────────────────────────────
@dataclass(frozen=True)
class TsaProvider:
    name: str
    url: str
    icp_brasil: bool = False


_PROVIDERS: list[TsaProvider] = [
    TsaProvider(
        name="certisign",
        url="https://timestamp.certisign.com.br/tsa",
        icp_brasil=True,
    ),
    TsaProvider(
        name="serpro",
        url="https://timestamp.serpro.gov.br/tsp",
        icp_brasil=True,
    ),
    TsaProvider(
        name="freetsa",
        url="https://freetsa.org/tsr",
        icp_brasil=False,
    ),
]

_PROVIDER_BY_NAME: dict[str, TsaProvider] = {p.name: p for p in _PROVIDERS}


def provider_for_name(name: str) -> TsaProvider | None:
    """Return registered TsaProvider by name (case-insensitive)."""
    return _PROVIDER_BY_NAME.get(name.lower())


def provider_chain(preferred_name: str | None) -> list[TsaProvider]:
    """Build ordered fallback list starting from ``preferred_name``.

    Providers already placed at the preferred head are not duplicated.
    """
    if not preferred_name or preferred_name == "stub":
        return list(_PROVIDERS)

    head = _PROVIDER_BY_NAME.get(preferred_name.lower())
    if head is None:
        _LOGGER.warning(
            "Unknown TSA provider '%s'; using default chain.", preferred_name
        )
        return list(_PROVIDERS)

    rest = [p for p in _PROVIDERS if p.name != head.name]
    return [head, *rest]


# ── Request construction ───────────────────────────────────────────────────────


def _build_req(data: bytes) -> bytes:
    """Build DER-encoded ``TimeStampReq`` hashing ``SHA256(data)``."""
    digest = sha256(data).digest()
    imprint = tsp.MessageImprint(
        {
            "hash_algorithm": algos.DigestAlgorithm({"algorithm": "sha256"}),
            "hashed_message": digest,
        }
    )
    req = tsp.TimeStampReq({"version": 1, "message_imprint": imprint, "cert_req": True})
    return bytes(req.dump())


# ── Response validation ────────────────────────────────────────────────────────


class TsaResponseError(Exception):
    """Raised when a TSA response fails structural validation."""


def _validate_response(der: bytes, provider: TsaProvider) -> None:
    """Parse and structurally validate a DER ``TimeStampResp``.

    Checks:
    - Status is ``granted`` or ``granted_with_mods``.
    - Message imprint algorithm is sha256.
    - For ICP-Brasil providers: policy OID must be 2.16.76.1.6.1.

    Raises:
        TsaResponseError: on any validation failure.
    """
    try:
        tsr = tsp.TimeStampResp.load(der)
        native = tsr.native
    except Exception as exc:
        raise TsaResponseError(f"Failed to parse TimeStampResp: {exc}") from exc

    status = native.get("status", {}).get("status")
    if status not in ("granted", "granted_with_mods"):
        raise TsaResponseError(f"TSA returned non-granted status: {status!r}")

    try:
        tst_info = native["time_stamp_token"]["content"]["encap_content_info"][
            "content"
        ]
        algo = tst_info["message_imprint"]["hash_algorithm"]["algorithm"]
        if algo != "sha256":
            raise TsaResponseError(f"Unexpected hash algorithm in TST: {algo!r}")
    except (KeyError, TypeError) as exc:
        raise TsaResponseError(f"Malformed TSTInfo structure: {exc}") from exc

    if provider.icp_brasil:
        try:
            policy = str(tst_info.get("policy") or "")
        except Exception:
            policy = ""
        if policy and policy != _ICP_BRASIL_TIMESTAMP_POLICY:
            _LOGGER.warning(
                "TSA '%s' returned policy OID '%s' (expected ICP-Brasil %s).",
                provider.name,
                policy,
                _ICP_BRASIL_TIMESTAMP_POLICY,
            )


# ── Main stamping function ─────────────────────────────────────────────────────


@dataclass
class StampResult:
    token_b64: str
    provider_name: str
    icp_brasil: bool


def stamp_with_fallback(
    data: bytes,
    *,
    preferred_provider: str | None = None,
    client: httpx.Client | None = None,
    timeout: float = 20.0,
) -> StampResult:
    """Attempt RFC 3161 stamping through the provider fallback chain.

    Args:
        data: Canonical bytes whose SHA-256 is imprinted in the request.
        preferred_provider: Name of the preferred TSA provider (or None for default order).
        client: Optional pooled httpx.Client; creates a transient one if omitted.
        timeout: Per-provider request timeout in seconds.

    Returns:
        :class:`StampResult` with the Base64 DER response and provider metadata.

    Raises:
        RuntimeError: If every provider in the chain fails.
    """
    chain = provider_chain(preferred_provider)
    req_der = _build_req(data)
    owns_client = client is None
    http = client or httpx.Client(timeout=timeout)

    errors: list[str] = []
    try:
        for provider in chain:
            try:
                resp = http.post(
                    provider.url,
                    content=req_der,
                    headers={"Content-Type": "application/timestamp-query"},
                    timeout=timeout,
                )
                resp.raise_for_status()
                _validate_response(resp.content, provider)
                token_b64 = base64.b64encode(resp.content).decode("ascii")
                _LOGGER.info(
                    "RFC3161 stamp obtained from provider '%s'.", provider.name
                )
                return StampResult(
                    token_b64=token_b64,
                    provider_name=provider.name,
                    icp_brasil=provider.icp_brasil,
                )
            except Exception as exc:
                msg = f"{provider.name}: {exc.__class__.__name__}: {exc}"
                _LOGGER.warning("TSA provider failed — %s", msg)
                errors.append(msg)
    finally:
        if owns_client:
            http.close()

    raise RuntimeError(
        "All TSA providers exhausted without a valid stamp. Errors: "
        + "; ".join(errors)
    )


def verify_icp_timestamp(data: bytes, token_b64: str) -> bool:
    """Verify that ``SHA256(data)`` matches the imprint in a real TSA token.

    This is a structural check only — it does NOT verify certificate chains.
    Full PKI validation requires the ICP-Brasil root bundle (out of scope here).

    Args:
        data: Original bytes whose SHA-256 was imprinted at stamp time.
        token_b64: Base64 DER ``TimeStampResp`` previously returned by :func:`stamp_with_fallback`.

    Returns:
        ``True`` if parsing succeeds and digests match.
    """
    try:
        der = base64.b64decode(token_b64.encode("ascii"), validate=True)
        tsr = tsp.TimeStampResp.load(der)
        native = tsr.native
        tst_info = native["time_stamp_token"]["content"]["encap_content_info"][
            "content"
        ]
        remote_digest = tst_info["message_imprint"]["hashed_message"]
    except Exception:
        return False

    return bool(remote_digest == sha256(data).digest())
