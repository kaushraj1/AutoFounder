"""Stage 3 — Instruction Guard (AF-046).

Cheap, deterministic validation of the system prompt / constraints handed to the
model: bounded length, no smuggled role-injection markers, no attempt to
override the platform's standing instructions. Fails *closed*.
"""

from __future__ import annotations

import re
from typing import Any

from app.guardrails.schema import GuardrailContext, GuardrailStage, GuardResult, GuardSeverity

_MAX_INSTRUCTION_CHARS = 20_000

# Role-confusion / smuggled-turn markers that should never appear inside a
# system prompt (they indicate an attempt to fake a conversation).
_ROLE_INJECTION = re.compile(r"(?im)^\s*(?:system|assistant|user)\s*:\s|<\|im_start\|>|\[/?INST\]")

_OVERRIDE = re.compile(
    r"(?i)(?:ignore|disregard|override)\s+(?:all\s+|the\s+|your\s+)?"
    r"(?:(?:previous|prior|above|system|standing)\s+){1,3}(?:instructions?|prompt|rules?)"
)


def check(ctx: GuardrailContext, payload: dict[str, Any]) -> GuardResult:
    """Validate the system prompt / instruction block. Absent => clean pass."""
    instruction = payload.get("system_prompt") or payload.get("instruction")
    if not isinstance(instruction, str) or not instruction.strip():
        return GuardResult.ok(GuardrailStage.instruction, payload)

    if len(instruction) > _MAX_INSTRUCTION_CHARS:
        return GuardResult.block(
            GuardrailStage.instruction,
            f"Instruction exceeds {_MAX_INSTRUCTION_CHARS} chars (prompt-stuffing risk)",
            severity=GuardSeverity.WARN,
        )

    if _ROLE_INJECTION.search(instruction):
        return GuardResult.block(
            GuardrailStage.instruction,
            "Instruction contains smuggled role/turn markers",
            severity=GuardSeverity.CRITICAL,
            flags=["role_injection"],
        )

    if _OVERRIDE.search(instruction):
        return GuardResult.block(
            GuardrailStage.instruction,
            "Instruction attempts to override standing system rules",
            severity=GuardSeverity.CRITICAL,
            flags=["override_attempt"],
        )

    return GuardResult.ok(GuardrailStage.instruction, payload)
