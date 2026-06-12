"""Generate ECS task definitions and service manifests."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.agents.devops.schema import ECSTaskDef, NodeStatus, NodeTrace


async def build_task_defs(state: dict) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	organization_id = state.get("organization_id", "tenant")
	run_prefix = str(state.get("run_id", "run"))[:8]
	task_defs: list[ECSTaskDef] = []

	for service in state.get("services", []):
		service_name = service["name"]
		family = f"{organization_id[:16]}-{service_name}-{run_prefix}"
		task_json = json.dumps(
			{
				"family": family,
				"networkMode": "awsvpc",
				"requiresCompatibilities": ["FARGATE"],
				"containerDefinitions": [
					{
						"name": service_name,
						"image": service["image_uri"],
						"portMappings": [{"containerPort": service["port"], "protocol": "tcp"}],
						"essential": True,
					}
				],
			}
		)
		task_defs.append(
			ECSTaskDef(
				service_name=service_name,
				family=family,
				task_def_json=task_json,
				container_image=service["image_uri"],
				log_group=f"/ecs/{organization_id}/{run_prefix}/{service_name}",
			)
		)

	return {
		"task_defs": task_defs,
		"node_traces": [
			NodeTrace(
				node="build_task_defs",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}