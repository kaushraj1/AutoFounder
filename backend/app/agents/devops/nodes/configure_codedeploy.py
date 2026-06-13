"""Generate CodeDeploy appspec, application, and deployment group.

Calls ``codedeploy_create_application`` + ``codedeploy_create_deployment_group``
so the deployment group exists before ``deploy_application`` tries to
create a deployment against it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agents.devops.schema import CodeDeployApp, NodeStatus, NodeTrace
from app.core.logging import bind_log_context, get_logger

logger = get_logger("app.agents.devops.nodes.configure_codedeploy")


async def configure_codedeploy(state: dict, agent: Any | None = None) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	org = state.get("organization_id", "tenant")
	run = str(state.get("run_id", "run"))[:8]
	bind_log_context(
		organization_id=str(state.get("organization_id", "")),
		run_id=str(state.get("run_id", "")),
		agent_id="devops",
		node="configure_codedeploy",
	)
	app_name = f"cd-{org[:16]}-{run}"
	deployment_group = f"dg-{org[:16]}-{run}"
	appspec = "version: 0.0\nResources:\n  - TargetService:\n      Type: AWS::ECS::Service\n"

	if agent is not None:
		try:
			await agent._call_tool(
				"codedeploy_create_application",
				{"app_name": app_name, "compute_platform": "ECS"},
			)
			# Use the AutoFounder operator role ARN convention; LocalStack
			# accepts any well-formed role ARN without verifying it exists.
			role_arn = (
				f"arn:aws:iam::000000000000:role/autofounder-{org[:12]}-codedeploy"
			)
			await agent._call_tool(
				"codedeploy_create_deployment_group",
				{
					"app_name": app_name,
					"deployment_group": deployment_group,
					"service_role_arn": role_arn,
				},
			)
		except Exception as exc:
			# A tool failure here is not fatal at the graph-state level;
			# deploy_application will fail loudly when it tries to deploy.
			logger.warning(
				"configure_codedeploy.tool_failed",
				error_type=type(exc).__name__,
				error=str(exc)[:300],
			)

	return {
		"codedeploy_app": CodeDeployApp(
			app_name=app_name,
			deployment_group=deployment_group,
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
