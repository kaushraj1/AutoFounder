"""Build the deploy report markdown from final state.

LLM-driven: the model writes a terse founder-facing release note. The
prompt instructs it to return raw Markdown (not JSON), so we surface
the LLM output verbatim after a small trim.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from jinja2 import Template

from app.agents.devops.schema import NodeStatus, NodeTrace


async def render_deploy_report(state: dict, agent: Any | None = None) -> dict:
    if agent is None:
        raise RuntimeError("render_deploy_report requires an agent (LLM router)")
    state = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)

    raw_template = agent.prompts.get("devops/render_deploy_report")
    rendered = Template(raw_template).render(
        organization_id=state.get("organization_id"),
        run_id=state.get("run_id"),
        aws_region=state.get("aws_region"),
        live_url=state.get("live_url"),
        deploy_status=state.get("deploy_status"),
        smoke_tests_passed=state.get("smoke_tests_passed"),
        estimated_monthly_cost_usd=state.get("estimated_monthly_cost_usd"),
        services=state.get("services", []),
        monitoring_config=state.get("monitoring_config"),
        cicd_config=state.get("cicd_config"),
    )
    raw_response = await agent._call_llm(
        task_class="render_deploy_report", prompt=rendered, json_mode=False
    )
    report = raw_response.strip()
    if report.startswith("```"):
        lines = report.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        report = "\n".join(lines).strip()

    return {
        "deploy_report_markdown": report,
        "node_traces": [
            NodeTrace(
                node="render_deploy_report",
                status=NodeStatus.COMPLETED,
                started_at=now,
                completed_at=now,
            )
        ],
    }
