"""Unit tests for the DevOps HITL spend gate."""

from __future__ import annotations

import importlib
from typing import Any

import fakeredis.aioredis
import pytest

from app.agents.devops.nodes.hitl_spend_gate import hitl_spend_gate
from app.agents.devops.schema import ApprovalStatus, NodeStatus
from app.core.config import get_settings

# nodes/__init__.py re-exports the function under the same name as the submodule,
# so plain `from ... import hitl_spend_gate as hitl_module` returns the function.
# Use importlib to get the actual module object for monkeypatching.
hitl_module = importlib.import_module("app.agents.devops.nodes.hitl_spend_gate")

RUN_ID = "11111111-1111-4111-8111-111111111111"


def _base_state(**overrides: Any) -> dict:
    state: dict = {
        "run_id": RUN_ID,
        "organization_id": "tenant-acme",
        "approval_status": ApprovalStatus.PENDING,
        "approval_comment": None,
        "estimated_monthly_cost_usd": 64.5,
    }
    state.update(overrides)
    return state


@pytest.fixture(autouse=True)
def _fast_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force short poll intervals so tests run in <1s."""
    settings = get_settings()
    monkeypatch.setattr(settings, "devops_hitl_poll_interval_seconds", 0.01)
    monkeypatch.setattr(settings, "devops_hitl_timeout_seconds", 0.2)
    monkeypatch.setattr(settings, "devops_spend_gate_cap_usd", 150.0)


async def test_hitl_pre_approved_passes_through() -> None:
    state = _base_state(approval_status=ApprovalStatus.APPROVED)

    result = await hitl_spend_gate(state)

    assert result["approval_status"] == ApprovalStatus.APPROVED
    assert result["last_error"] is None
    assert result["node_traces"][0].status == NodeStatus.COMPLETED


async def test_hitl_under_cap_auto_approves() -> None:
    state = _base_state(estimated_monthly_cost_usd=64.5)

    result = await hitl_spend_gate(state)

    assert result["approval_status"] == ApprovalStatus.APPROVED
    assert "Auto-approved" in (result["approval_comment"] or "")
    assert result["last_error"] is None


async def test_hitl_over_cap_polls_redis_and_approves(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await redis.set(f"hitl:devops:spend:{RUN_ID}", "approved")
    monkeypatch.setattr(hitl_module, "_get_redis_client", lambda: redis)

    state = _base_state(estimated_monthly_cost_usd=500.0)

    result = await hitl_spend_gate(state)

    assert result["approval_status"] == ApprovalStatus.APPROVED
    assert result["last_error"] is None
    assert "Founder approved" in (result["approval_comment"] or "")


async def test_hitl_over_cap_polls_redis_and_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await redis.set(f"hitl:devops:spend:{RUN_ID}", "rejected")
    monkeypatch.setattr(hitl_module, "_get_redis_client", lambda: redis)

    state = _base_state(estimated_monthly_cost_usd=500.0)

    result = await hitl_spend_gate(state)

    assert result["approval_status"] == ApprovalStatus.REJECTED
    assert result["last_error"] is not None
    assert result["node_traces"][0].status == NodeStatus.FAILED


async def test_hitl_over_cap_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    # Nothing pre-populated → poll loop runs to the deadline.
    monkeypatch.setattr(hitl_module, "_get_redis_client", lambda: redis)

    state = _base_state(estimated_monthly_cost_usd=500.0)

    result = await hitl_spend_gate(state)

    assert result["approval_status"] == ApprovalStatus.TIMED_OUT
    assert result["last_error"] is not None


async def test_hitl_over_cap_redis_unavailable_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise() -> None:
        raise RuntimeError("Redis pool not initialized")

    monkeypatch.setattr(hitl_module, "_get_redis_client", _raise)

    state = _base_state(estimated_monthly_cost_usd=500.0)

    result = await hitl_spend_gate(state)

    assert result["approval_status"] == ApprovalStatus.REJECTED
    assert result["last_error"] is not None
