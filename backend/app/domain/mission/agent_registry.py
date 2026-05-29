"""Registry attaching catalog metadata and runtime executors for EASY agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.mission.models import AgentDefinition

if TYPE_CHECKING:
    from app.domain.mission.agent_execution import MissionAgentExecutor


class AgentRegistry:
    """Maps mission agent identifiers to catalog rows plus concrete executors."""

    def __init__(
        self, *, fallback_executor: MissionAgentExecutor | None = None
    ) -> None:
        self._definitions: dict[str, AgentDefinition] = {}
        self._executors: dict[str, MissionAgentExecutor] = {}
        self._fallback_executor = fallback_executor

    def register(
        self, definition: AgentDefinition, executor: MissionAgentExecutor
    ) -> None:
        """Associate a catalogue entry with the executor wired for runtime."""

        self._definitions[definition.agent_id] = definition
        self._executors[definition.agent_id] = executor

    def list_definitions(self) -> list[AgentDefinition]:
        return list(self._definitions.values())

    def get_definition(self, agent_id: str) -> AgentDefinition | None:
        return self._definitions.get(agent_id)

    def get_executor(self, agent_id: str) -> MissionAgentExecutor | None:
        return self._executors.get(agent_id)

    def resolve_executor(self, agent_id: str) -> MissionAgentExecutor | None:
        """Return executor for ``agent_id`` or configured fallback."""

        return self._executors.get(agent_id) or self._fallback_executor


def synthetic_definition(agent_id: str) -> AgentDefinition:
    """Build a permissive catalogue row for DAG nodes referencing unregistered IDs."""

    return AgentDefinition(
        agent_id=agent_id,
        name=f"Synthetic EASY worker `{agent_id}`",
        capabilities=[],
        model="fallback-stub",
        version="1.0",
    )
