"""6-stage guardrail pipeline (stub) — see CLAUDE.md §34.

Wraps every agent invocation in order: Policy -> Input -> Instruction -> Execution ->
Output -> Monitoring, with cross-cutting Audit & Lineage. Phase 1 fixes the stage order;
Sprint 1 implements each stage's checks (OPA, Llama Guard, Presidio, citation-check, ...).
"""

from enum import StrEnum


class GuardrailStage(StrEnum):
    """The ordered stages every request passes through."""

    policy = "policy"
    input = "input"
    instruction = "instruction"
    execution = "execution"
    output = "output"
    monitoring = "monitoring"


STAGE_ORDER: tuple[GuardrailStage, ...] = (
    GuardrailStage.policy,
    GuardrailStage.input,
    GuardrailStage.instruction,
    GuardrailStage.execution,
    GuardrailStage.output,
    GuardrailStage.monitoring,
)


class GuardrailPipeline:
    """Runs a payload through all guardrail stages."""

    async def run(self, payload: dict[str, object]) -> dict[str, object]:
        """Validate and (if needed) transform a payload. Returns the safe payload."""
        raise NotImplementedError("Guardrail checks land in Phase 1 Sprint 1")
