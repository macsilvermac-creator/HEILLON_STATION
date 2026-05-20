"""Cryptographic hashing and Ed25519 signing helpers."""

from __future__ import annotations

import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def generate_hash(data: bytes) -> str:
    """Compute the SHA-256 digest of arbitrary bytes encoded as hexadecimal.

    Args:
        data: Raw payload to digest.

    Returns:
        Lowercase hexadecimal SHA-256 string (length 64).
    """
    return hashlib.sha256(data).hexdigest()


def generate_hdr_id(canonical_json_str: str) -> str:
    """Derive HDR identifier as SHA-256 hex of canonical JSON text.

    The identifier is deterministic for a given canonical input string.

    Args:
        canonical_json_str: UTF-8 JSON text that has already been canonicalized.

    Returns:
        Lowercase hexadecimal SHA-256 digest of UTF-8 bytes.
    """
    return generate_hash(canonical_json_str.encode("utf-8"))


def generate_ed25519_keypair() -> tuple[bytes, bytes]:
    """Generate a random Ed25519 key pair encoded as raw 32-byte seeds/keys.

    Returns:
        A tuple ``(private_key_seed, public_key_bytes)``. The private portion is
        the raw PKCS#8 seed bytes usable with :mod:`cryptography`.
    """
    private_key = Ed25519PrivateKey.generate()
    seed = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return seed, public_bytes


def sign_data(private_key: bytes, data: bytes) -> bytes:
    """Sign data with Ed25519 using a raw private key seed.

    Args:
        private_key: 32-byte Ed25519 seed (RFC 8032 private scalar encoding).
        data: Payload to authenticate.

    Returns:
        Raw 64-byte Ed25519 signature.
    """
    sk = Ed25519PrivateKey.from_private_bytes(private_key)
    return sk.sign(data)


def verify_signature(public_key: bytes, data: bytes, signature: bytes) -> bool:
    """Verify an Ed25519 signature.

    Args:
        public_key: 32-byte public key encoding.
        data: Payload that was allegedly signed.
        signature: Alleged detached signature bytes.

    Returns:
        ``True`` if the signature verifies, ``False`` on any cryptographic
        mismatch or malformed key material (fail-closed semantics).
    """
    try:
        pk = Ed25519PublicKey.from_public_bytes(public_key)
        pk.verify(signature, data)
        return True
    except Exception:
        return False
