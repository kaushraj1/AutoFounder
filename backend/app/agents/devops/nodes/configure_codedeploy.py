"""Generate CodeDeploy appspec and deployment group."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import CodeDeployApp, NodeStatus, NodeTrace


async def configure_codedeploy(state: dict) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	org = state.get("organization_id", "tenant")
	run = str(state.get("run_id", "run"))[:8]
	appspec = "version: 0.0\nResources:\n  - TargetService:\n      Type: AWS::ECS::Service\n"

	return {
		"codedeploy_app": CodeDeployApp(
			app_name=f"cd-{org[:16]}-{run}",
			deployment_group=f"dg-{org[:16]}-{run}",
			appspec_yaml=appspec,
		),
		"node_traces": [
			NodeTrace(
				node="configure_codedeploy",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}