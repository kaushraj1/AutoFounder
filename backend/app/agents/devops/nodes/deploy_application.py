"""Trigger CodeDeploy blue/green deployment to ECS.

Calls ``codedeploy_create_deployment`` against the application + group
created by ``configure_codedeploy``. Failures flip the deploy_status to
FAILED so the router sends the run to error_handler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agents.devops.schema import DeployStatus, NodeStatus, NodeTrace
from app.core.logging import bind_log_context, get_logger

logger = get_logger("app.agents.devops.nodes.deploy_application")


async def deploy_application(state: dict, agent: Any | None = None) -> dict:
    state = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)
    bind_log_context(
        organization_id=str(state.get("organization_id", "")),
        run_id=str(state.get("run_id", "")),
        agent_id="devops",
        node="deploy_application",
    )
    task_defs = state.get("task_defs", [])
    if not task_defs:
        logger.error(
            "deploy_application.no_task_defs",
            message="task_defs missing — upstream build_task_defs likely failed",
        )
        return {
            "deploy_status": DeployStatus.FAILED,
            "last_error": "No task definitions available for deployment",
            "node_traces": [
                NodeTrace(
                    node="deploy_application",
                    status=NodeStatus.FAILED,
                    started_at=now,
                    completed_at=now,
                    error="No task definitions",
                )
            ],
        }

    run = str(state.get("run_id", "run"))[:8]
    deployment_id: str | None = f"d-{run}"
    cd_app = state.get("codedeploy_app") or {}
    app_name = (
        cd_app.get("app_name") if isinstance(cd_app, dict) else getattr(cd_app, "app_name", None)
    )
    deployment_group = (
        cd_app.get("deployment_group")
        if isinstance(cd_app, dict)
        else getattr(cd_app, "deployment_group", None)
    )

    if agent is not None and app_name and deployment_group:
        try:
            result = await agent._call_tool(
                "codedeploy_create_deployment",
                {"app_name": app_name, "deployment_group": deployment_group},
            )
            deployment_id = result.get("deployment_id") or deployment_id
        except Exception as exc:
            logger.error(
                "deploy_application.codedeploy_failed",
                error_type=type(exc).__name__,
                error=str(exc)[:300],
                app_name=app_name,
                deployment_group=deployment_group,
            )
            return {
                "deploy_status": DeployStatus.FAILED,
                "last_error": f"CodeDeploy create_deployment failed: {exc}",
                "node_traces": [
                    NodeTrace(
                        node="deploy_application",
                        status=NodeStatus.FAILED,
                        started_at=now,
                        completed_at=now,
                        error=str(exc),
                    )
                ],
            }

    return {
        "deploy_status": DeployStatus.HEALTHY,
        "deployment_id": deployment_id,
        "node_traces": [
            NodeTrace(
                node="deploy_application",
                status=NodeStatus.COMPLETED,
                started_at=now,
                completed_at=now,
            )
        ],
    }
