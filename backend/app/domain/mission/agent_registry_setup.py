"""Factory wiring EASY ``AgentRegistry`` against runtime ``Settings``."""

from __future__ import annotations

from app.core import config as runtime_config
from app.core.config import Settings
from app.domain.mission.agent_registry import AgentRegistry
from app.domain.mission.executors_llm import OpenAICompatibleMissionExecutor
from app.domain.mission.executors_stub import DeterministicStubMissionExecutor
from app.domain.mission.services import DEFAULT_AGENTS


def build_agent_registry(settings: Settings | None = None) -> AgentRegistry:
    """Hydrate catalogue plus executors — LLM-backed analysis only when credentials exist."""

    settings = settings or runtime_config.get_settings()
    fallback = DeterministicStubMissionExecutor()
    registry = AgentRegistry(fallback_executor=fallback)

    for definition in DEFAULT_AGENTS:
        executor: DeterministicStubMissionExecutor | OpenAICompatibleMissionExecutor
        use_llm_for_analysis = definition.agent_id == "analysis-agent" and bool(settings.OPENAI_API_KEY)

        if use_llm_for_analysis:
            executor = OpenAICompatibleMissionExecutor(
                agent_binding=definition.agent_id,
                api_key=settings.OPENAI_API_KEY or "",
                base_url=f"{settings.OPENAI_API_BASE_URL.rstrip('/')}/v1",
                model=settings.OPENAI_MODEL,
            )

            patched = definition.model_copy(update={"model": settings.OPENAI_MODEL})
            registry.register(patched, executor)
            continue

        executor = DeterministicStubMissionExecutor(agent_binding=definition.agent_id)
        registry.register(definition, executor)

    return registry


create_default_agent_registry = build_agent_registry
