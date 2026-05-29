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

_PREVIEW_CHARS = 400


def build_ingestion_hdr(
    hdr_svc: HDRService,
    *,
    sanitized_name: str,
    inferred_mission_id: str,
    checksum: str,
    previous_hdr: str | None,
    extracted_text: str = "",
) -> HDR:
    """Compose ingestion HDR artefacts for filesystem ingress."""

    text_preview = extracted_text[:_PREVIEW_CHARS].strip()
    has_text = bool(text_preview)

    hypothesis = (
        f"Document `{sanitized_name}` contains extractable text content for legal analysis."
        if has_text
        else f"Binary artefact `{sanitized_name}` preserved with deterministic SHA-256 digest."
    )
    result_detail = (
        f"Extracted {len(extracted_text)} chars; preview: «{text_preview[:120]}…»"
        if has_text
        else f"Integrity digest `{checksum}` anchored for mission DAG chaining."
    )

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
            tools_required=["local_sha256_manifest", "text_extractor"]
            if has_text
            else ["local_sha256_manifest"],
            estimated_cost_gas=0.05,
        ),
        execution=HDRExecution(
            status="completed",
            input_hash=checksum,
            output_hash=checksum,
            duration_ms=0,
        ),
        cognitive_snapshot=HDRCognitiveSnapshot(
            hypothesis=hypothesis,
            action="Persist byte-identical envelope with deterministic SHA-256 digest and extract text content.",
            result=result_detail,
        ),
        normative=HDRNormative(
            checked=True,
            violations=[],
            corpus_version="v1_legal_default",
        ),
        previous_hdr=previous_hdr,
    )
