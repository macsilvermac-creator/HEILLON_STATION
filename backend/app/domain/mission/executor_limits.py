"""Shared truncation ceilings for mission cognition executors.

Previously the Anthropic executor clipped prompts at 120_000 chars while the
OpenAI-compatible executor clipped at 12_000 — a 10x asymmetry that silently
inflated token spend on the Anthropic path and produced divergent cognition
for the same node depending on which provider served it. Both executors now
share a single ceiling so behaviour and cost are provider-independent.

The unified prompt ceiling (24_000 chars ≈ 6k tokens) is a deliberate middle
ground: well below the old Anthropic figure (≈5x token reduction on that path)
yet generous enough that realistic mission payloads — whose free-form parts are
already bounded (``plan_excerpt`` capped at 800 chars, node fields modest) — are
never truncated in practice. The cap acts as a safety ceiling against
pathological inputs, not a routine clip.
"""

from __future__ import annotations

# Maximum characters of the serialized prompt forwarded to a provider.
MISSION_PROMPT_MAX_CHARS = 24_000

# Maximum characters retained from a provider's textual result/summary when
# persisted into the HDR-bound execution outcome.
MISSION_RESULT_MAX_CHARS = 12_000

# Hard cap on completion tokens requested from a provider. Keeps EASY
# cognition outputs compact (compact JSON: hypothesis/summary/confidence) and
# bounds output-token spend.
MISSION_MAX_COMPLETION_TOKENS = 1_024
