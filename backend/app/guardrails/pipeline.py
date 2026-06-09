"""6-stage guardrail pipeline (AF-046) — see CLAUDE.md §34.

The safety membrane wrapping every agent invocation:
``Policy -> Input -> Instruction`` before the LLM, ``Execution`` around each
tool call, ``Output -> Monitoring`` after generation, with an immutable Audit &
Lineage record emitted for every decision.

Security stages fail *closed* (``blocked=True`` short-circuits the chain);
quality stages fail *open with flags*. Each decision is persisted via
``emit_lineage`` so there are no un-audited agent calls.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.guardrails.audit import emit_lineage
from app.guardrails.metrics import GUARDRAIL_BLOCKS
from app.guardrails.schema import (
    STAGE_ORDER,
    GuardrailContext,
    GuardrailStage,
    GuardResult,
    GuardSeverity,
)
from app.guardrails.stages import (
    execution_guard,
    input_guard,
    instruction_guard,
    monitoring,
    output_guard,
    policy,
)

logger = logging.getLogger(__name__)

__all__ = ["STAGE_ORDER", "GuardrailStage", "GuardrailPipeline", "GuardrailBlocked"]


class GuardrailBlocked(Exception):
    """Raised by the convenience ``run()`` wrapper when a security stage blocks."""

    def __init__(self, result: GuardResult) -> None:
        super().__init__(result.reason or f"Blocked at {result.stage.value} stage")
        self.result = result


class GuardrailPipeline:
    """Wraps every BaseAgent invocation. Fail-closed on security stages.

    Stateless and reusable across calls; per-call identity lives in the
    ``GuardrailContext`` passed to each method.
    """

    async def _record(self, ctx: GuardrailContext, result: GuardResult) -> bool:
        """Emit lineage + count blocks. Returns whether a durable record was written."""
        durable = await emit_lineage(ctx, result)
        if result.blocked:
            GUARDRAIL_BLOCKS.labels(stage=result.stage.value, severity=result.severity.value).inc()
        return durable

    def _audit_block(self, ctx: GuardrailContext, durable: bool, stage: GuardrailStage) -> bool:
        """Apply the 'block on audit failure' policy (CLAUDE.md §34 / plan D3)."""
        settings = get_settings()
        if durable or not getattr(settings, "guardrail_block_on_audit_failure", False):
            return False
        # Configured to block when a durable audit write is required but failed.
        return settings.is_production

    async def before_llm(self, ctx: GuardrailContext, payload: dict[str, Any]) -> GuardResult:
        """Run Policy -> Input -> Instruction. Returns sanitized payload or a block."""
        if not _enabled():
            return GuardResult.ok(GuardrailStage.input, payload)

        current = dict(payload)
        flags: list[str] = []

        # Stage 1 — Policy (async).
        res = await policy.check(ctx, current)
        durable = await self._record(ctx, res)
        if res.blocked or self._audit_block(ctx, durable, GuardrailStage.policy):
            return res if res.blocked else _audit_failure(GuardrailStage.policy)

        # Stage 2 — Input (PII + injection).
        res = input_guard.check(ctx, current)
        await self._record(ctx, res)
        if res.blocked:
            return res
        if res.sanitized_payload is not None:
            current = res.sanitized_payload
        flags.extend(res.flags)

        # Stage 3 — Instruction.
        res = instruction_guard.check(ctx, current)
        await self._record(ctx, res)
        if res.blocked:
            return res
        flags.extend(res.flags)

        return GuardResult(
            stage=GuardrailStage.instruction,
            blocked=False,
            sanitized_payload=current,
            flags=flags,
            severity=GuardSeverity.WARN if flags else GuardSeverity.INFO,
        )

    async def around_tool(self, ctx: GuardrailContext, tool_call: dict[str, Any]) -> GuardResult:
        """Stage 4 — Execution Guard: schema + allow-list + rate + cost per tool call."""
        if not _enabled():
            return GuardResult.ok(GuardrailStage.execution, tool_call)
        res = execution_guard.check(ctx, tool_call)
        await self._record(ctx, res)
        return res

    async def after_llm(self, ctx: GuardrailContext, output: Any) -> GuardResult:
        """Stage 5 + 6 — Output Guard then Monitoring. Open-with-flags (never blocks)."""
        if not _enabled():
            return GuardResult.ok(GuardrailStage.output)

        out_res = output_guard.check(ctx, output)
        await self._record(ctx, out_res)

        mon_res = monitoring.observe(ctx, output)
        await self._record(ctx, mon_res)

        # Merge monitoring flags into the returned output verdict.
        merged_flags = [*out_res.flags, *mon_res.flags]
        return GuardResult(
            stage=GuardrailStage.output,
            blocked=False,
            reason=out_res.reason,
            severity=out_res.severity,
            sanitized_payload=out_res.sanitized_payload,
            flags=merged_flags,
        )

    async def run(
        self, payload: dict[str, Any], ctx: GuardrailContext | None = None
    ) -> dict[str, Any]:
        """Convenience: run the before-LLM chain and return the safe payload.

        Raises ``GuardrailBlocked`` if a security stage denies the call.
        """
        if ctx is None:
            ctx = GuardrailContext(organization_id=str(payload.get("organization_id", "unknown")))
        result = await self.before_llm(ctx, payload)
        if result.blocked:
            raise GuardrailBlocked(result)
        return result.sanitized_payload or payload


def _enabled() -> bool:
    return bool(getattr(get_settings(), "guardrails_enabled", True))


def _audit_failure(stage: GuardrailStage) -> GuardResult:
    GUARDRAIL_BLOCKS.labels(stage=stage.value, severity=GuardSeverity.CRITICAL.value).inc()
    return GuardResult.block(
        stage,
        "Durable audit write failed (failing closed per policy)",
        severity=GuardSeverity.CRITICAL,
        flags=["audit_write_failure"],
    )
