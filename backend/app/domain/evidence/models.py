"""Evidence package envelope models for forensic export milestones."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.hdr.models import HDR


class EvidenceEnvelope(BaseModel):
    """Declarative linkage between filesystem custody and HDR identifiers."""

    model_config = {"extra": "forbid", "frozen": True}

    evidence_id: str
    hdr_id: str = Field(description="Primary HDR ingestion anchor.")
    storage_path: str


class IngestionResponse(BaseModel):
    """Ingress acknowledgement bundling cryptographic custody artefacts."""

    model_config = {"frozen": True}

    hdr: HDR
    evidence_storage_path: str
