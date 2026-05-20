"""HTTP-backed LLM executor (OpenAI-compatible chat completions API)."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.core.security import generate_hash
from app.domain.mission.agent_execution import MissionAgentExecutionOutcome
from app.domain.mission.models import DAGNode


class OpenAICompatibleMissionExecutor:
    """Calls `/v1/chat/completions`; falls back gracefully when misconfigured."""

    def __init__(
        self,
        *,
        agent_binding: str,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.agent_id = agent_binding
        self._api_key = api_key.strip()
        self._base_url = base_url.rstrip("/")
        self._model = model
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
        prompt = json.dumps(
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
        hypothesis = ""
        summary = ""

        duration_ms = 0
        try:
            with httpx.Client(timeout=self._timeout) as client:
                t0 = time.perf_counter()
                response = client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "temperature": 0.2,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are HEILLON-LEGAL EASY. Reply with compact JSON only, "
                                    "keys: hypothesis (string), summary (string), "
                                    "confidence (number 0..1)."
                                ),
                            },
                            {"role": "user", "content": prompt[:12000]},
                        ],
                    },
                )
                duration_ms = max(int((time.perf_counter() - t0) * 1000.0), 1)

            response.raise_for_status()
            envelope = response.json()

            texts: list[str] = []
            for choice in envelope.get("choices") or []:
                message = choice.get("message") or {}
                fragment = message.get("content") or ""
                if isinstance(fragment, str) and fragment.strip():
                    texts.append(fragment.strip())
            bundled = "\n".join(texts).strip()

            try:
                payload = json.loads(bundled)
                hypothesis = str(payload.get("hypothesis") or "").strip()
                summary = str(payload.get("summary") or "").strip()
            except json.JSONDecodeError:
                hypothesis = "LLM emitted non-JSON prose."
                summary = bundled[:12000]

        except Exception as exc:  # noqa: BLE001 - boundary for executor surface

            return MissionAgentExecutionOutcome(
                cognitive_hypothesis="LLM invocation failed.",
                cognitive_action=f"node `{node.node_id}` `{node.agent_id}:{node.action}`",
                cognitive_result=str(exc)[:4096],
                execution_status="failed",
                input_hash_hex=generate_hash(prompt.encode("utf-8")),
                output_hash_hex=None,
                duration_ms=max(duration_ms, 0),
            )

        body_for_hash = hypothesis + "\n" + summary + "\n" + bundled
        out_hash = generate_hash(body_for_hash.encode("utf-8"))

        return MissionAgentExecutionOutcome(
            cognitive_hypothesis=hypothesis or "LLM returned empty hypothesis.",
            cognitive_action=f"Production LLM pass for `{node.agent_id}:{node.action}`.",
            cognitive_result=(summary or bundled)[:12000],
            execution_status="completed",
            input_hash_hex=generate_hash(prompt.encode("utf-8")),
            output_hash_hex=out_hash,
            duration_ms=duration_ms,
        )
