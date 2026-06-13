"""HITL spend gate — wait for founder approval of the AWS spend estimate.

Decision order:
  1. If ``approval_status`` was already set to APPROVED on input (test or
     orchestrator pre-approval), accept and continue.
  2. If ``estimated_monthly_cost_usd <= settings.devops_spend_gate_cap_usd``,
     auto-approve.
  3. Otherwise, poll Redis at
        ``{settings.devops_hitl_redis_key_prefix}:{run_id}``
     every ``devops_hitl_poll_interval_seconds`` for ``approved`` / ``rejected``,
     up to ``devops_hitl_timeout_seconds``. The founder portal / Slack webhook
     writes that value when the human decides.
  4. If Redis is unavailable, mark REJECTED so the graph routes to error_handler
     instead of hanging forever.
  5. If the poll loop times out, mark TIMED_OUT.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from app.agents.devops.schema import ApprovalStatus, NodeStatus, NodeTrace
from app.core.config import get_settings

logger = logging.getLogger("app.agents.devops.nodes.hitl_spend_gate")


def _get_redis_client():  # pragma: no cover - thin wrapper monkeypatched in tests
    from app.db.redis_pool import get_redis

    return get_redis()


async def _poll_redis_for_decision(
    run_id: str,
    redis_key: str,
    poll_interval: float,
    timeout: float,
) -> ApprovalStatus:
    """Poll Redis until a decision lands or the timeout elapses."""
    try:
        redis = _get_redis_client()
    except RuntimeError:
        logger.warning(
            "[devops.hitl] Redis pool not initialized — cannot wait for approval "
            "of run_id=%s; rejecting.",
            run_id,
        )
        return ApprovalStatus.REJECTED

    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        try:
            raw = await redis.get(redis_key)
        except Exception as exc:  # noqa: BLE001 - any Redis error → reject
            logger.warning(
                "[devops.hitl] Redis read failed for %s: %s — rejecting.",
                redis_key,
                exc,
            )
            return ApprovalStatus.REJECTED

        if raw is not None:
            value = (raw if isinstance(raw, str) else raw.decode("utf-8")).strip().lower()
            if value == "approved":
                logger.info("[devops.hitl] founder APPROVED run_id=%s", run_id)
                return ApprovalStatus.APPROVED
            if value == "rejected":
                logger.info("[devops.hitl] founder REJECTED run_id=%s", run_id)
                return ApprovalStatus.REJECTED
            logger.debug(
                "[devops.hitl] unexpected value %r at %s — continuing to poll",
                value,
                redis_key,
            )

        if asyncio.get_event_loop().time() >= deadline:
            logger.warning(
                "[devops.hitl] timed out waiting for approval on run_id=%s after %ss",
                run_id,
                timeout,
            )
            return ApprovalStatus.TIMED_OUT

        await asyncio.sleep(poll_interval)


async def hitl_spend_gate(state: dict) -> dict:
    data = state.model_dump() if hasattr(state, "model_dump") else state
    started_at = datetime.now(UTC)
    settings = get_settings()

    approval_status = data.get("approval_status", ApprovalStatus.PENDING)
    if isinstance(approval_status, str):
        try:
            approval_status = ApprovalStatus(approval_status)
        except ValueError:
            approval_status = ApprovalStatus.PENDING
    approval_comment: str | None = data.get("approval_comment")
    cost = float(data.get("estimated_monthly_cost_usd") or 0.0)
    cap = float(settings.devops_spend_gate_cap_usd)
    run_id = str(data.get("run_id", ""))

    if approval_status == ApprovalStatus.APPROVED:
        approval_comment = approval_comment or "Pre-approved on input"
    elif cost <= cap:
        approval_status = ApprovalStatus.APPROVED
        approval_comment = f"Auto-approved: ${cost:.2f}/mo is at or under the ${cap:.2f}/mo cap"
    else:
        redis_key = f"{settings.devops_hitl_redis_key_prefix}:{run_id}"
        logger.info(
            "[devops.hitl] cost $%.2f/mo > cap $%.2f/mo — waiting on %s",
            cost,
            cap,
            redis_key,
        )
        approval_status = await _poll_redis_for_decision(
            run_id=run_id,
            redis_key=redis_key,
            poll_interval=float(settings.devops_hitl_poll_interval_seconds),
            timeout=float(settings.devops_hitl_timeout_seconds),
        )
        if approval_status == ApprovalStatus.APPROVED:
            approval_comment = f"Founder approved ${cost:.2f}/mo via {redis_key}"
        elif approval_status == ApprovalStatus.REJECTED:
            approval_comment = f"Founder rejected ${cost:.2f}/mo via {redis_key}"
        else:
            approval_comment = (
                f"No decision in {settings.devops_hitl_timeout_seconds}s on {redis_key}"
            )

    completed_at = datetime.now(UTC)
    node_status = (
        NodeStatus.COMPLETED if approval_status == ApprovalStatus.APPROVED else NodeStatus.FAILED
    )
    last_error = (
        None
        if approval_status == ApprovalStatus.APPROVED
        else f"Infra spend gate not approved: {approval_status.value}"
    )

    return {
        "approval_status": approval_status,
        "approval_comment": approval_comment,
        "node_traces": [
            NodeTrace(
                node="hitl_spend_gate",
                status=node_status,
                started_at=started_at,
                completed_at=completed_at,
            )
        ],
        "last_error": last_error,
    }
