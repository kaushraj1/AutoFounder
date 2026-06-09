"""6-stage guardrail pipeline (AF-046).

Public surface: the ``GuardrailPipeline`` wrapper (before_llm / around_tool /
after_llm), the ``GuardResult`` / ``LineageRecord`` contracts, the per-call
``GuardrailContext``, and the reused ``check_opa_policy`` helper.
"""

from app.guardrails.opa import check_opa_policy
from app.guardrails.pipeline import GuardrailBlocked, GuardrailPipeline
from app.guardrails.schema import (
    STAGE_ORDER,
    GuardDecision,
    GuardrailContext,
    GuardrailStage,
    GuardResult,
    GuardSeverity,
    LineageRecord,
)

__all__ = [
    "STAGE_ORDER",
    "GuardrailPipeline",
    "GuardrailBlocked",
    "GuardrailStage",
    "GuardResult",
    "GuardSeverity",
    "GuardDecision",
    "GuardrailContext",
    "LineageRecord",
    "check_opa_policy",
]
