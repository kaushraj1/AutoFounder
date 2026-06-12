"""LocalStack integration tests for DevOps tool wrappers.

These exercise the real boto3 path against a local LocalStack container.
Skipped by default — set ``LOCALSTACK_RUNNING=1`` and start the container
via ``docker compose -f docker-compose.localstack.yml up -d`` first.

Coverage:
  * secrets_manager_create  -> SecretsManager: create + idempotent update
  * codedeploy_create_deployment -> CodeDeploy: create_deployment against a
    pre-created application + deployment group
  * route53_upsert -> Route53: create a hosted zone, UPSERT an A record
  * acm_request_certificate -> ACM: request a DNS-validated cert
  * http_health_check -> hits a 200 endpoint and asserts ok=True
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import boto3
import pytest

from app.agents.devops import tools
from app.core.config import get_settings


pytestmark = pytest.mark.localstack

if not os.getenv("LOCALSTACK_RUNNING"):
    pytest.skip(
        "LOCALSTACK_RUNNING is not set; skipping LocalStack integration tests",
        allow_module_level=True,
    )


LOCALSTACK_URL = os.getenv("LOCALSTACK_URL", "http://localhost:4566")


@pytest.fixture(autouse=True)
def _real_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "devops_tools_mode", "real")
    monkeypatch.setattr(settings, "aws_endpoint_url", LOCALSTACK_URL)
    monkeypatch.setattr(settings, "aws_region", "ap-south-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")


def _aws(service: str) -> Any:
    return boto3.client(
        service,
        endpoint_url=LOCALSTACK_URL,
        region_name="ap-south-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


async def test_secrets_manager_create_idempotent() -> None:
    name = f"af-test-secret-{uuid.uuid4().hex[:8]}"
    first = await tools.secrets_manager_create(
        name=name, values={"db_url": "postgres://x", "api_key": "k1"}
    )
    assert first["ok"] is True
    assert first["secret_arn"]
    assert sorted(first["keys"]) == ["api_key", "db_url"]

    # Re-issue with new values: hits the put_secret_value branch.
    second = await tools.secrets_manager_create(
        name=name, values={"db_url": "postgres://y", "api_key": "k2"}
    )
    assert second["ok"] is True
    assert second["secret_arn"]


async def test_codedeploy_create_deployment_real() -> None:
    cd = _aws("codedeploy")
    app_name = f"af-test-app-{uuid.uuid4().hex[:8]}"
    group_name = f"{app_name}-dg"
    cd.create_application(applicationName=app_name, computePlatform="ECS")
    # Minimal deployment group — LocalStack accepts a sparse spec.
    cd.create_deployment_group(
        applicationName=app_name,
        deploymentGroupName=group_name,
        serviceRoleArn="arn:aws:iam::000000000000:role/codedeploy-role",
    )

    res = await tools.codedeploy_create_deployment(
        app_name=app_name, deployment_group=group_name
    )
    assert res["ok"] is True
    assert res["deployment_id"]


async def test_route53_upsert_real() -> None:
    r53 = _aws("route53")
    zone_name = f"af-test-{uuid.uuid4().hex[:8]}.local."
    zone = r53.create_hosted_zone(
        Name=zone_name, CallerReference=f"af-{uuid.uuid4().hex}"
    )
    zone_id = zone["HostedZone"]["Id"].split("/")[-1]

    res = await tools.route53_upsert(
        zone_id=zone_id,
        record_name=f"api.{zone_name}",
        alb_dns_name="dualstack.example.elb.amazonaws.com",
    )
    assert res["ok"] is True
    assert res["change_id"]


async def test_acm_request_certificate_real() -> None:
    res = await tools.acm_request_certificate(domain="api.example-mvp.local")
    assert res["ok"] is True
    assert res["certificate_arn"]
    assert res["status"] == "PENDING_VALIDATION"


async def test_http_health_check_real_via_localstack_health() -> None:
    # LocalStack itself exposes a 200 health endpoint — convenient target.
    res = await tools.http_health_check(
        endpoint=f"{LOCALSTACK_URL}/_localstack/health"
    )
    assert res["ok"] is True
    assert res["status_code"] == 200
    assert res["latency_ms"] >= 0
