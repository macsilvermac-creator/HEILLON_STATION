"""Filesystem persistence for deterministic evidence artefacts."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class EvidenceRepository:
    """Writes byte-identical evidence envelopes under courthouse vault tiers."""

    def reserve_target(
        self, vault_root: Path, original_filename: str
    ) -> tuple[str, Path]:
        """Return ``(evidence_id, canonical_path)`` respecting collision isolation."""

        evidence_id = str(uuid4())
        sanitized_name = Path(original_filename or "evidence.bin").name
        target_dir = vault_root / evidence_id
        target_dir.mkdir(parents=True, exist_ok=True)
        canonical_path = target_dir / sanitized_name
        return evidence_id, canonical_path
