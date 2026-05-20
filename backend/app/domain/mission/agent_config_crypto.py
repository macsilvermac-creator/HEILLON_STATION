"""Fernet symmetric helpers keyed from a dedicated configured secret (not the JWT secret)."""

from __future__ import annotations

from cryptography.fernet import Fernet

from app.core import config as cfg
from app.core.config import _derive_fernet_key_from_auth


def build_config_fernet(*, secret_material: str | None = None) -> Fernet:
    """Build Fernet from explicit material, ``FERNET_ENCRYPTION_KEY``, or a deterministic dev derivation."""

    if secret_material is not None and str(secret_material).strip():
        key_source = str(secret_material).strip()
    else:
        settings = cfg.get_settings()
        key_source = (settings.FERNET_ENCRYPTION_KEY or "").strip() or _derive_fernet_key_from_auth(
            settings.AUTH_SECRET_KEY
        )
    if not key_source:
        msg = "FERNET_ENCRYPTION_KEY is not configured"
        raise ValueError(msg)
    return Fernet(key_source.encode("utf-8"))
