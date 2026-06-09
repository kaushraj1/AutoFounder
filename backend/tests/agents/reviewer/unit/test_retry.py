"""Unit — with_retry records faults without raising, and times the node (SLA)."""

from __future__ import annotations

from typing import Any

from prometheus_client import REGISTRY
from tests.agents.reviewer.conftest import make_state

from app.agents.reviewer.schema import NodeStatus, RetryPolicy
from app.agents.reviewer.utils.retry import with_retry


async def test_exhaustion_returns_failed_trace_without_raising() -> None:
    @with_retry("flaky")
    async def always_fails(state: Any, agent: Any) -> dict[str, Any]:
        raise RuntimeError("boom")

    state = make_state(retry_policy=RetryPolicy(max_retries=1, backoff_seconds=[0]))
    result = await always_fails(state, agent=None)  # must not raise

    assert result["error_count"] == 1
    trace = result["node_traces"][0]
    assert trace.status is NodeStatus.FAILED
    assert "boom" in (trace.error or "")
    assert trace.retry_count == 1  # retried once after the first attempt


async def test_success_records_completed_trace_and_duration() -> None:
    before = (
        REGISTRY.get_sample_value(
            "reviewer_node_duration_seconds_count",
            {"node": "oknode", "tenant": "org-test", "status": "completed"},
        )
        or 0.0
    )

    @with_retry("oknode")
    async def ok(state: Any, agent: Any) -> dict[str, Any]:
        return {"total_tool_calls": 1}

    result = await ok(make_state(), agent=None)
    trace = result["node_traces"][0]
    assert trace.status is NodeStatus.COMPLETED
    assert trace.sla_breached is False
    assert result["total_tool_calls"] == 1

    after = (
        REGISTRY.get_sample_value(
            "reviewer_node_duration_seconds_count",
            {"node": "oknode", "tenant": "org-test", "status": "completed"},
        )
        or 0.0
    )
    assert after == before + 1  # the node was timed (SLA metric emitted)
