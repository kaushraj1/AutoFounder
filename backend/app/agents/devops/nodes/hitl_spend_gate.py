"""Wait for founder approval of the AWS spend estimate."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import ApprovalStatus, NodeStatus, NodeTrace

DEFAULT_AUTO_APPROVE_CAP_USD = 150.0


async def hitl_spend_gate(state: dict) -> dict:
	data = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	approval_status = data.get("approval_status", ApprovalStatus.PENDING)
	cost = float(data.get("estimated_monthly_cost_usd") or 0.0)

	if approval_status == ApprovalStatus.PENDING:
		if cost <= DEFAULT_AUTO_APPROVE_CAP_USD:
			approval_status = ApprovalStatus.APPROVED
			approval_comment = "Auto-approved under scaffolding cap"
		else:
			approval_status = ApprovalStatus.REJECTED
			approval_comment = "Rejected by scaffolding cap; requires human approval"
	else:
		approval_comment = data.get("approval_comment")

	return {
		"approval_status": approval_status,
		"approval_comment": approval_comment,
		"node_traces": [
			NodeTrace(
				node="hitl_spend_gate",
				status=(
					NodeStatus.COMPLETED
					if approval_status == ApprovalStatus.APPROVED
					else NodeStatus.FAILED
				),
				started_at=now,
				completed_at=now,
			)
		],
		"last_error": (
			None
			if approval_status == ApprovalStatus.APPROVED
			else "Infra spend gate was not approved"
		),
	}