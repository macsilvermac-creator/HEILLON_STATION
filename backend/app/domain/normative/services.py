"""Normative Corpus service acting as deterministic governance firewall before EASY."""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.mission.lexicon import KEYWORD_AGENT_MAP, SECURITY_SCOPE_MARKERS
from app.domain.normative.models import (
    NormativeCategory,
    NormativeResult,
    NormativeRule,
    NormativeViolation,
    ViolationAction,
)
from app.domain.normative.repository import NormativeRepository

DEFAULT_LEGAL_RULES: tuple[NormativeRule, ...] = (
    NormativeRule(
        rule_id="LEGAL-001",
        name="Block Privileged Access",
        description=(
            "Prevent access to documents tagged as privileged/confidential attorney-client communication"
        ),
        category=NormativeCategory.LEGAL,
        condition=(
            "Intent or action involves accessing documents with tag 'privileged' or 'attorney-client'"
        ),
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="LEGAL-002",
        name="Block PII Without Anonymization",
        description=(
            "Block processing of personal data if anonymization is not explicitly enabled in context"
        ),
        category=NormativeCategory.LEGAL,
        condition="Processing documents containing PII without anonymization flag set to true",
        action_on_violation=ViolationAction.BLOCK,
        priority=95,
    ),
    NormativeRule(
        rule_id="LEGAL-003",
        name="Require Human Approval for External Actions",
        description="External communications (publish, send, share) must have human approval recorded",
        category=NormativeCategory.COMPLIANCE,
        condition="Action touches external publication channels without judiciary approval artefacts",
        action_on_violation=ViolationAction.REALIGN,
        priority=90,
    ),
    NormativeRule(
        rule_id="LEGAL-004",
        name="Block Actions Outside Authorized Scope",
        description="Block intents inferring toolchain outside the sanctioned authorized_tools catalog",
        category=NormativeCategory.SECURITY,
        condition="Requested tool/agent is absent from context.authorized_tools payload",
        action_on_violation=ViolationAction.BLOCK,
        priority=85,
    ),
    NormativeRule(
        rule_id="LEGAL-005",
        name="Warn on High Cost",
        description="Issue advisory warning when estimated mission cost exceeds guardrail threshold",
        category=NormativeCategory.CUSTOM,
        condition="estimated_cost_gas > 100",
        action_on_violation=ViolationAction.WARN,
        priority=10,
    ),
    NormativeRule(
        rule_id="LGPD-001",
        name="Block PII Processing Without Legal Basis",
        description="Block processing of personal data if no legal basis is declared in the intent context",
        category=NormativeCategory.LEGAL,
        condition="Intent involves personal data and no legal_basis is declared in context",
        action_on_violation=ViolationAction.REALIGN,
        priority=98,
    ),
    NormativeRule(
        rule_id="LGPD-002",
        name="Block Cross-Border Transfer Without Safeguards",
        description="Block cross-border data transfers unless adequate safeguards are documented",
        category=NormativeCategory.LEGAL,
        condition="Intent involves cross-border transfer and no safeguards in context",
        action_on_violation=ViolationAction.BLOCK,
        priority=96,
    ),
    NormativeRule(
        rule_id="LGPD-003",
        name="Require Data Minimization Check",
        description="Warn when processing more data fields than declared necessary",
        category=NormativeCategory.LEGAL,
        condition="input_field_count exceeds necessary_fields threshold",
        action_on_violation=ViolationAction.WARN,
        priority=85,
    ),
    NormativeRule(
        rule_id="LGPD-004",
        name="Block Processing of Sensitive Data Without Explicit Consent",
        description="Block processing of sensitive personal data without explicit consent flag",
        category=NormativeCategory.LEGAL,
        condition="Intent involves sensitive categories and explicit_consent not in context",
        action_on_violation=ViolationAction.BLOCK,
        priority=100,
    ),
    NormativeRule(
        rule_id="LGPD-005",
        name="Require Data Retention Policy",
        description="Require a data retention period to be specified when storing personal data",
        category=NormativeCategory.COMPLIANCE,
        condition="Action is store/archive and no retention_period in context",
        action_on_violation=ViolationAction.REALIGN,
        priority=75,
    ),
)

EXTERNAL_ACTIONS = {"publish", "send_external", "share"}


class NormativeService:
    """Validates intentions and actions against the frozen Corpus Normativo."""

    def __init__(
        self,
        rules: Sequence[NormativeRule] | None = None,
        *,
        repository: NormativeRepository | None = None,
    ) -> None:
        if repository is not None and rules is not None:
            msg = "Provide either repository or legacy rules tuple, never both."
            raise ValueError(msg)
        if repository is not None:
            self._repository = repository
        else:
            seeded = list(rules) if rules is not None else list(DEFAULT_LEGAL_RULES)
            self._repository = NormativeRepository(seeded)

    def add_rule(self, rule: NormativeRule) -> None:
        """Append a rule to the active corpus."""

        self._repository.add_rule(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by identifier if present."""

        return self._repository.remove_rule(rule_id)

    def get_active_rules(self) -> list[NormativeRule]:
        """Return enabled rules ordered by descending priority."""

        return sorted(
            (r for r in self._repository.list_all() if r.enabled),
            key=lambda r: r.priority,
            reverse=True,
        )

    @staticmethod
    def _infer_agents_from_intent(description: str) -> set[str]:
        """Infer candidate agent identifiers using MVP keyword heuristics."""

        folded = description.casefold()
        inferred: set[str] = set()
        for keyword, agent_id in KEYWORD_AGENT_MAP.items():
            if keyword.casefold() in folded:
                inferred.add(agent_id)
        return inferred

    def check_intent(
        self, intent_description: str, context: dict[str, object]
    ) -> NormativeResult:
        """Audit a natural-language intent prior to DAG materialization."""

        violations: list[NormativeViolation] = []
        warnings: list[NormativeViolation] = []
        suggested_realignment: str | None = None
        folded = intent_description.casefold()

        authorized_raw = context.get("authorized_tools", [])
        authorized_tools = (
            {str(x) for x in authorized_raw}
            if isinstance(authorized_raw, list)
            else set()
        )
        inferred_agents = self._infer_agents_from_intent(intent_description)

        for rule in self.get_active_rules():
            if rule.rule_id == "LEGAL-001":
                markers = (
                    "privileged",
                    "attorney-client",
                    "advogado-cliente",
                    "segredo profissional",
                )
                if any(token in folded for token in markers):
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="Intent references privileged or attorney-client material.",
                    )
                    self._accumulate(rule, entry, violations, warnings)

            elif rule.rule_id == "LEGAL-002":
                pii_tokens = (
                    "pii",
                    "personal data",
                    "gdpr",
                    "dados pessoais",
                    "dado pessoal",
                )
                mentions_pii = any(token in folded for token in pii_tokens)
                anonymized = bool(context.get("anonymization"))
                if mentions_pii and not anonymized:
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="PII identifiers detected without court-approved anonymization controls.",
                    )
                    self._accumulate(rule, entry, violations, warnings)

            elif rule.rule_id == "LEGAL-003":
                mentions_external_launch = any(
                    marker in folded
                    for marker in (
                        "publish",
                        "send_external",
                        "share publicly",
                        "publicar externamente",
                    )
                )
                human_ok = bool(context.get("human_approved"))
                if mentions_external_launch and not human_ok:
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="Outbound publication requires supervising counsel approval.",
                    )
                    self._accumulate(rule, entry, violations, warnings)
                    if rule.action_on_violation == ViolationAction.REALIGN:
                        suggested_realignment = (
                            "Route mission through supervising counsel workstation and capture dual-control "
                            "human_approved=True token before egress."
                        )

            elif rule.rule_id == "LEGAL-004":
                if any(marker in folded for marker in SECURITY_SCOPE_MARKERS):
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="Intent references offensive or out-of-band infrastructure actions.",
                    )
                    self._accumulate(rule, entry, violations, warnings)
                elif inferred_agents and not inferred_agents.issubset(authorized_tools):
                    offenders = ", ".join(sorted(inferred_agents - authorized_tools))
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason=f"Inferred toolchain includes unauthorized agents: {offenders}.",
                    )
                    self._accumulate(rule, entry, violations, warnings)

            elif rule.rule_id == "LEGAL-005":
                cost_value = context.get("estimated_cost_gas")
                if isinstance(cost_value, (int, float)) and float(cost_value) > 100:
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason=f"Estimated metering {float(cost_value)} exceeds advisory threshold 100.",
                    )
                    self._accumulate(rule, entry, violations, warnings)

            elif rule.rule_id == "LGPD-001":
                mentions_personal = any(
                    token in folded
                    for token in (
                        "dados pessoais",
                        "dado pessoal",
                        "pii",
                        "personal data",
                    )
                )
                if mentions_personal and not context.get("legal_basis"):
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="LGPD: tratamento de dados pessoais sem legal_basis declarada no contexto.",
                    )
                    self._accumulate(rule, entry, violations, warnings)

            elif rule.rule_id == "LGPD-002":
                mentions_transfer = any(
                    token in folded
                    for token in (
                        "transferência internacional",
                        "transferencia internacional",
                        "cross-border",
                        "international transfer",
                    )
                )
                if mentions_transfer and not context.get("safeguards"):
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="LGPD: transferência transfronteiriça sem salvaguardas documentadas.",
                    )
                    self._accumulate(rule, entry, violations, warnings)

            elif rule.rule_id == "LGPD-003":
                necessary = context.get("necessary_fields")
                icount = context.get("input_field_count")
                if isinstance(necessary, (int, float)) and isinstance(
                    icount, (int, float)
                ):
                    if float(icount) > 2 * float(necessary):
                        entry = NormativeViolation(
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            reason="LGPD: volume de campos acima do mínimo necessário declarado.",
                        )
                        self._accumulate(rule, entry, violations, warnings)

            elif rule.rule_id == "LGPD-004":
                mentions_sensitive = any(
                    token in folded
                    for token in (
                        "dados sensíveis",
                        "dados sensiveis",
                        "sensitive personal",
                        "health data",
                    )
                )
                if mentions_sensitive and not context.get("explicit_consent"):
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="LGPD: dados sensíveis sem explicit_consent no contexto.",
                    )
                    self._accumulate(rule, entry, violations, warnings)

            elif rule.rule_id == "LGPD-005":
                mentions_storage = any(
                    token in folded
                    for token in (
                        "armazenar",
                        "arquivo",
                        "store",
                        "archive",
                        "retenção",
                        "retention",
                    )
                )
                mentions_personal = any(
                    token in folded
                    for token in ("dados pessoais", "pii", "personal data")
                )
                if (
                    mentions_storage
                    and mentions_personal
                    and not context.get("retention_period")
                ):
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="LGPD: armazenamento de dados pessoais sem retention_period.",
                    )
                    self._accumulate(rule, entry, violations, warnings)

        hard_blocks = {"LEGAL-001", "LEGAL-002", "LEGAL-004", "LGPD-002", "LGPD-004"}
        realign_ids = {"LEGAL-003", "LGPD-001", "LGPD-005"}
        blocking = any(v.rule_id in hard_blocks for v in violations)
        realign_blocks = any(v.rule_id in realign_ids for v in violations)
        allowed = not blocking and not realign_blocks

        return NormativeResult(
            allowed=allowed,
            violations=violations,
            warnings=warnings,
            suggested_realignment=suggested_realignment,
        )

    def check_action(
        self, action: str, hdr_context: dict[str, object]
    ) -> NormativeResult:
        """Inspect atomic actions during DAG execution for additional guarantees."""

        violations: list[NormativeViolation] = []
        warnings: list[NormativeViolation] = []
        suggested_realignment: str | None = None
        action_key = action.strip().lower()

        authorized_raw = hdr_context.get("authorized_tools", [])
        authorized_tools = (
            {str(x) for x in authorized_raw}
            if isinstance(authorized_raw, list)
            else set()
        )

        for rule in self.get_active_rules():
            if rule.rule_id == "LEGAL-003":
                if action_key in EXTERNAL_ACTIONS and not bool(
                    hdr_context.get("human_approved")
                ):
                    entry = NormativeViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        reason="External-facing action attempted without recorded human approval.",
                    )
                    self._accumulate(rule, entry, violations, warnings)
                    suggested_realignment = "Obtain partner-level approval and persist human_approved=True before retrying."

            elif rule.rule_id == "LEGAL-004":
                tool_candidate = hdr_context.get("requested_tool")
                if isinstance(tool_candidate, str):
                    mapped = KEYWORD_AGENT_MAP.get(tool_candidate.casefold())
                    inferred = mapped or tool_candidate
                    if inferred and inferred not in authorized_tools:
                        entry = NormativeViolation(
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            reason=f"Requested tool `{inferred}` not present in sanctioned manifest.",
                        )
                        self._accumulate(rule, entry, violations, warnings)

        blocking = [
            v
            for v in violations
            if v.rule_id in {"LEGAL-001", "LEGAL-002", "LEGAL-004"}
        ]
        allowed = len(blocking) == 0 and not any(
            v.rule_id == "LEGAL-003" for v in violations
        )

        return NormativeResult(
            allowed=allowed,
            violations=violations,
            warnings=warnings,
            suggested_realignment=suggested_realignment,
        )

    @staticmethod
    def _accumulate(
        rule: NormativeRule,
        entry: NormativeViolation,
        violations: list[NormativeViolation],
        warnings: list[NormativeViolation],
    ) -> None:
        """Route severity buckets according to adjudication modality."""

        if rule.action_on_violation == ViolationAction.WARN:
            warnings.append(entry)
            return

        violations.append(entry)
