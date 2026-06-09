"""Unit — SLA tracking records breaches without aborting."""

from __future__ import annotations

import asyncio

from prometheus_client import REGISTRY

from app.agents.reviewer.utils.sla import track_sla


async def test_sla_breach_increments_counter() -> None:
    node = "test_sla_node"
    before = REGISTRY.get_sample_value("reviewer_sla_breaches_total", {"node": node}) or 0.0
    async with track_sla(node, budget_seconds=0.0, tenant="org-x"):
        await asyncio.sleep(0.01)  # guaranteed to exceed a 0s budget
    after = REGISTRY.get_sample_value("reviewer_sla_breaches_total", {"node": node}) or 0.0
    assert after == before + 1


async def test_sla_within_budget_does_not_breach() -> None:
    node = "test_sla_node_ok"
    before = REGISTRY.get_sample_value("reviewer_sla_breaches_total", {"node": node}) or 0.0
    async with track_sla(node, budget_seconds=60.0):
        pass
    after = REGISTRY.get_sample_value("reviewer_sla_breaches_total", {"node": node}) or 0.0
    assert after == before
