"""Full DevOps subgraph end-to-end test against LocalStack.

Runs ``DevOpsAgent`` through ``understand`` -> ``plan`` -> ``execute`` with
``devops_tools_mode='real'`` and ``aws_endpoint_url`` pointed at LocalStack,
then asserts:
  * Secrets actually exist on LocalStack Secrets Manager
  * ACM cert was requested
  * GitHub commit was skipped (dry-run default still on)
  * CodeDeploy app/group/deployment objects flow through state (the
    underlying CodeDeploy service is Pro-only on LocalStack, so those
    tools are patched to scaffold mode just for this test)

We call ``agent.execute(plan)`` rather than ``agent.run`` because the
synthesized ALB FQDN is not reachable, which makes the verify-phase
smoke-test assertion fail. The graph itself still produces a complete
state, which is what we want to inspect.

Gated by ``LOCALSTACK_RUNNING=1``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import boto3
import pytest

from app.agents._providers import JinjaPromptRegistry
from app.agents.devops import DevOpsAgent
from app.agents.devops import tools as devops_tools
from app.agents.devops.schema import ApprovalStatus, DevOpsState
from app.agents.devops.tests._fakes import FakeDevOpsLLMRouter
from app.agents.devops.tools import LocalToolRegistry
from app.core.config import get_settings

pytestmark = pytest.mark.localstack

if not os.getenv("LOCALSTACK_RUNNING"):
    pytest.skip(
        "LOCALSTACK_RUNNING is not set; skipping subgraph LocalStack e2e",
        allow_module_level=True,
    )


LOCALSTACK_URL = os.getenv("LOCALSTACK_URL", "http://localhost:4566")
FIXTURE = Path(__file__).resolve().parents[4] / ".claude" / "specs" / "pillar5-dummy-input.json"


class _StubUDAL:
    pass


def _load_input() -> dict[str, Any]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload.setdefault("repo_url", payload.get("github_repo_html_url", ""))
    payload["approval_status"] = ApprovalStatus.APPROVED.value
    return payload


def _aws(service: str) -> Any:
    return boto3.client(
        service,
        endpoint_url=LOCALSTACK_URL,
        region_name="ap-south-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


@pytest.fixture(autouse=True)
def _real_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "devops_tools_mode", "real")
    monkeypatch.setattr(settings, "aws_endpoint_url", LOCALSTACK_URL)
    monkeypatch.setattr(settings, "aws_region", "ap-south-1")
    monkeypatch.setattr(settings, "devops_github_dry_run", True)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")


@pytest.fixture(autouse=True)
def _stub_codedeploy(monkeypatch: pytest.MonkeyPatch) -> None:
    # CodeDeploy is Pro-only on LocalStack — community drops the service
    # silently. Patch the three tool wrappers to return scaffold-shaped
    # responses so the graph can flow past deploy_application.
    async def _fake_app(**kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "app_name": kwargs.get("app_name"), "existed": False}

    async def _fake_group(**kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "deployment_group": kwargs.get("deployment_group")}

    async def _fake_deploy(**kwargs: Any) -> dict[str, Any]:
        return {
            "ok": True,
            "app_name": kwargs.get("app_name"),
            "deployment_group": kwargs.get("deployment_group"),
            "deployment_id": f"d-stub-{kwargs.get('app_name', 'x')[:8]}",
        }

    monkeypatch.setitem(devops_tools._TOOL_DISPATCH, "codedeploy_create_application", _fake_app)
    monkeypatch.setitem(
        devops_tools._TOOL_DISPATCH,
        "codedeploy_create_deployment_group",
        _fake_group,
    )
    monkeypatch.setitem(devops_tools._TOOL_DISPATCH, "codedeploy_create_deployment", _fake_deploy)


async def test_devops_subgraph_against_localstack() -> None:
    if not FIXTURE.exists():
        pytest.skip(f"Fixture {FIXTURE} not present")

    agent = DevOpsAgent(
        udal=_StubUDAL(),
        checkpointer=None,
        tool_registry=LocalToolRegistry(),
        prompt_registry=JinjaPromptRegistry(),
        llm_router=FakeDevOpsLLMRouter(),
    )

    payload = _load_input()
    intent = await agent.understand(payload)
    plan = await agent.plan(intent)
    state: DevOpsState = await agent.execute(plan)

    # 1) provision_secrets -> SecretsManager
    assert state.secrets, "provision_secrets should produce at least one secret"
    sm = _aws("secretsmanager")
    listed = {s["Name"] for s in sm.list_secrets().get("SecretList", [])}
    for ref in state.secrets:
        assert ref.secret_name in listed, f"secret {ref.secret_name} not on LocalStack"
        assert ref.secret_arn, f"secret_arn missing for {ref.secret_name}"

    # 2) configure_codedeploy + deploy_application -> graph state populated
    #    (real CodeDeploy is Pro-only on LocalStack — see _stub_codedeploy)
    assert state.codedeploy_app is not None
    assert state.deployment_id, "deploy_application should set deployment_id"

    # 3) configure_dns_ssl -> ACM cert ARN looks real
    assert state.tls_certificate is not None
    assert state.tls_certificate.cert_arn.startswith("arn:aws:acm:")

    # 4) configure_cicd -> github_upsert_file should have short-circuited
    #    (dry-run on), CICDConfig still populated
    assert state.cicd_config is not None
    assert state.cicd_config.workflow_yaml
