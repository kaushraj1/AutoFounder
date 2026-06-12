"""Validate CoderOutput and compute cost estimate."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.agents.devops.schema import NodeStatus, NodeTrace
from app.agents.devops.utils.cost import estimate_monthly_cost_usd


async def ingest_input(state: dict) -> dict:
	data = state.model_dump() if hasattr(state, "model_dump") else state
	services = data.get("services", [])
	now = datetime.now(UTC)
	return {
		"estimated_monthly_cost_usd": estimate_monthly_cost_usd(services),
		"approval_timeout_at": now + timedelta(minutes=15),
		"node_traces": [
			NodeTrace(
				node="ingest_input",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}