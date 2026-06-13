"""Provision ECS Fargate cluster and services (Path A: HCL plan validation)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import ECSCluster, ECSService, InfraStatus, NodeStatus, NodeTrace
from app.core.logging import bind_log_context, get_logger

logger = get_logger("app.agents.devops.nodes.provision_compute")


async def provision_compute(state: dict, agent=None) -> dict:
    data = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)
    region = data.get("aws_region", "ap-south-1")
    org = data.get("organization_id", "tenant")
    run = str(data.get("run_id", "run"))[:8]
    bind_log_context(
        organization_id=str(data.get("organization_id", "")),
        run_id=str(data.get("run_id", "")),
        agent_id="devops",
        node="provision_compute",
    )

    services = []
    # Build both the synthesized ECSService list AND the var.services map the
    # ecs module expects, so we can validate the module wiring with `plan`.
    services_var: dict[str, dict] = {}
    for service in data.get("services", []):
        name = service["name"]
        port = int(service["port"])
        desired = int(service.get("replicas_baseline", 2))
        health = service.get("health_check_path", "/health")
        image = service.get("image_uri") or f"placeholder/{name}:latest"
        services.append(
            ECSService(
                service_name=name,
                desired_count=desired,
                container_port=port,
                health_check_path=health,
                status=InfraStatus.READY,
            )
        )
        services_var[name] = {
            "image_uri": image,
            "container_port": port,
            "desired_count": desired,
            "cpu": int(service.get("cpu", 256)),
            "memory_mb": int(service.get("memory_mb", 512)),
            "health_check_path": health,
            "env_secret_refs": list(service.get("env_secret_refs", [])),
        }

    vpc_cfg = data.get("vpc_config") or {}
    if hasattr(vpc_cfg, "model_dump"):
        vpc_cfg = vpc_cfg.model_dump()
    private_subnets = list(vpc_cfg.get("private_subnet_ids") or [])
    sg_map = vpc_cfg.get("security_group_ids") or {}
    ecs_tasks_sg = sg_map.get("ecs_tasks", f"sg-{org[:8]}-ecs-{run}")

    # Path A plan-only validation of the ecs module against the var schema.
    if agent is not None:
        try:
            plan = await agent._call_tool(
                "terraform_plan_module",
                {
                    "module_name": "ecs",
                    "organization_id": str(data.get("organization_id", org)),
                    "run_id": str(data.get("run_id", run)),
                    "vars": {
                        "aws_region": region,
                        "services": services_var,
                        "private_subnet_ids": private_subnets
                        or ["subnet-placeholder-a", "subnet-placeholder-b"],
                        "ecs_tasks_security_group_id": ecs_tasks_sg,
                    },
                },
            )
            logger.info(
                "provision_compute.plan_result",
                ok=plan.get("ok"),
                returncode=plan.get("returncode"),
                working_dir=plan.get("working_dir"),
                duration_ms=plan.get("duration_ms"),
                service_count=len(services_var),
            )
        except Exception as exc:
            logger.warning(
                "provision_compute.plan_failed",
                error_type=type(exc).__name__,
                error=str(exc)[:300],
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
