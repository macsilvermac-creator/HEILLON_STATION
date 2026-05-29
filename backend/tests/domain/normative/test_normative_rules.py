"""Corpus Normativo adjudication regressions."""

from __future__ import annotations


def test_load_default_rules(normative_service):
    rules = normative_service.get_active_rules()
    assert len(rules) == 10
    assert any(rule.rule_id == "LEGAL-001" for rule in rules)


def test_block_privileged_access(normative_service):
    result = normative_service.check_intent(
        "Access privileged documents for review",
        {"authorized_tools": ["analysis-agent"], "estimated_cost_gas": 5.0},
    )
    assert result.allowed is False
    assert any(
        "privileged" in violation.reason.casefold() for violation in result.violations
    )


def test_allow_normal_analysis(normative_service):
    result = normative_service.check_intent(
        "Analyze financial documents for risk",
        {
            "authorized_tools": ["analysis-agent", "ocr-agent"],
            "estimated_cost_gas": 10.0,
        },
    )
    assert result.allowed is True
    assert len(result.violations) == 0


def test_realign_external_action(normative_service):
    result = normative_service.check_action("send_external", {"human_approved": False})
    assert result.allowed is False
    assert result.suggested_realignment is not None


def test_block_outside_scope(normative_service):
    result = normative_service.check_intent(
        "Hack into the mainframe",
        {"authorized_tools": ["ocr-agent"], "estimated_cost_gas": 15.0},
    )
    assert result.allowed is False
