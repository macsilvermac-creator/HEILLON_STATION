"""Agent registry regressions guarding fallback executors."""

from __future__ import annotations

import asyncio

from app.domain.mission.models import DAGNode


def test_registry_fallback_handles_unknown_catalog_ids(orchestration_engine):
    node = DAGNode(
        node_id="n-discovery",
        agent_id="novelty-discovery-agent",
        action="stub_execute",
        description="Synthetic worker absent from EASY catalogue imports.",
        input_schema={"mode": "test"},
        depends_on=[],
    )

    hdr = asyncio.run(
        orchestration_engine.execute_node(
            node,
            previous_hdr_id=None,
            mission_id="mission_registry_probe",
            plan_description="Registry fallback probe",
            chunk_cost=7.25,
            authorized_tools=["novelty-discovery-agent"],
            context={"origin": "pytest"},
        )
    )

    assert hdr.agent.id == "novelty-discovery-agent"
    assert hdr.execution.status == "completed"
    assert len(hdr.execution.input_hash) == 64
