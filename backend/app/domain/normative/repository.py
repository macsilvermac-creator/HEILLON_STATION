"""Normative Corpus persistence (in-memory until dedicated norms DDL ships)."""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.normative.models import NormativeRule


class NormativeRepository:
    """Holds adjudication rules surfaced by ``NormativeService``."""

    def __init__(self, rules: Sequence[NormativeRule] | None = None) -> None:
        self._rules: list[NormativeRule] = list(rules) if rules is not None else []

    def list_all(self) -> list[NormativeRule]:
        """Return authoritative mutable snapshot backing services."""

        return list(self._rules)

    def add_rule(self, rule: NormativeRule) -> None:
        """Persist an additional juridical statute."""

        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove statutes by courthouse identifier."""

        before = len(self._rules)
        self._rules = [r for r in self._rules if r.rule_id != rule_id]
        return len(self._rules) < before
