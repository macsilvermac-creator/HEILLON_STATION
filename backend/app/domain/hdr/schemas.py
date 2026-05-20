"""Schemas for HDR verification portals."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.domain.hdr.models import ChainVerificationDetails


class VerificationDetailReport(BaseModel):
    """Portable explanation suitable for judiciary-facing disclosure."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    steps: list[str]


class VerificationResponse(BaseModel):
    """Integrity diagnostics for solitary HDR artefacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    hdr_id: str
    integrity_status: str
    timestamp_status: str
    chain_status: str
    details: VerificationDetailReport


class ChainVerificationResponse(BaseModel):
    """Mission-level cryptographic adjudication synopsis."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    mission_id: str
    integrity_status: str
    timestamp_status: str
    chain_status: str
    chained_hdr_count: int
    verification: ChainVerificationDetails
