import asyncio
import functools
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from app.agents.strategy.schema import NodeStatus, NodeTrace, StrategistState

logger = logging.getLogger("app.agents.strategy.retry")


def with_retry(node_name: str):
    """
    Decorator that wraps a node function with the graph's retry policy.
    Updates NodeTrace in state on each attempt.
    """

    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(state: StrategistState, agent: Any) -> dict:
            policy = state.retry_policy
            trace = NodeTrace(
                node=node_name, status=NodeStatus.RUNNING, started_at=datetime.now(UTC)
            )
            last_exc = None

            for attempt in range(policy.max_retries + 1):
                trace.retry_count = attempt
                try:
                    result = await fn(state, agent)
                    trace.status = NodeStatus.COMPLETED
                    trace.completed_at = datetime.now(UTC)
                    return {**result, "node_traces": [trace]}

                except Exception as exc:
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

            return {
                "node_traces": [trace],
                "error_count": 1,
            }

        return wrapper

    return decorator
