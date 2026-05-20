"""Anthropic Messages API executor emitting EASY HDR-oriented outcomes."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.core.security import generate_hash
from app.domain.mission.agent_execution import MissionAgentExecutionOutcome
from app.domain.mission.models import DAGNode

ANTHROPIC_VERSION_HEADER = "2023-06-01"


class AnthropicMessagesMissionExecutor:
    """Invokes Claude via ``/v1/messages``."""

    def __init__(
        self,
        *,
        agent_binding: str,
        api_key: str,
        model: str,
        api_base_url: str = "https://api.anthropic.com",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.agent_id = agent_binding
        self._api_key = api_key.strip()
        self._model = model
        self._base_url = api_base_url.rstrip("/")
        self._timeout = timeout_seconds

    def execute(
        self,
        *,
        node: DAGNode,
        mission_id: str,
        plan_description: str,
        chunk_cost: float,
        authorized_tools: list[str],
        context: dict[str, Any] | None = None,
    ) -> MissionAgentExecutionOutcome:
        prompt_payload = json.dumps(
            {
                "mission_id": mission_id,
                "node": node.model_dump(mode="json"),
                "plan_excerpt": plan_description[:800],
                "chunk_cost_gas": chunk_cost,
                "authorized_tools": authorized_tools,
                "context": context or {},
            },
            sort_keys=True,
        )
        system_block = (
            "You are HEILLON-LEGAL EASY. Reply with compact JSON only. "
            "Keys: hypothesis (string), summary (string), confidence (number 0..1)."
        )
        duration_ms = 0

        user_message = prompt_payload[:120000]

        try:
            with httpx.Client(timeout=self._timeout) as client:
                t0 = time.perf_counter()
                response = client.post(
                    f"{self._base_url}/v1/messages",
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": ANTHROPIC_VERSION_HEADER,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "max_tokens": 1024,
                        "temperature": 0.2,
                        "system": system_block,
                        "messages": [{"role": "user", "content": user_message}],
                    },
                )
                duration_ms = max(int((time.perf_counter() - t0) * 1000.0), 1)

            response.raise_for_status()
            envelope = response.json()

            bundled_parts: list[str] = []
            for block in envelope.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_fragment = block.get("text") or ""
                    if isinstance(text_fragment, str):
                        bundled_parts.append(text_fragment)
            bundled = "\n".join(part for part in bundled_parts if part.strip()).strip()

            hypothesis = ""
            summary = ""
            try:
                payload = json.loads(bundled)
                hypothesis = str(payload.get("hypothesis") or "").strip()
                summary = str(payload.get("summary") or "").strip()
            except json.JSONDecodeError:
                hypothesis = "Anthropic emitted non-JSON prose."
                summary = bundled[:12000]

            body_for_hash = hypothesis + "\n" + summary + "\n" + bundled
            out_hash = generate_hash(body_for_hash.encode("utf-8"))

            return MissionAgentExecutionOutcome(
                cognitive_hypothesis=hypothesis or "Anthropic returned empty hypothesis.",
                cognitive_action=f"Anthropic cognition for `{node.agent_id}:{node.action}`.",
                cognitive_result=(summary or bundled)[:12000],
                execution_status="completed",
                input_hash_hex=generate_hash(prompt_payload.encode("utf-8")),
                output_hash_hex=out_hash,
                duration_ms=duration_ms,
            )

        except Exception as exc:  # noqa: BLE001 — executor boundary contract

            return MissionAgentExecutionOutcome(
                cognitive_hypothesis="Anthropic invocation failed.",
                cognitive_action=f"node `{node.node_id}` `{node.agent_id}:{node.action}`",
                cognitive_result=str(exc)[:4096],
                execution_status="failed",
                input_hash_hex=generate_hash(prompt_payload.encode("utf-8")),
                output_hash_hex=None,
                duration_ms=max(duration_ms, 0),
            )
