"""Attach product-tier resources onto the shared foundation network."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.agents.devops.schema import NodeStatus, NodeTrace, VPCConfig
from app.core.config import get_settings

logger = logging.getLogger("app.agents.devops.nodes.attach_foundation_network")


async def attach_foundation_network(state: dict) -> dict:
	data = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	org = data.get("organization_id", "tenant")
	run = str(data.get("run_id", "run"))[:8]
	region = data.get("aws_region", "ap-south-1")

	# TODO(AF-012-021): Replace settings lookup with a terraform_remote_state data
	# source once Asit's foundation network Terraform module ships.
	settings = get_settings()
	logger.warning(
		"attach_foundation_network using hardcoded foundation VPC %s — "
		"replace with terraform_remote_state when AF-012-021 lands.",
		settings.foundation_vpc_id,
	)

	vpc = VPCConfig(
		vpc_id=settings.foundation_vpc_id,
		public_subnet_ids=list(settings.foundation_public_subnet_ids),
		private_subnet_ids=list(settings.foundation_private_subnet_ids),
		availability_zones=list(settings.foundation_availability_zones),
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