"""Orchestration engine deterministic planning tests."""

from __future__ import annotations

from app.domain.mission.models import MissionStatus


def test_plan_simple_mission(orchestration_engine):
    plan = orchestration_engine.plan_mission(
        "Analyze these documents for fraud",
        ["analysis-agent"],
    )

    assert plan.status == MissionStatus.PENDING
    assert plan.normative_result is not None
    assert plan.normative_result.allowed is True
    assert len(plan.dag.nodes) > 0


def test_plan_multi_step_mission(orchestration_engine):
    plan = orchestration_engine.plan_mission(
        "OCR these documents, then classify them, then analyze for risk",
        ["ocr-agent", "classification-agent", "analysis-agent"],
    )

    assert len(plan.dag.nodes) == 3

    roots = [node for node in plan.dag.nodes if not node.depends_on]
    assert len(roots) == 1

    for node in plan.dag.nodes:
        if node.node_id != roots[0].node_id:
            assert len(node.depends_on) == 1

    assert len(plan.dag.edges) == len(plan.dag.nodes) - 1


def test_dag_no_cycles(orchestration_engine):
    plan = orchestration_engine.plan_mission(
        "Analyze documents for risk and prioritize by relevance",
        ["analysis-agent", "prioritization-agent"],
    )

    assert orchestration_engine.validate_dag(plan.dag) is True


def test_execute_mission(orchestration_engine):
    plan = orchestration_engine.plan_mission(
        "OCR and analyze documents",
        ["ocr-agent", "analysis-agent"],
    )
    plan.status = MissionStatus.APPROVED

    hdrs = orchestration_engine.execute_mission(plan)

    assert len(hdrs) == 2
    assert hdrs[0].previous_hdr is None
    assert hdrs[1].previous_hdr == hdrs[0].hdr_id
