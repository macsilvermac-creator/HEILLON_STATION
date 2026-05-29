"""Fernet symmetric helpers keyed from a dedicated configured secret (not the JWT secret).

Supports KEY ROTATION via MultiFernet:
- ``FERNET_ENCRYPTION_KEY`` (active) — always used to ENCRYPT new ciphertext.
- ``FERNET_ENCRYPTION_KEY_LEGACY`` (comma-separated, optional) — older keys tried in
  order during DECRYPT. Once all stored ciphertext is re-encrypted with the active
  key, the legacy ring can be emptied.

The returned object is a ``Fernet`` (single key) OR ``MultiFernet`` (key ring). Both
expose identical ``encrypt(bytes)`` and ``decrypt(bytes)`` methods, so callers don't
need to branch.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, MultiFernet

from app.core import config as cfg
from app.core.config import _derive_fernet_key_from_auth


def _parse_legacy_keys(raw: str) -> list[str]:
    """Split comma-separated legacy keys, strip whitespace, drop empties."""
    return [k.strip() for k in raw.split(",") if k.strip()]


def build_config_fernet(*, secret_material: str | None = None) -> Fernet | MultiFernet:
    """Build Fernet from explicit material, or ``FERNET_ENCRYPTION_KEY`` (+ optional legacy ring).

    When ``FERNET_ENCRYPTION_KEY_LEGACY`` is set, returns a ``MultiFernet`` so existing
    ciphertext encrypted with old keys remains decryptable while new ciphertext uses
    the active key. Explicit ``secret_material`` ignores the legacy ring (single-key mode).
    """

    if secret_material is not None and str(secret_material).strip():
        # Explicit override (e.g., tests, ephemeral instances) — single key
        key_source = str(secret_material).strip()
        return Fernet(key_source.encode("utf-8"))

    settings = cfg.get_settings()
    active = (
        settings.FERNET_ENCRYPTION_KEY or ""
    ).strip() or _derive_fernet_key_from_auth(settings.AUTH_SECRET_KEY)
    if not active:
        msg = "FERNET_ENCRYPTION_KEY is not configured"
        raise ValueError(msg)

    legacy_keys = _parse_legacy_keys(settings.FERNET_ENCRYPTION_KEY_LEGACY or "")
    if not legacy_keys:
        return Fernet(active.encode("utf-8"))

    # MultiFernet uses the FIRST instance for encryption; later ones only for decrypt.
    fernets = [Fernet(active.encode("utf-8"))]
    fernets.extend(Fernet(k.encode("utf-8")) for k in legacy_keys)
    return MultiFernet(fernets)


def rotate_token(fernet: Fernet | MultiFernet, ciphertext: bytes) -> bytes:
    """Re-encrypt a token under the ACTIVE key.

    On ``MultiFernet``, ``rotate()`` decrypts with any valid key and re-encrypts with
    the active one — used by ops jobs that migrate stored ciphertext after rotation.
    On a plain ``Fernet``, this is a no-op identity (decrypt + encrypt under same key).
    """
    if isinstance(fernet, MultiFernet):
        return fernet.rotate(ciphertext)
    # Plain Fernet: decrypt + encrypt under same key (effectively refreshes the timestamp)
    return fernet.encrypt(fernet.decrypt(ciphertext))
