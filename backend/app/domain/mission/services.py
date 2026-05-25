"""EASY-lite orchestrator with deterministic planners and stub executions."""

from __future__ import annotations

import uuid
from collections import defaultdict, deque

from app.core.security import generate_hash
from app.domain.hdr.models import (
    HDR,
    HDRAgent,
    HDRCognitiveSnapshot,
    HDRExecution,
    HDRIntent,
    HDRNormative,
    HDRUser,
    HdrTypeLiteral,
)
from app.domain.hdr.services import HDRService
from app.domain.mission.agent_config_service import AgentConfigService
from app.domain.mission.agent_registry import AgentRegistry, synthetic_definition
from app.domain.mission.lexicon import KEYWORD_AGENT_MAP
from app.domain.mission.models import AgentDefinition, DAG, DAGNode, MissionPlan, MissionStatus
from app.domain.normative.services import NormativeService


DEFAULT_AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        agent_id="ocr-agent",
        name="OCR Agent",
        capabilities=["text_extraction"],
        model="tesseract-5.3",
        version="1.0",
    ),
    AgentDefinition(
        agent_id="classification-agent",
        name="Classification Agent",
        capabilities=["document_classification"],
        model="legal-bert-2.0",
        version="1.0",
    ),
    AgentDefinition(
        agent_id="analysis-agent",
        name="Analysis Agent",
        capabilities=["risk_detection", "clause_analysis"],
        model="legal-llm-3.0",
        version="1.0",
    ),
    AgentDefinition(
        agent_id="clustering-agent",
        name="Clustering Agent",
        capabilities=["document_clustering"],
        model="clustering-v2",
        version="1.0",
    ),
    AgentDefinition(
        agent_id="prioritization-agent",
        name="Prioritization Agent",
        capabilities=["relevance_scoring"],
        model="priority-v1",
        version="1.0",
    ),
    AgentDefinition(
        agent_id="extraction-agent",
        name="Extraction Agent",
        capabilities=["field_extraction"],
        model="extraction-mini",
        version="1.0",
    ),
    AgentDefinition(
        agent_id="summarization-agent",
        name="Summarization Agent",
        capabilities=["abstractive_summarization"],
        model="summarizer-v3",
        version="1.0",
    ),
)


class OrchestrationEngine:
    """Materializes EASY missions using DAG custody with pluggable cognition executors."""

    def __init__(
        self,
        normative_service: NormativeService,
        hdr_service: HDRService,
        agent_registry: AgentRegistry | None = None,
        *,
        agent_config_service: AgentConfigService | None = None,
    ) -> None:
        self._normative = normative_service
        self._hdr = hdr_service
        resolved_registry = agent_registry
        if resolved_registry is None:
            from app.domain.mission.agent_registry_setup import build_agent_registry

            resolved_registry = build_agent_registry()

        self._agent_registry = resolved_registry
        self._agent_cfg = agent_config_service

    def plan_mission(
        self,
        description: str,
        available_agent_ids: list[str],
        *,
        organization_id: str | None = None,
    ) -> MissionPlan:
        """Derive deterministic DAG scaffolding plus normative adjudication artefacts."""

        mission_id = f"mission_{uuid.uuid4().hex}"
        sanitized_description = description.strip()
        sanitized_agents = list(dict.fromkeys(available_agent_ids))

        inferred_agents = self._ordered_agent_selection(sanitized_description, sanitized_agents)
        tentative_dag = self._build_linear_dag(inferred_agents, sanitized_description)
        estimated_cost_gas = float(max(len(tentative_dag.nodes), 1) * 35)

        intent_context = {
            "authorized_tools": sanitized_agents,
            "estimated_cost_gas": estimated_cost_gas,
            "human_approved": False,
            "anonymization": False,
        }
        normative_result = self._normative.check_intent(sanitized_description, intent_context)

        if not normative_result.allowed:
            dag = DAG(nodes=[], edges=[])
            estimated_cost_gas = 0.0
        else:
            dag = tentative_dag

        return MissionPlan(
            mission_id=mission_id,
            description=sanitized_description,
            authorized_agent_ids=sanitized_agents,
            dag=dag,
            normative_result=normative_result,
            estimated_cost_gas=estimated_cost_gas,
            organization_id=organization_id or "org_default",
        )

    @staticmethod
    def _hdr_type_for(agent_id: str) -> HdrTypeLiteral:
        """Translate registry identifiers into HDR vocabulary."""

        normalized = {
            "ocr-agent": "ocr",
            "classification-agent": "classification",
            "analysis-agent": "analysis",
            "clustering-agent": "clustering",
            "prioritization-agent": "priority",
            "extraction-agent": "analysis",
            "summarization-agent": "analysis",
        }
        mapped = normalized.get(agent_id)
        if mapped:
            return mapped  # type: ignore[return-value]

        compact_agent = agent_id.casefold().replace("-", "").replace("_", "")
        for key, hdr_kind in normalized.items():
            condensed = key.casefold().replace("-", "").replace("_", "")
            if condensed == compact_agent:
                return hdr_kind  # type: ignore[return-value]

        return "analysis"

    def validate_dag(self, dag: DAG) -> bool:
        """Structural validation guarding against malformed graphs."""

        if not dag.nodes:
            return True

        node_lookup = {node.node_id: node for node in dag.nodes}
        if len(node_lookup) != len(dag.nodes):
            return False

        for node in dag.nodes:
            for dep in node.depends_on:
                if dep not in node_lookup:
                    return False

        if self._detect_cycles_from_nodes(dag):
            return False

        roots = [n for n in dag.nodes if not n.depends_on]
        return len(roots) == 1

    async def execute_mission(self, plan: MissionPlan, mission_id: str | None = None) -> list[HDR]:
        """Walk an approved DAG emitting cryptographic HDR artefacts per node."""

        if plan.status != MissionStatus.APPROVED:
            msg = "Mission must be APPROVED prior to EASY execution."
            raise ValueError(msg)

        if not plan.normative_result or not plan.normative_result.allowed:
            msg = "Mission normative rulings disallow automated execution."
            raise ValueError(msg)

        mid = mission_id or plan.mission_id
        if len(plan.dag.nodes) == 0 or not self.validate_dag(plan.dag):
            msg = "Malformed or empty DAG cannot execute."
            raise ValueError(msg)

        ordered_nodes = self._topological_sort(dag=plan.dag)
        if ordered_nodes is None:
            msg = "Unable to derive deterministic execution ordering."
            raise ValueError(msg)

        hdr_bundle: list[HDR] = []
        previous_chain: str | None = None
        denom = max(len(ordered_nodes), 1)
        authorized = list(plan.authorized_agent_ids)

        plan.hdrs_generated = []

        for node in ordered_nodes:
            hdr = await self.execute_node(
                node=node,
                previous_hdr_id=previous_chain,
                mission_id=mid,
                plan_description=plan.description,
                chunk_cost=plan.estimated_cost_gas / denom,
                authorized_tools=authorized,
                organization_id=plan.organization_id,
            )
            hdr_bundle.append(hdr)
            previous_chain = hdr.hdr_id
            plan.hdrs_generated.append(hdr.hdr_id)

        return hdr_bundle

    async def execute_node(
        self,
        node: DAGNode,
        previous_hdr_id: str | None,
        mission_id: str,
        *,
        plan_description: str,
        chunk_cost: float,
        authorized_tools: list[str],
        organization_id: str | None = None,
        context: dict | None = None,
    ) -> HDR:
        """Execute DAG nodes via configured executors, minting cryptographic HDR artefacts."""

        tenant = organization_id or "org_default"

        action_gate = self._normative.check_action(
            "stub_execute",
            {
                "authorized_tools": authorized_tools,
                "requested_tool": node.agent_id,
                "human_approved": False,
            },
        )

        definition = self._agent_registry.get_definition(node.agent_id) or synthetic_definition(
            node.agent_id,
        )

        executor = None
        cfg_service = getattr(self, "_agent_cfg", None)
        if cfg_service is not None:
            executor = cfg_service.resolve_executor(node.agent_id, tenant)
        if executor is None:
            executor = self._agent_registry.resolve_executor(node.agent_id)
        if executor is None:
            msg = (
                "Executor wiring incomplete — populate ``AgentRegistry.fallback_executor`` "
                "or register explicit EASY workers."
            )
            raise ValueError(msg)

        if not action_gate.allowed:
            msg = f"Normative firewall blocked EASY node `{node.node_id}` execution."
            raise ValueError(msg)

        if cfg_service is not None:
            model_label, version_label = cfg_service.effective_hdr_agent(definition, node.agent_id, tenant)
        else:
            model_label, version_label = definition.model, definition.version

        hdr_agent = HDRAgent(
            id=definition.agent_id,
            model=model_label,
            version=version_label,
        )
        user = HDRUser(id="easy_orchestration_stub")

        outcome = await executor.execute(
            node=node,
            mission_id=mission_id,
            plan_description=plan_description,
            chunk_cost=chunk_cost,
            authorized_tools=authorized_tools,
            context=context,
        )

        intent = HDRIntent(
            description=f"{plan_description[:512]} ▸ {node.description}",
            tools_required=[node.agent_id],
            estimated_cost_gas=max(chunk_cost, 0.0),
        )

        exec_status = outcome.execution_status
        if exec_status not in {"completed", "failed", "aborted"}:
            exec_status = "completed"

        execution = HDRExecution(
            status=exec_status,
            input_hash=outcome.input_hash_hex or generate_hash(node.node_id.encode("utf-8")),
            output_hash=outcome.output_hash_hex,
            duration_ms=outcome.duration_ms,
        )

        cognitive_snapshot = HDRCognitiveSnapshot(
            hypothesis=outcome.cognitive_hypothesis,
            action=outcome.cognitive_action,
            result=outcome.cognitive_result,
        )

        normative_bundle = HDRNormative(
            checked=True,
            violations=[],
            corpus_version="v1_normative_default",
        )

        hdr_kind = self._hdr_type_for(node.agent_id)

        return self._hdr.generate_hdr(
            hdr_type=hdr_kind,
            mission_id=mission_id,
            agent=hdr_agent,
            user=user,
            intent=intent,
            execution=execution,
            cognitive_snapshot=cognitive_snapshot,
            normative=normative_bundle,
            previous_hdr=previous_hdr_id,
        )

    def _ordered_agent_selection(self, description: str, available_agent_ids: list[str]) -> list[str]:
        """Return sanctioned agents respecting first occurrence ordering within briefing prose."""

        if not available_agent_ids:
            return []

        folded = description.casefold()
        allowed = set(available_agent_ids)

        positional_hits: list[tuple[int, int, str]] = []
        for keyword, agent_id in KEYWORD_AGENT_MAP.items():
            if agent_id not in allowed:
                continue
            needle = keyword.casefold()
            cursor = 0
            while True:
                idx = folded.find(needle, cursor)
                if idx == -1:
                    break
                positional_hits.append((idx, len(needle), agent_id))
                cursor = idx + len(needle)

        positional_hits.sort(key=lambda item: (item[0], item[1], item[2]))
        selections: list[str] = []

        for _idx, _span, agent in positional_hits:
            if agent not in selections:
                selections.append(agent)

        return selections if selections else [available_agent_ids[0]]

    @staticmethod
    def _build_linear_dag(agent_ids: list[str], briefing: str) -> DAG:
        """Construct deterministic linear DAG mirroring sequential EASY phases."""

        if not agent_ids:
            return DAG(nodes=[], edges=[])

        snippet = f"{briefing[:96]}…" if len(briefing) > 96 else briefing

        nodes: list[DAGNode] = []
        edges: list[tuple[str, str]] = []

        prev_id: str | None = None

        for index, agent_id in enumerate(agent_ids, start=1):
            node_id = f"n{index}-{agent_id}"
            depends_on: list[str] = [prev_id] if prev_id else []
            descriptor = (
                f"Auto-generated EASY step leveraging `{agent_id}` for briefing anchored on `{snippet}`."
            )

            nodes.append(
                DAGNode(
                    node_id=node_id,
                    agent_id=agent_id,
                    action="stub_execute",
                    description=descriptor,
                    depends_on=list(depends_on),
                ),
            )

            if prev_id:
                edges.append((prev_id, node_id))
            prev_id = node_id

        return DAG(nodes=nodes, edges=edges)

    @staticmethod
    def _detect_cycles_from_nodes(dag: DAG) -> bool:
        """Detect directed cycles leveraging Kahn traversal over depends_on linkage."""

        node_ids = [node.node_id for node in dag.nodes]
        node_lookup = {node.node_id: node for node in dag.nodes}

        graph: defaultdict[str, list[str]] = defaultdict(list)
        indegree: defaultdict[str, int] = defaultdict(int)

        for node_id in node_ids:
            indegree[node_id]

        for node in dag.nodes:
            indegree[node.node_id] = len(node.depends_on)
            for dependency in node.depends_on:
                graph[dependency].append(node.node_id)

        queue = deque(sorted([nid for nid in indegree if indegree[nid] == 0]))
        processed = 0

        while queue:
            current = queue.popleft()
            processed += 1
            if current not in node_lookup:
                return True

            for neighbor in sorted(graph.get(current, [])):
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        return processed != len(node_ids)

    def _topological_sort(self, *, dag: DAG) -> list[DAGNode] | None:
        """Return stable topological schedule using depends_on prerequisites."""

        if not dag.nodes:
            return []

        graph: defaultdict[str, list[str]] = defaultdict(list)
        indegree: defaultdict[str, int] = defaultdict(int)

        ordering_ids: list[str] = []

        for node in dag.nodes:
            indegree[node.node_id] = len(node.depends_on)
            for dep in node.depends_on:
                graph[dep].append(node.node_id)

        queue = deque(sorted([nid for nid in indegree if indegree[nid] == 0]))
        processed = 0

        while queue:
            current = queue.popleft()
            ordering_ids.append(current)
            processed += 1

            for neighbor in sorted(graph.get(current, [])):
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if processed != len(dag.nodes):
            return None

        node_lookup = {node.node_id: node for node in dag.nodes}
        return [node_lookup[nid] for nid in ordering_ids]
