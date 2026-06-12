"""Best-effort error handling for failed deployment paths."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import DeployStatus, NodeStatus, NodeTrace


async def error_handler(state: dict) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	reason = state.get("last_error") or "Deployment flow routed to error handler"
	return {
		"deploy_status": DeployStatus.FAILED,
		"last_error": reason,
		"node_traces": [
			NodeTrace(
				node="error_handler",
				status=NodeStatus.FAILED,
				started_at=now,
				completed_at=now,
				error=reason,
			)
		],
	}