"""Commit GitHub Actions workflow to the tenant repo.

LLM-driven: the model authors the workflow YAML; we wrap it in CICDConfig
and let the downstream tool-call commit it (dry-run by default).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from jinja2 import Template
from pydantic import BaseModel

from app.agents.devops.schema import CICDConfig, NodeStatus, NodeTrace
from app.agents.devops.utils.llm_json import parse_with_correction


class _CICDResponse(BaseModel):
    workflow_yaml: str


async def configure_cicd(state: dict, agent: Any | None = None) -> dict:
    if agent is None:
        raise RuntimeError("configure_cicd requires an agent (LLM router)")
    state = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)

    cd_app = state.get("codedeploy_app")
    codedeploy_app_name = None
    if isinstance(cd_app, dict):
        codedeploy_app_name = cd_app.get("app_name")
    elif cd_app is not None:
        codedeploy_app_name = getattr(cd_app, "app_name", None)

    raw_template = agent.prompts.get("devops/configure_cicd")
    rendered = Template(raw_template).render(
        organization_id=state.get("organization_id"),
        run_id=state.get("run_id"),
        aws_region=state.get("aws_region"),
        ecr_registry=state.get("ecr_registry"),
        codedeploy_app_name=codedeploy_app_name,
        services=state.get("services", []),
    )
    raw_response = await agent._call_llm(
        task_class="configure_cicd", prompt=rendered, json_mode=True
    )
    parsed = await parse_with_correction(
        agent=agent,
        task_class="configure_cicd",
        raw_output=raw_response,
        schema=_CICDResponse,
        original_prompt=rendered,
    )

    repo_full_name = state.get("github_repo_full_name")
    if repo_full_name:
        try:
            await agent._call_tool(
                "github_upsert_file",
                {
                    "repo_full_name": repo_full_name,
                    "path": ".github/workflows/deploy.yml",
                    "content": parsed.workflow_yaml,
                    "commit_message": f"chore: add CodeDeploy workflow for run {state.get('run_id')}",
                    "branch": state.get("github_branch", "main"),
                },
            )
        except Exception:
            pass

    return {
        "cicd_config": CICDConfig(
            workflow_file_path=".github/workflows/deploy.yml",
            workflow_yaml=parsed.workflow_yaml,
            codedeploy_app_name=codedeploy_app_name,
            ecr_registry=state.get("ecr_registry"),
        ),
        "node_traces": [
            NodeTrace(
                node="configure_cicd",
                status=NodeStatus.COMPLETED,
                started_at=now,
                completed_at=now,
            )
        ],
    }
