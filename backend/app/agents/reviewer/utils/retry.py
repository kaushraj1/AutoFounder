"""Node retry decorator for the Reviewer graph.

Mirrors ``app.agents.strategy.utils.retry`` but threads ``ReviewerState`` and
records an SLA flag on the ``NodeTrace``. A node that exhausts its retries
returns ``{node_traces:[trace], error_count: 1}`` (never raises) so the graph's
routers can decide whether to escalate via ``error_handler``.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol

from app.agents.reviewer.schema import NodeStatus, NodeTrace, ReviewerState
from app.agents.reviewer.utils.sla import track_sla

logger = logging.getLogger("app.agents.reviewer.retry")

# Per-node SLA budgets in seconds (plan §3.4). Default applies to unlisted nodes.
_NODE_BUDGETS: dict[str, float] = {
    "run_linters": 60.0,
    "run_unit_tests": 180.0,
    "run_e2e_tests": 300.0,
    "run_security_scan": 120.0,
    "run_sonarqube": 120.0,
    "llm_judge": 60.0,
    "triage_failures": 30.0,
}
_DEFAULT_BUDGET = 60.0


def _node_budget(node: str) -> float:
    return _NODE_BUDGETS.get(node, _DEFAULT_BUDGET)


class NodeFn(Protocol):
    """A graph node: ``async (state, agent) -> partial state dict``."""

    async def __call__(self, state: ReviewerState, agent: Any) -> dict[str, Any]: ...


def with_retry(node_name: str) -> Callable[[NodeFn], NodeFn]:
    """Wrap a node with the graph's retry policy + NodeTrace bookkeeping."""

    def decorator(fn: NodeFn) -> NodeFn:
        @functools.wraps(fn)
        async def wrapper(state: ReviewerState, agent: Any) -> dict[str, Any]:
            policy = state.retry_policy
            trace = NodeTrace(
                node=node_name, status=NodeStatus.RUNNING, started_at=datetime.now(UTC)
            )
            last_exc: Exception | None = None

            tenant = getattr(state, "organization_id", "unknown")
            budget = _node_budget(node_name)
            for attempt in range(policy.max_retries + 1):
                trace.retry_count = attempt
                try:
                    async with track_sla(node_name, budget, tenant=tenant) as probe:
                        result = await fn(state, agent)
                    trace.sla_breached = probe.breached
                    trace.status = NodeStatus.COMPLETED
                    trace.completed_at = datetime.now(UTC)
                    return {**result, "node_traces": [trace]}
                except Exception as exc:  # noqa: BLE001 - node faults are recorded, not raised
                    last_exc = exc
                    logger.warning(
                        "Node %s attempt %d/%d failed: %s",
                        node_name,
                        attempt + 1,
                        policy.max_retries + 1,
                        exc,
                    )
                    if attempt < policy.max_retries:
                        sleep_s = policy.backoff_seconds[
                            min(attempt, len(policy.backoff_seconds) - 1)
                        ]
                        await asyncio.sleep(sleep_s)

            trace.status = NodeStatus.FAILED
            trace.error = str(last_exc)
            trace.completed_at = datetime.now(UTC)
            return {"node_traces": [trace], "error_count": 1}

        return wrapper

    return decorator
