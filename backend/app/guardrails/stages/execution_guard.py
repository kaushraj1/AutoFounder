"""Stage 4 — Execution Guard (AF-046), wraps every tool call.

Reads the shared Tool Registry (AF-047) to enforce, per call:
  * allow-list  — the tool must be registered (and in ctx.allowed_tools if set)
  * schema      — args must satisfy the tool's args_schema
  * auth scope  — caller scopes must include the tool's required scope
  * rate limit  — per-tenant calls/minute
  * cost cap     — per-tenant accumulated estimated spend

Fails *closed*: any violation blocks the tool call.

The rate-limit and cost ledgers are in-process (precise float accounting). A
Redis-backed cross-instance accumulator (``guard:cost:{org}``) is the Phase-2
wiring; ``ctx.cache`` is reserved for it.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.guardrails.metrics import GUARDRAIL_COST_CAP_BLOCKS
from app.guardrails.schema import GuardrailContext, GuardrailStage, GuardResult, GuardSeverity
from app.tools.errors import ToolValidationError
from app.tools.registry import ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)

# In-process ledgers (reset_state() clears them for test isolation).
_RATE: dict[tuple[str, str, int], int] = {}
_COST: dict[tuple[str, str], float] = {}


def reset_state() -> None:
    """Clear the in-process rate-limit and cost ledgers (test isolation)."""
    _RATE.clear()
    _COST.clear()


def _bump_rate(org_id: str, tool: str) -> int:
    minute = int(time.time() // 60)
    key = (org_id, tool, minute)
    _RATE[key] = _RATE.get(key, 0) + 1
    return _RATE[key]


def _accumulate_cost(org_id: str, est_usd: float) -> float:
    day = datetime.now(UTC).date().isoformat()
    key = (org_id, day)
    _COST[key] = _COST.get(key, 0.0) + est_usd
    return _COST[key]


def check(
    ctx: GuardrailContext,
    tool_call: dict[str, Any],
    *,
    registry: ToolRegistry | None = None,
) -> GuardResult:
    """Authorize a single tool call against the registry + tenant budgets."""
    reg = registry or get_tool_registry()
    name = tool_call.get("name") or tool_call.get("tool")
    args = tool_call.get("args") or {}

    if not isinstance(name, str) or not name:
        return GuardResult.block(
            GuardrailStage.execution, "Tool call missing a tool name", severity=GuardSeverity.WARN
        )

    # Allow-list: must be a registered tool.
    if not reg.has(name):
        return GuardResult.block(
            GuardrailStage.execution,
            f"Tool '{name}' is not in the registry allow-list",
            severity=GuardSeverity.CRITICAL,
            flags=["unregistered_tool"],
        )
    # Per-call allow-list (when the run scopes tools).
    if ctx.allowed_tools is not None and name not in ctx.allowed_tools:
        return GuardResult.block(
            GuardrailStage.execution,
            f"Tool '{name}' is not allowed for this run",
            severity=GuardSeverity.CRITICAL,
            flags=["tool_not_allowed"],
        )

    spec = reg.get(name)

    # Schema.
    try:
        reg.validate_args(spec, args if isinstance(args, dict) else {})
    except ToolValidationError as exc:
        return GuardResult.block(
            GuardrailStage.execution,
            f"Tool '{name}' args failed validation: {exc.message}",
            severity=GuardSeverity.CRITICAL,
            flags=["schema_invalid"],
        )

    # Auth scope (defense-in-depth; skipped when no caller scopes are known).
    if spec.auth_scope and ctx.scopes and spec.auth_scope not in ctx.scopes:
        return GuardResult.block(
            GuardrailStage.execution,
            f"Tool '{name}' requires scope '{spec.auth_scope}'",
            severity=GuardSeverity.CRITICAL,
            flags=["scope_denied"],
        )

    # Rate limit.
    if spec.rate_limit_per_min is not None:
        count = _bump_rate(ctx.organization_id, name)
        if count > spec.rate_limit_per_min:
            return GuardResult.block(
                GuardrailStage.execution,
                f"Tool '{name}' rate limit exceeded ({spec.rate_limit_per_min}/min)",
                severity=GuardSeverity.WARN,
                flags=["rate_limited"],
            )

    # Cost cap.
    est = spec.cost_class.estimated_usd
    if ctx.cost_cap_usd is not None and est > 0:
        total = _accumulate_cost(ctx.organization_id, est)
        if total > ctx.cost_cap_usd:
            GUARDRAIL_COST_CAP_BLOCKS.labels(tenant=ctx.organization_id).inc()
            return GuardResult.block(
                GuardrailStage.execution,
                f"Tool '{name}' would exceed cost cap (${total:.4f} > ${ctx.cost_cap_usd:.4f})",
                severity=GuardSeverity.WARN,
                flags=["cost_cap_exceeded"],
            )

    return GuardResult.ok(GuardrailStage.execution, {"name": name, "args": args})
