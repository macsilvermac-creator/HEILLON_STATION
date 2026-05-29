"""Deterministic stub executor reproducing Phase 3 EASY cognition semantics."""

from __future__ import annotations

from typing import Any

from app.core.security import generate_hash
from app.domain.mission.agent_execution import MissionAgentExecutionOutcome
from app.domain.mission.models import DAGNode


class DeterministicStubMissionExecutor:
    """Phase-3-compatible deterministic cognition + digest wiring."""

    def __init__(self, agent_binding: str | None = None) -> None:
        self.agent_id = agent_binding or "__stub_default__"

    async def execute(
        self,
        *,
        node: DAGNode,
        mission_id: str,
        plan_description: str,
        chunk_cost: float,
        authorized_tools: list[str],
        context: dict[str, Any] | None = None,
    ) -> MissionAgentExecutionOutcome:
        _ = (chunk_cost, authorized_tools, context, plan_description)

        seed_core = f"{mission_id}:{node.node_id}:{node.agent_id}:{node.action}".encode(
            "utf-8"
        )
        input_digest = generate_hash(seed_core)
        output_digest = generate_hash(seed_core + b"|stub-output")

        return MissionAgentExecutionOutcome(
            cognitive_hypothesis=(
                f"Stub cognition presumes `{node.agent_id}` can satisfy `{node.action}` reliably."
            ),
            cognitive_action=f"Synthetic EASY invocation for node `{node.node_id}`.",
            cognitive_result=(
                "Heuristic placeholders only — substitute production OCR/classification/analysis "
                "signals when EASY leaves stub mode."
            ),
            execution_status="completed",
            input_hash_hex=input_digest,
            output_hash_hex=output_digest,
            duration_ms=5,
        )


class FailingMissionExecutor:
    """Test hook simulating deterministic executor faults."""

    def __init__(self, agent_binding: str) -> None:
        self.agent_id = agent_binding

    async def execute(
        self,
        *,
        node: DAGNode,
        mission_id: str,
        plan_description: str,
        chunk_cost: float,
        authorized_tools: list[str],
        context: dict[str, Any] | None = None,
    ) -> MissionAgentExecutionOutcome:
        raise RuntimeError("forced executor failure")
