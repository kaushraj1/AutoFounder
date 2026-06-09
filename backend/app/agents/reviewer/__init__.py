"""AF-042 Reviewer / Self-Healer Agent (Pillar 4).

Quality-gate + self-healing engine: ingests a generated repo, runs lint / unit /
e2e / security / quality gates inside an ephemeral sandbox, LLM-judges the code,
triages failures, and runs a bounded self-heal loop before approving or
escalating.

Submodules (agent, graph, nodes, tools, registry) are imported lazily by callers
to keep ``from app.agents.reviewer import metrics`` cheap and side-effect-free.
"""

from app.agents.reviewer.schema import (
    MAX_HEAL_CYCLES,
    ReviewDecision,
    ReviewerInput,
    ReviewerOutput,
    ReviewerState,
)

__all__ = [
    "MAX_HEAL_CYCLES",
    "ReviewDecision",
    "ReviewerInput",
    "ReviewerOutput",
    "ReviewerState",
]
