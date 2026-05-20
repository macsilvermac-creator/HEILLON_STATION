"""Detached Ed25519 manifest signature checks."""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidSignature

from app.domain.forensic.signature_service import ForensicManifestSigner


def test_manifest_signatures_verify_with_public_half():
    signer = ForensicManifestSigner()
    canonical = b'demo-manifest-bytes-emitted-canonical-sort="true"'
    signature = signer.sign(canonical)

    public = signer._private_key.public_key()  # noqa: SLF001 — whitebox verifier anchored to cryptography
    public.verify(signature, canonical)


def test_manifest_signature_rejects_altered_payload():
    signer = ForensicManifestSigner()
    signature = signer.sign(b"trusted-payload-lock")
    public = signer._private_key.public_key()  # noqa: SLF001
    with pytest.raises(InvalidSignature):
        public.verify(signature, b"altered-payload")
