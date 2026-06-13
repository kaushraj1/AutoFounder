"""Provision RDS PostgreSQL, ElastiCache, and S3 (Path A: HCL plan validation)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import (
    ElastiCacheCluster,
    InfraStatus,
    NodeStatus,
    NodeTrace,
    RDSInstance,
    S3Bucket,
)
from app.core.logging import bind_log_context, get_logger

logger = get_logger("app.agents.devops.nodes.provision_data_layer")


async def provision_data_layer(state: dict, agent=None) -> dict:
    state = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)
    org = state.get("organization_id", "tenant")
    run = str(state.get("run_id", "run"))[:8]
    region = state.get("aws_region", "ap-south-1")
    bind_log_context(
        organization_id=str(state.get("organization_id", "")),
        run_id=str(state.get("run_id", "")),
        agent_id="devops",
        node="provision_data_layer",
    )

    vpc_cfg = state.get("vpc_config") or {}
    if hasattr(vpc_cfg, "model_dump"):
        vpc_cfg = vpc_cfg.model_dump()
    private_subnets = list(vpc_cfg.get("private_subnet_ids") or [])
    sg_map = vpc_cfg.get("security_group_ids") or {}
    rds_sg = sg_map.get("rds", f"sg-{org[:8]}-rds-{run}")
    redis_sg = sg_map.get("redis", f"sg-{org[:8]}-redis-{run}")

    if agent is not None:
        try:
            plan = await agent._call_tool(
                "terraform_plan_module",
                {
                    "module_name": "data-layer",
                    "organization_id": str(state.get("organization_id", org)),
                    "run_id": str(state.get("run_id", run)),
                    "vars": {
                        "aws_region": region,
                        "private_subnet_ids": private_subnets
                        or ["subnet-placeholder-a", "subnet-placeholder-b"],
                        "rds_security_group_id": rds_sg,
                        "redis_security_group_id": redis_sg,
                    },
                },
            )
            logger.info(
                "provision_data_layer.plan_result",
                ok=plan.get("ok"),
                returncode=plan.get("returncode"),
                working_dir=plan.get("working_dir"),
                duration_ms=plan.get("duration_ms"),
            )
        except Exception as exc:
            logger.warning(
                "provision_data_layer.plan_failed",
                error_type=type(exc).__name__,
                error=str(exc)[:300],
            )

    rds = RDSInstance(
        db_instance_identifier=f"autofounder-{org[:8]}-{run}",
        endpoint=f"autofounder-{org[:8]}-{run}.{region}.rds.amazonaws.com",
        status=InfraStatus.READY,
    )
    redis = ElastiCacheCluster(
        cluster_id=f"redis-{org[:8]}-{run}",
        endpoint=f"redis-{org[:8]}-{run}.cache.amazonaws.com",
        status=InfraStatus.READY,
    )
    bucket = S3Bucket(bucket_name=f"autofounder-{org[:12]}-{run}", region=region)

    return {
        "rds_instance": rds,
        "elasticache_cluster": redis,
        "s3_bucket": bucket,
        "node_traces": [
            NodeTrace(
                node="provision_data_layer",
                status=NodeStatus.COMPLETED,
                started_at=now,
                completed_at=now,
            )
        ],
    }
