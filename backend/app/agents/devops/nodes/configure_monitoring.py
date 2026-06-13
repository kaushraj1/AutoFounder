"""CloudWatch alarms, Prometheus scrape, Grafana.

LLM-driven: the model picks 1-5 alarms appropriate for the deployed
services; we wrap each in a CloudWatchAlarm with deterministic naming.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from jinja2 import Template
from pydantic import BaseModel, Field

from app.agents.devops.schema import (
    CloudWatchAlarm,
    MonitoringConfig,
    NodeStatus,
    NodeTrace,
)
from app.agents.devops.utils.llm_json import parse_with_correction


class _AlarmSpec(BaseModel):
    name_suffix: str
    metric_name: str
    namespace: str
    threshold: float
    comparison: str
    evaluation_periods: int = 2
    period_seconds: int = 60


class _MonitoringResponse(BaseModel):
    alarms: list[_AlarmSpec] = Field(default_factory=list)
    log_retention_days: int = 30


_SAFE_SLUG = re.compile(r"[^a-z0-9-]+")


async def configure_monitoring(state: dict, agent: Any | None = None) -> dict:
    if agent is None:
        raise RuntimeError("configure_monitoring requires an agent (LLM router)")
    state = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)
    org = state.get("organization_id", "tenant")
    run = str(state.get("run_id", "run"))[:8]

    vpc_cfg = state.get("vpc_config") or {}
    ecs_cluster_obj = state.get("ecs_cluster") or {}
    alb_arn = vpc_cfg.get("alb_arn") if isinstance(vpc_cfg, dict) else None
    ecs_cluster_name = (
        ecs_cluster_obj.get("cluster_name") if isinstance(ecs_cluster_obj, dict) else None
    )

    raw_template = agent.prompts.get("devops/configure_monitoring")
    rendered = Template(raw_template).render(
        organization_id=org,
        run_id=state.get("run_id"),
        aws_region=state.get("aws_region"),
        alb_arn=alb_arn,
        ecs_cluster_name=ecs_cluster_name,
        services=state.get("services", []),
    )
    raw_response = await agent._call_llm(
        task_class="configure_monitoring", prompt=rendered, json_mode=True
    )
    parsed = await parse_with_correction(
        agent=agent,
        task_class="configure_monitoring",
        raw_output=raw_response,
        schema=_MonitoringResponse,
        original_prompt=rendered,
    )
    if len(parsed.alarms) > 5:
        parsed.alarms = parsed.alarms[:5]

    alarms: list[CloudWatchAlarm] = []
    for spec in parsed.alarms:
        suffix = _SAFE_SLUG.sub("-", spec.name_suffix.lower()).strip("-") or "alarm"
        alarms.append(
            CloudWatchAlarm(
                alarm_name=f"{org[:12]}-{run}-{suffix}",
                metric_name=spec.metric_name,
                namespace=spec.namespace,
                threshold=spec.threshold,
                comparison=spec.comparison,
                evaluation_periods=spec.evaluation_periods,
                period_seconds=spec.period_seconds,
            )
        )

    cfg = MonitoringConfig(
        cloudwatch_alarms=alarms,
        prometheus_scrape_configs=["job_name: ecs-services"],
        grafana_dashboard_url=f"https://grafana.example.com/d/{run}",
        log_group_name=f"/ecs/{org}/{run}",
        log_retention_days=parsed.log_retention_days,
    )
    return {
        "monitoring_config": cfg,
        "node_traces": [
            NodeTrace(
                node="configure_monitoring",
                status=NodeStatus.COMPLETED,
                started_at=now,
                completed_at=now,
            )
        ],
    }
