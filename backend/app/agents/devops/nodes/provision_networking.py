"""Attach product-tier resources onto the shared foundation network."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import NodeStatus, NodeTrace, VPCConfig
from app.core.config import get_settings
from app.core.logging import bind_log_context, get_logger

logger = get_logger("app.agents.devops.nodes.attach_foundation_network")


async def attach_foundation_network(state: dict, agent=None) -> dict:
    data = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)
    org = data.get("organization_id", "tenant")
    run = str(data.get("run_id", "run"))[:8]
    region = data.get("aws_region", "ap-south-1")
    bind_log_context(
        organization_id=str(data.get("organization_id", "")),
        run_id=str(data.get("run_id", "")),
        agent_id="devops",
        node="attach_foundation_network",
    )

    # TODO(AF-012-021): Replace settings lookup with a terraform_remote_state data
    # source once Asit's foundation network Terraform module ships.
    settings = get_settings()
    logger.warning(
        "attach_foundation_network.foundation_hardcoded",
        foundation_vpc_id=settings.foundation_vpc_id,
        message=(
            "using hardcoded foundation VPC — replace with terraform_remote_state "
            "when AF-012-021 lands."
        ),
    )

    # Path A: validate the networking HCL against the foundation VPC vars.
    # Plan failures stay non-fatal so the rest of the subgraph still produces
    # state. Cloud ops can grep `terraform_plan_module.plan.done ok=false`.
    if agent is not None:
        try:
            plan = await agent._call_tool(
                "terraform_plan_module",
                {
                    "module_name": "networking",
                    "organization_id": str(data.get("organization_id", org)),
                    "run_id": str(data.get("run_id", run)),
                    "vars": {
                        "aws_region": region,
                        "vpc_id": settings.foundation_vpc_id,
                        "private_subnet_ids": list(settings.foundation_private_subnet_ids),
                        "public_subnet_ids": list(settings.foundation_public_subnet_ids),
                        "availability_zones": list(settings.foundation_availability_zones),
                    },
                },
            )
            logger.info(
                "attach_foundation_network.plan_result",
                ok=plan.get("ok"),
                returncode=plan.get("returncode"),
                working_dir=plan.get("working_dir"),
                duration_ms=plan.get("duration_ms"),
            )
        except Exception as exc:
            logger.warning(
                "attach_foundation_network.plan_failed",
                error_type=type(exc).__name__,
                error=str(exc)[:300],
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
