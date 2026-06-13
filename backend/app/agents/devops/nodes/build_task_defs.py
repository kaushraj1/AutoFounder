"""Generate ECS task definitions and service manifests.

LLM-driven: asks the model for Fargate sizing per service, then merges
those values with deterministic family/image/log-group derivations.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from jinja2 import Template
from pydantic import BaseModel

from app.agents.devops.schema import ECSTaskDef, NodeStatus, NodeTrace
from app.agents.devops.utils.llm_json import parse_with_correction


class _TaskDefSpec(BaseModel):
    service_name: str
    cpu_units: int
    memory_mb: int
    container_port: int
    log_retention_days: int = 30


class _TaskDefsResponse(BaseModel):
    task_defs: list[_TaskDefSpec]


async def build_task_defs(state: dict, agent: Any | None = None) -> dict:
    if agent is None:
        raise RuntimeError("build_task_defs requires an agent (LLM router)")
    state = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)
    organization_id = state.get("organization_id", "tenant")
    run_prefix = str(state.get("run_id", "run"))[:8]
    services = state.get("services", [])

    raw_template = agent.prompts.get("devops/build_task_defs")
    rendered = Template(raw_template).render(
        organization_id=organization_id,
        run_id=state.get("run_id"),
        overall_pattern=state.get("overall_pattern", "modular_monolith"),
        services=services,
    )
    raw_response = await agent._call_llm(
        task_class="build_task_defs", prompt=rendered, json_mode=True
    )
    parsed = await parse_with_correction(
        agent=agent,
        task_class="build_task_defs",
        raw_output=raw_response,
        schema=_TaskDefsResponse,
        original_prompt=rendered,
    )

    sizing_by_name = {t.service_name: t for t in parsed.task_defs}
    task_defs: list[ECSTaskDef] = []
    for service in services:
        service_name = service["name"]
        sizing = sizing_by_name.get(service_name)
        if sizing is None:
            raise ValueError(f"build_task_defs: LLM omitted sizing for service '{service_name}'")
        family = f"{organization_id[:16]}-{service_name}-{run_prefix}"
        task_json = json.dumps(
            {
                "family": family,
                "networkMode": "awsvpc",
                "requiresCompatibilities": ["FARGATE"],
                "cpu": str(sizing.cpu_units),
                "memory": str(sizing.memory_mb),
                "containerDefinitions": [
                    {
                        "name": service_name,
                        "image": service["image_uri"],
                        "portMappings": [
                            {"containerPort": sizing.container_port, "protocol": "tcp"}
                        ],
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
