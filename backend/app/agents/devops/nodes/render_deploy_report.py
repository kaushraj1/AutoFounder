"""Build the deploy report markdown from final state."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import NodeStatus, NodeTrace


async def render_deploy_report(state: dict) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	report = (
		"# DevOps Deployment Report\n\n"
		f"- Organization: {state.get('organization_id')}\n"
		f"- Run: {state.get('run_id')}\n"
		f"- Region: {state.get('aws_region')}\n"
		f"- Live URL: {state.get('live_url')}\n"
		f"- Deploy status: {state.get('deploy_status')}\n"
		f"- Smoke passed: {state.get('smoke_tests_passed')}\n"
		f"- Estimated monthly cost (USD): {state.get('estimated_monthly_cost_usd')}\n"
	)
	return {
		"deploy_report_markdown": report,
		"node_traces": [
			NodeTrace(
				node="render_deploy_report",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}