"""Mission planning, DAG, and orchestration artefacts (Phase 2)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.hdr.models import HDR
from app.domain.normative.models import NormativeResult


class MissionStatus(str, Enum):
    """Lifecycle enumerator for EASY missions."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class AgentDefinition(BaseModel):
    """Catalog metadata for attachable EASY workers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_id: str
    name: str
    capabilities: list[str]
    model: str
    version: str


class DAGNode(BaseModel):
    """Single deterministic execution checkpoint inside a DAG."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str
    agent_id: str
    action: str
    description: str
    input_schema: dict[str, object] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class DAG(BaseModel):
    """Directed execution graph with topological constraints."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nodes: list[DAGNode]
    edges: list[tuple[str, str]] = Field(default_factory=list)

    @field_validator("edges", mode="before")
    @classmethod
    def _coerce_edges_to_tuples(cls, value: object) -> list[tuple[str, str]]:
        """Round-trip edges when JSON deserialization yields nested lists."""

        if value is None:
            return []
        if not isinstance(value, list):
            msg = "edges must be a list of pairs"
            raise TypeError(msg)
        pairs: list[tuple[str, str]] = []
        for item in value:
            if isinstance(item, tuple) and len(item) == 2:
                a, b = item
            elif isinstance(item, list) and len(item) == 2:
                a, b = item[0], item[1]
            else:
                msg = "each edge must be a length-2 tuple or list"
                raise ValueError(msg)
            pairs.append((str(a), str(b)))
        return pairs


class MissionPlan(BaseModel):
    """Court-facing mission envelope bridging normative rulings + DAG intents."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    mission_id: str
    description: str
    authorized_agent_ids: list[str] = Field(default_factory=list)
    dag: DAG
    normative_result: NormativeResult | None = None
    status: MissionStatus = MissionStatus.PENDING
    estimated_cost_gas: float = Field(default=0.0, ge=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    completed_at: datetime | None = None
    hdrs_generated: list[str] = Field(default_factory=list)
    organization_id: str = Field(
        default="org_default", description="Tenant scope for dossier lineage."
    )


class PlanMissionRequest(BaseModel):
    """Inbound REST contract for EASY planning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str
    authorized_agents: list[str] = Field(default_factory=list)


class MissionExecutionResult(BaseModel):
    """Post-execution dossier consolidating HDR artefacts."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    mission_id: str
    status: MissionStatus
    hdrs: list[HDR] = Field(default_factory=list)
    chain_root: str | None = None
    chain_tail: str | None = None
    total_hdrs: int = 0


class MissionDiaryResponse(BaseModel):
    """Paged diary envelope for judiciary browsing."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    total: int
    skip: int
    limit: int
    missions: list[MissionPlan]


class AgentFrequency(BaseModel):
    """Agent prevalence analytics."""

    agent_id: str
    count: int


class MissionStats(BaseModel):
    """Aggregation suitable for EASY dashboard tiles."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    total_missions: int = 0
    completed: int = 0
    failed: int = 0
    blocked_by_normative: int = 0
    total_hdrs_generated: int = 0
    avg_execution_time_ms: float = 0.0
    most_used_agents: list[AgentFrequency] = Field(default_factory=list)
