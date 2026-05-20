"""Domain services coordinating evidence cryptography."""

from __future__ import annotations

from app.domain.hdr.models import (
    HDRCognitiveSnapshot,
    HDRExecution,
    HDRIntent,
    HDRNormative,
    HDRAgent,
    HDRUser,
    HDR,
)
from app.domain.hdr.services import HDRService


def build_ingestion_hdr(
    hdr_svc: HDRService,
    *,
    sanitized_name: str,
    inferred_mission_id: str,
    checksum: str,
    previous_hdr: str | None,
) -> HDR:
    """Compose ingestion HDR artefacts for filesystem ingress."""

    return hdr_svc.generate_hdr(
        hdr_type="ingestion",
        mission_id=inferred_mission_id,
        agent=HDRAgent(
            id="agent_ingest_v1",
            model="heillon.ingest.blob_hasher.v1",
            version="2026.05",
        ),
        user=HDRUser(id="anonymous_uploader"),
        intent=HDRIntent(
            description=f"Immutable custody ingestion for artefact `{sanitized_name}`.",
            tools_required=["local_sha256_manifest"],
            estimated_cost_gas=0.05,
        ),
        execution=HDRExecution(
            status="completed",
            input_hash=checksum,
            output_hash=checksum,
            duration_ms=0,
        ),
        cognitive_snapshot=HDRCognitiveSnapshot(
            hypothesis="Uploaded binary preserved on deterministic local filesystem tier.",
            action="Persist byte-identical envelope with deterministic SHA-256 digest.",
            result=f"Integrity digest `{checksum}` anchored for mission DAG chaining.",
        ),
        normative=HDRNormative(
            checked=True,
            violations=[],
            corpus_version="v1_legal_default",
        ),
        previous_hdr=previous_hdr,
    )
