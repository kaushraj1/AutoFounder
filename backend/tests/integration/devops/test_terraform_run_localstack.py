"""LocalStack integration test for the ``terraform_run`` tool wrapper.

Runs ``terraform init`` + ``apply`` against a minimal HCL module that
creates an S3 bucket via the LocalStack endpoint, then verifies the
bucket exists with the AWS SDK and tears it down with ``destroy``.

Gated by ``LOCALSTACK_RUNNING=1`` plus the ``terraform`` binary on PATH.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

import boto3
import pytest

from app.agents.devops import tools
from app.core.config import get_settings


pytestmark = pytest.mark.localstack

if not os.getenv("LOCALSTACK_RUNNING"):
	pytest.skip(
		"LOCALSTACK_RUNNING is not set; skipping terraform LocalStack test",
		allow_module_level=True,
	)

if shutil.which("terraform") is None:
	pytest.skip(
		"terraform binary not on PATH; skipping terraform LocalStack test",
		allow_module_level=True,
	)


LOCALSTACK_URL = os.getenv("LOCALSTACK_URL", "http://localhost:4566")
FIXTURE_DIR = Path(__file__).parent / "terraform_fixtures" / "s3_bucket"


@pytest.fixture(autouse=True)
def _real_mode(monkeypatch: pytest.MonkeyPatch) -> None:
	settings = get_settings()
	monkeypatch.setattr(settings, "devops_tools_mode", "real")
	monkeypatch.setattr(settings, "aws_endpoint_url", LOCALSTACK_URL)
	monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
	monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
	monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")


def _s3_client() -> Any:
	return boto3.client(
		"s3",
		endpoint_url=LOCALSTACK_URL,
		region_name="ap-south-1",
		aws_access_key_id="test",
		aws_secret_access_key="test",
	)


async def test_terraform_run_creates_s3_bucket_on_localstack(
	tmp_path: Path,
) -> None:
	# Copy the fixture module into a tmp dir so terraform state stays
	# scoped to this test invocation.
	work_dir = tmp_path / "tf"
	shutil.copytree(FIXTURE_DIR, work_dir)

	bucket_name = f"af-tf-test-{uuid.uuid4().hex[:10]}"
	vars_ = {
		"endpoint_url": LOCALSTACK_URL,
		"bucket_name": bucket_name,
	}

	init = await tools.terraform_run(
		action="init", working_dir=str(work_dir), vars={}
	)
	assert init["returncode"] == 0, init.get("stderr")
	assert init["ok"] is True

	apply = await tools.terraform_run(
		action="apply", working_dir=str(work_dir), vars=vars_
	)
	assert apply["returncode"] == 0, apply.get("stderr")
	assert apply["ok"] is True

	# Verify the bucket actually exists on LocalStack.
	s3 = _s3_client()
	existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
	assert bucket_name in existing

	# Clean up.
	destroy = await tools.terraform_run(
		action="destroy", working_dir=str(work_dir), vars=vars_
	)
	assert destroy["returncode"] == 0, destroy.get("stderr")
