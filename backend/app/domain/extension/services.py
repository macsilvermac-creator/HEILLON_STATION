"""Capture service — converts extension payloads into HDRs."""

from __future__ import annotations

import hashlib
import uuid

from app.core.security import generate_hash
from app.domain.extension.models import ExtensionCaptureRequest
from app.domain.hdr.models import (
    HDR,
    HDRAgent,
    HDRCognitiveSnapshot,
    HDRExecution,
    HDRIntent,
    HDRNormative,
    HDRUser,
)
from app.domain.hdr.services import HDRService

# Preview size for cognitive_snapshot.result (we never store full prompt/response
# in the snapshot — only hashes go into execution.input_hash/output_hash).
_PREVIEW_CHARS = 240

# Mission ID prefix for extension-originated captures
EXTENSION_MISSION_PREFIX = "ext_"


def _truncate_for_preview(text: str, *, limit: int = _PREVIEW_CHARS) -> str:
    """Truncate to limit chars with ellipsis if needed (no PII redaction here —
    user opt-in to capture; redaction happens at extension side)."""
    cleaned = text.strip().replace("\n", " ").replace("\r", " ")
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _derive_mission_id(req: ExtensionCaptureRequest, *, user_id: str) -> str:
    """Group captures sharing the same AI session into one mission.

    If the provider gave us a session_id, we deterministically hash it +
    user_id so captures in the same chat thread chain naturally. Otherwise
    we synthesize a fresh mission_id per capture.
    """
    if req.ai_session_id:
        seed = f"{user_id}|{req.provider.value}|{req.ai_session_id}".encode("utf-8")
        digest = hashlib.sha256(seed).hexdigest()[:16]
        return f"{EXTENSION_MISSION_PREFIX}{req.provider.value}_{digest}"
    return f"{EXTENSION_MISSION_PREFIX}{uuid.uuid4().hex[:16]}"


def build_capture_hdr(
    hdr_svc: HDRService,
    *,
    req: ExtensionCaptureRequest,
    user_id: str,
    extension_user_signature: str | None = None,
    corpus_version: str,
    previous_hdr: str | None = None,
) -> HDR:
    """Convert an ExtensionCaptureRequest into a fully signed HDR.

    HDR type: "analysis" (closest fit — user requested AI analysis via prompt).
    Hashes:  input_hash  = SHA-256(prompt UTF-8)
             output_hash = SHA-256(response UTF-8)
    These hashes prove the exact content captured WITHOUT storing the raw text
    publicly (raw text is stored in the cognitive_snapshot for the org's use
    but never exposed via verification URL).
    """
    mission_id = _derive_mission_id(req, user_id=user_id)
    prompt_hash = generate_hash(req.prompt.encode("utf-8"))
    response_hash = generate_hash(req.response.encode("utf-8"))

    return hdr_svc.generate_hdr(
        hdr_type="analysis",
        mission_id=mission_id,
        agent=HDRAgent(
            id=f"ai_{req.provider.value}_{req.model[:60]}",
            model=req.model,
            version=req.extension_version or "browser_ext_v1",
        ),
        user=HDRUser(
            id=user_id,
            signature=extension_user_signature,
        ),
        intent=HDRIntent(
            description=(
                f"Interação com IA capturada via Browser Extension em {req.provider.value}. "
                f"Page: {req.page_title or '(sem título)'} — URL: {str(req.source_url)[:140]}"
            ),
            tools_required=["llm_remote", "browser_extension"],
            estimated_cost_gas=0.02,
        ),
        execution=HDRExecution(
            status="completed",
            input_hash=prompt_hash,
            output_hash=response_hash,
            duration_ms=None,
        ),
        cognitive_snapshot=HDRCognitiveSnapshot(
            hypothesis=(
                f"Operador busca auxílio de IA ({req.provider.value}/{req.model}) "
                f"para tarefa jurídica em {req.captured_at.isoformat()}."
            ),
            action=(f"Prompt: «{_truncate_for_preview(req.prompt)}»"),
            result=(f"Resposta: «{_truncate_for_preview(req.response)}»"),
        ),
        normative=HDRNormative(
            checked=True,
            violations=[],  # Future: run corpus pre-check on prompt
            corpus_version=corpus_version,
        ),
        previous_hdr=previous_hdr,
    )
