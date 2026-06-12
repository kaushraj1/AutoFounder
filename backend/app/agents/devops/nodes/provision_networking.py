"""Attach product-tier resources onto the shared foundation network."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import NodeStatus, NodeTrace, VPCConfig


async def attach_foundation_network(state: dict) -> dict:
	data = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	org = data.get("organization_id", "tenant")
	run = str(data.get("run_id", "run"))[:8]
	region = data.get("aws_region", "ap-south-1")

	vpc = VPCConfig(
		vpc_id="vpc-foundation-shared",
		public_subnet_ids=["subnet-public-a", "subnet-public-b"],
		private_subnet_ids=["subnet-private-a", "subnet-private-b"],
		security_group_ids={
			"alb": f"sg-{org[:8]}-alb-{run}",
			"ecs_tasks": f"sg-{org[:8]}-ecs-{run}",
			"redis": f"sg-{org[:8]}-redis-{run}",
			"rds": f"sg-{org[:8]}-rds-{run}",
		},
		alb_arn=f"arn:aws:elasticloadbalancing:{region}:000000000000:loadbalancer/app/{org}-{run}",
		alb_dns_name=f"{org[:12]}-{run}.elb.{region}.amazonaws.com",
	)

	return {
		"vpc_config": vpc,
		"node_traces": [
			NodeTrace(
				node="attach_foundation_network",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}