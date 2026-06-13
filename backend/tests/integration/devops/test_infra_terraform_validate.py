"""Offline (Path A) integration test for the three infra DevOps nodes.

Runs ``terraform init -backend=false`` + ``terraform validate`` against
the seeded ``networking``, ``data-layer``, and ``ecs`` modules using the
:func:`terraform_plan_module` tool wrapper. Validates HCL syntax,
variable wiring, and provider constraints WITHOUT any AWS calls.

Gates:
- ``terraform`` binary must be on PATH.
- No LocalStack required.
- No AWS credentials required.

Why this exists: the three infra nodes (``attach_foundation_network``,
``provision_compute``, ``provision_data_layer``) call this wrapper at
runtime. If the modules drift from the var schemas the agent passes,
this test fails fast offline instead of crashing during a real ECS
deployment.

Note: First run will fetch the AWS provider into the terraform plugin
cache (~3min, ~900MB). Subsequent runs are fast. To prime the cache:
``$env:TF_PLUGIN_CACHE_DIR='C:\\Users\\<you>\\.terraform.d\\plugin-cache'``
before invoking pytest.
"""

from __future__ import annotations

import os
import shutil

import pytest

from app.agents.devops import tools
from app.core.config import get_settings

pytestmark = pytest.mark.integration

if shutil.which("terraform") is None:
    pytest.skip(
        "terraform binary not on PATH; skipping offline infra validate test",
        allow_module_level=True,
    )


@pytest.fixture(autouse=True)
def _real_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "devops_tools_mode", "real")
    # Speed up provider downloads if the caller hasn't set this.
    if not os.getenv("TF_PLUGIN_CACHE_DIR"):
        default = os.path.expanduser("~/.terraform.d/plugin-cache")
        os.makedirs(default, exist_ok=True)
        monkeypatch.setenv("TF_PLUGIN_CACHE_DIR", default)


ORG = "org-test-1234"
RUN = "run-test-5678"


async def test_networking_module_validates_offline() -> None:
    settings = get_settings()
    result = await tools.terraform_plan_module(
        module_name="networking",
        organization_id=ORG,
        run_id=RUN,
        vars={
            "aws_region": settings.foundation_aws_region,
            "vpc_id": settings.foundation_vpc_id,
            "private_subnet_ids": list(settings.foundation_private_subnet_ids),
            "public_subnet_ids": list(settings.foundation_public_subnet_ids),
            "availability_zones": list(settings.foundation_availability_zones),
        },
    )
    assert result["ok"] is True, {
        "returncode": result["returncode"],
        "init_stderr_tail": (result.get("init_stderr") or "")[-400:],
        "validate_stderr_tail": (result.get("validate_stderr") or "")[-400:],
    }
    assert result["returncode"] == 0
    assert result["module"] == "networking"
    assert "duration_ms" in result


async def test_data_layer_module_validates_offline() -> None:
    result = await tools.terraform_plan_module(
        module_name="data-layer",
        organization_id=ORG,
        run_id=RUN,
        vars={
            "aws_region": "ap-south-1",
            "private_subnet_ids": ["subnet-placeholder-a", "subnet-placeholder-b"],
            "rds_security_group_id": "sg-placeholder-rds",
            "redis_security_group_id": "sg-placeholder-redis",
        },
    )
    assert result["ok"] is True, {
        "returncode": result["returncode"],
        "init_stderr_tail": (result.get("init_stderr") or "")[-400:],
        "validate_stderr_tail": (result.get("validate_stderr") or "")[-400:],
    }
    assert result["returncode"] == 0


async def test_ecs_module_validates_offline_with_empty_services() -> None:
    result = await tools.terraform_plan_module(
        module_name="ecs",
        organization_id=ORG,
        run_id=RUN,
        vars={
            "aws_region": "ap-south-1",
            "services": {},
            "private_subnet_ids": ["subnet-placeholder-a", "subnet-placeholder-b"],
            "ecs_tasks_security_group_id": "sg-placeholder-ecs",
        },
    )
    assert result["ok"] is True, {
        "returncode": result["returncode"],
        "init_stderr_tail": (result.get("init_stderr") or "")[-400:],
        "validate_stderr_tail": (result.get("validate_stderr") or "")[-400:],
    }
    assert result["returncode"] == 0


async def test_unknown_module_name_raises() -> None:
    with pytest.raises(FileNotFoundError):
        await tools.terraform_plan_module(
            module_name="nonexistent-module",
            organization_id=ORG,
            run_id=RUN,
            vars={},
        )
