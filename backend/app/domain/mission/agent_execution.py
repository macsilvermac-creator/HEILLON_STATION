"""Execution outcomes for EASY mission orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from app.domain.mission.models import DAGNode


@dataclass(frozen=True)
class MissionAgentExecutionOutcome:
    """Structured result used to mint HDR artefacts after executor runs."""

    cognitive_hypothesis: str
    cognitive_action: str
    cognitive_result: str
    execution_status: str  # completed | failed
    input_hash_hex: str
    output_hash_hex: str | None
    duration_ms: int


@runtime_checkable
class MissionAgentExecutor(Protocol):
    """Protocol satisfied by deterministic stubs and production LLM / OCR backends."""

    agent_id: str

    async def execute(
        self,
        *,
        node: DAGNode,
        mission_id: str,
        plan_description: str,
        chunk_cost: float,
        authorized_tools: list[str],
        context: dict[str, Any] | None = None,
    ) -> MissionAgentExecutionOutcome: ...
