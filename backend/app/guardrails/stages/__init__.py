"""The six guardrail stages (AF-046).

Policy -> Input -> Instruction (before LLM) · Execution (around tools) ·
Output -> Monitoring (after LLM). Each exposes a pure ``check``/``observe``
function over a ``GuardrailContext`` so it is independently unit-testable.
"""

from app.guardrails.stages import (
    execution_guard,
    input_guard,
    instruction_guard,
    monitoring,
    output_guard,
    policy,
)

__all__ = [
    "policy",
    "input_guard",
    "instruction_guard",
    "execution_guard",
    "output_guard",
    "monitoring",
    "reset_guardrail_state",
]


def reset_guardrail_state() -> None:
    """Reset all in-process stage ledgers (rate, cost, strikes, drift baselines)."""
    execution_guard.reset_state()
    output_guard.reset_state()
    monitoring.reset_state()
