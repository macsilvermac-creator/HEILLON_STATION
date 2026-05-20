"""Forensic export aggregates for courtroom disclosure."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ForensicPackageStatus(str, Enum):
    """Lifecycle state machines for EASY forensic bundles."""

    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditManifest(BaseModel):
    """Integrity manifest anchored to judiciary verification rails."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package_id: str
    mission_id: str
    chain_root: str
    chain_tail: str
    total_hdrs: int
    generated_at: datetime
    generated_by: str
    integrity_hash: str
    verification_url: str


class ForensicPackage(BaseModel):
    """Complete forensic dossier bridging PDF, JSON lineage, plus manifest."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    package_id: str
    mission_id: str
    status: ForensicPackageStatus = ForensicPackageStatus.GENERATING
    manifest: AuditManifest | None = None
    pdf_checksum: str | None = None
    json_chain_checksum: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    download_url: str | None = None
