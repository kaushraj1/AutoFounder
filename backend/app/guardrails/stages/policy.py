"""Stage 1 — Policy & Rules (AF-046).

Decides allow/deny for the agent call via OPA (RBAC/ABAC). Reuses the existing
``check_opa_policy`` httpx client (AF-029), which already dev-bypasses when the
sidecar is offline and fails closed in production. This stage fails *closed*.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.guardrails.opa import check_opa_policy
from app.guardrails.schema import GuardrailContext, GuardrailStage, GuardResult, GuardSeverity

logger = logging.getLogger(__name__)


async def check(ctx: GuardrailContext, payload: dict[str, Any]) -> GuardResult:
    """Authorize the call. Deny -> blocked CRITICAL; OPA error -> fail closed in prod."""
    action = str(payload.get("action") or "agent.invoke")
    resource = str(payload.get("resource") or ctx.agent_id or "agent")

    try:
        allow, reason = await check_opa_policy(
            organization_id=ctx.organization_id,
            role=ctx.role,
            scopes=ctx.scopes,
            action=action,
            resource=resource,
        )
    except Exception as exc:  # unexpected — fail closed in prod, open in dev
        if get_settings().is_production:
            logger.error(
                "policy_stage_error org=%s action=%s err=%s", ctx.organization_id, action, exc
            )
            return GuardResult.block(
                GuardrailStage.policy,
                "Policy engine error (failing closed)",
                severity=GuardSeverity.CRITICAL,
            )
        logger.warning("policy_stage_error_dev_bypass action=%s err=%s", action, exc)
        return GuardResult.ok(GuardrailStage.policy, payload)

    if not allow:
        return GuardResult.block(
            GuardrailStage.policy,
            reason or f"Policy denied action '{action}' on '{resource}'",
            severity=GuardSeverity.CRITICAL,
        )
    return GuardResult.ok(GuardrailStage.policy, payload)
