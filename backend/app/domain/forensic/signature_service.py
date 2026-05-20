"""Detached Ed25519 signatures over forensic manifests."""

from __future__ import annotations

import binascii
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ed25519


class ForensicManifestSigner:
    """Sign courtroom manifests with detachable Ed25519 envelopes."""

    def __init__(self, *, private_key_seed: bytes | None = None) -> None:
        if private_key_seed is None:
            self._private_key = ed25519.Ed25519PrivateKey.generate()
        else:
            if len(private_key_seed) != ed25519.Ed25519PrivateKey.SEED_BYTE_LENGTH:
                msg = (
                    "Ed25519 seed must unpack to 32 bytes — supply a 64-hex-character representation "
                    "via `FORENSICS_SIGNATURE_PRIVATE_KEY_HEX`."
                )
                raise ValueError(msg)
            self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_seed)

    @classmethod
    def from_hex_optional(cls, maybe_hex: str | None) -> ForensicManifestSigner:
        seed: bytes | None
        if not maybe_hex:
            seed = None
        else:
            seed = binascii.unhexlify(maybe_hex.strip())
            if len(seed) != ed25519.Ed25519PrivateKey.SEED_BYTE_LENGTH:
                msg = (
                    "`FORENSICS_SIGNATURE_PRIVATE_KEY_HEX` deve representar uma seed raw "
                    "de 32 bytes (64 dígitos hex)."
                )
                raise ValueError(msg)

        return cls(private_key_seed=seed)

    def sign(self, canonical_manifest_bytes: bytes) -> bytes:
        return self._private_key.sign(canonical_manifest_bytes)

    def write_signature_file(self, target: Path, canonical_manifest_bytes: bytes) -> None:
        target.write_bytes(self.sign(canonical_manifest_bytes))
