"""End-to-end test of DevOpsAgent.run() via the BaseAgent contract.

Loads the canonical CoderOutput dummy fixture and asserts the agent runs the
full 14-node graph through to render_deploy_report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.agents.devops import DevOpsAgent
from app.agents.devops.schema import ApprovalStatus, DeployStatus, DevOpsState
from app.agents.devops.tools import LocalToolRegistry

FIXTURE = (
    Path(__file__).resolve().parents[6]
    / ".claude"
    / "specs"
    / "pillar5-dummy-input.json"
)


class _StubUDAL:
    pass


class _StubPromptRegistry:
    def get(self, key: str, version: str | None = None) -> str:
        return ""


class _StubLLMRouter:
    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        raise RuntimeError("DevOps scaffold must not call the LLM")


def _load_input() -> dict[str, Any]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload.setdefault("repo_url", payload.get("github_repo_html_url", ""))
    # Pre-approve the spend gate so the happy path runs end-to-end.
    payload["approval_status"] = ApprovalStatus.APPROVED.value
    return payload


@pytest.mark.asyncio
async def test_devops_agent_run_happy_path() -> None:
    if not FIXTURE.exists():
        pytest.skip(f"Fixture {FIXTURE} not present")

    agent = DevOpsAgent(
        udal=_StubUDAL(),
        checkpointer=None,
        tool_registry=LocalToolRegistry(),
        prompt_registry=_StubPromptRegistry(),
        llm_router=_StubLLMRouter(),
    )

    out: DevOpsState = await agent.run(_load_input())

    assert out.deploy_status == DeployStatus.HEALTHY
    assert out.live_url, "live_url should be populated by configure_dns_ssl"
    assert out.smoke_tests_passed is True
    assert out.deploy_report_markdown, "render_deploy_report should produce markdown"
    assert out.vpc_config is not None
    # Foundation VPC must come from settings (real account), not the placeholder.
    assert out.vpc_config.vpc_id.startswith("vpc-")
    assert len(out.vpc_config.private_subnet_ids) >= 2
    assert len(out.vpc_config.public_subnet_ids) >= 2


@pytest.mark.asyncio
async def test_devops_agent_run_isolation_two_tenants() -> None:
    """Two organization_id runs must not collide on derived resource names."""
    if not FIXTURE.exists():
        pytest.skip(f"Fixture {FIXTURE} not present")

    def _agent() -> DevOpsAgent:
        return DevOpsAgent(
            udal=_StubUDAL(),
            checkpointer=None,
            tool_registry=LocalToolRegistry(),
            prompt_registry=_StubPromptRegistry(),
            llm_router=_StubLLMRouter(),
        )

    a = _load_input()
    a["organization_id"] = "tenant-aaaa-aaaa-aaaa"
    a["run_id"] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    b = _load_input()
    b["organization_id"] = "tenant-bbbb-bbbb-bbbb"
    b["run_id"] = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    out_a = await _agent().run(a)
    out_b = await _agent().run(b)

    assert out_a.organization_id != out_b.organization_id
    assert out_a.rds_instance and out_b.rds_instance
    assert (
        out_a.rds_instance.db_instance_identifier
        != out_b.rds_instance.db_instance_identifier
    )
    assert out_a.s3_bucket and out_b.s3_bucket
    assert out_a.s3_bucket.bucket_name != out_b.s3_bucket.bucket_name
    assert out_a.vpc_config and out_b.vpc_config
    # Foundation VPC is shared — that's the whole point of the foundation network.
    assert out_a.vpc_config.vpc_id == out_b.vpc_config.vpc_id
    # ...but security groups are per-tenant.
    assert (
        out_a.vpc_config.security_group_ids["ecs_tasks"]
        != out_b.vpc_config.security_group_ids["ecs_tasks"]
    )
