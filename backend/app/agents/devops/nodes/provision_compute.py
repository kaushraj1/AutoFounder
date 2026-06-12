"""Provision ECS Fargate cluster and services (scaffold implementation)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import ECSCluster, ECSService, InfraStatus, NodeStatus, NodeTrace


async def provision_compute(state: dict) -> dict:
	data = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	region = data.get("aws_region", "ap-south-1")
	org = data.get("organization_id", "tenant")
	run = str(data.get("run_id", "run"))[:8]
	services = []

	for service in data.get("services", []):
		services.append(
			ECSService(
				service_name=service["name"],
				desired_count=int(service.get("replicas_baseline", 2)),
				container_port=int(service["port"]),
				health_check_path=service.get("health_check_path", "/health"),
				status=InfraStatus.READY,
			)
		)

	cluster = ECSCluster(
		cluster_name=f"{org[:16]}-{run}",
		cluster_arn=f"arn:aws:ecs:{region}:000000000000:cluster/{org[:16]}-{run}",
		region=region,
		services=services,
		status=InfraStatus.READY,
	)

	return {
		"ecs_cluster": cluster,
		"node_traces": [
			NodeTrace(
				node="provision_compute",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}