"""DevOps tool wrappers.

Two modes (selected by ``settings.devops_tools_mode``):

* ``real`` (default): boto3 / PyGithub / httpx / subprocess. Targets the real
  AWS account, or LocalStack when ``settings.aws_endpoint_url`` is set.
* ``scaffold``: returns canned dicts so unit suites can exercise the LangGraph
  topology without faking every cloud client. Enable with
  ``DEVOPS_TOOLS_MODE=scaffold`` (or set it inline in a fixture).

All wrappers are async at the boundary. Sync SDK calls (boto3, PyGithub,
subprocess) are pushed to a thread via ``asyncio.to_thread`` so the event
loop is not blocked.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
import tempfile
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import httpx

from app.agents.base import ToolRegistryProtocol
from app.core.config import get_settings
from app.core.logging import get_logger

logger = logging.getLogger("app.agents.devops.tools")
# JSON-structured logger for the new Phase 1D code paths so CloudWatch /
# ELK can filter on organization_id, run_id, module, event, returncode, etc.
slog = get_logger("app.agents.devops.tools")

TERRAFORM_TEMPLATES_DIR = Path(__file__).parent / "terraform_templates"


# ---------------------------------------------------------------------------
# Mode helpers
# ---------------------------------------------------------------------------


def _is_scaffold_mode() -> bool:
    return (get_settings().devops_tools_mode or "real").lower() != "real"


def _boto3_client(service: str) -> Any:
    """Build a boto3 client honouring the LocalStack endpoint override."""
    import boto3  # local import so unit suites don't pay the cost

    settings = get_settings()
    kwargs: dict[str, Any] = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client(service, **kwargs)


# ---------------------------------------------------------------------------
# Terraform
# ---------------------------------------------------------------------------


async def terraform_run(*, action: str, working_dir: str, vars: dict[str, Any]) -> dict[str, Any]:
    """Invoke the local terraform binary against ``working_dir``.

    ``action`` is one of ``init``, ``plan``, ``apply``, ``destroy``. ``vars``
    are surfaced as ``-var key=value`` flags. Returns stdout + exit code so the
    caller can decide whether to fail the run or persist the plan file.
    """
    if _is_scaffold_mode():
        return {
            "ok": True,
            "action": action,
            "working_dir": working_dir,
            "vars": vars,
            "stdout": "scaffold terraform execution",
            "returncode": 0,
        }

    settings = get_settings()
    bin_path = settings.devops_terraform_binary
    cmd: list[str] = [bin_path]
    if action == "init":
        cmd += ["init", "-input=false", "-no-color"]
    elif action == "plan":
        cmd += ["plan", "-input=false", "-no-color", "-out=tfplan"]
    elif action == "apply":
        cmd += ["apply", "-input=false", "-no-color", "-auto-approve"]
    elif action == "destroy":
        cmd += ["destroy", "-input=false", "-no-color", "-auto-approve"]
    else:
        raise ValueError(f"Unsupported terraform action: {action}")

    for key, value in (vars or {}).items():
        cmd += ["-var", f"{key}={value}"]

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 — caller-controlled args, no shell
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=600,
        )

    proc = await asyncio.to_thread(_run)
    return {
        "ok": proc.returncode == 0,
        "action": action,
        "working_dir": working_dir,
        "vars": vars,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "returncode": proc.returncode,
    }


def _stage_terraform_module(*, module_name: str, organization_id: str, run_id: str) -> Path:
    """Copy ``terraform_templates/<module>`` + ``_shared`` into a fresh tmp dir.

    Strips the partial S3 backend so Path A (plan-only, no AWS) can ``init``
    with the default local backend. When the apply path lands, drop the
    backend-strip and pass real ``-backend-config`` instead.
    """
    src = TERRAFORM_TEMPLATES_DIR / module_name
    if not src.is_dir():
        raise FileNotFoundError(f"Unknown terraform module: {module_name} ({src})")
    shared = TERRAFORM_TEMPLATES_DIR / "_shared"

    work = Path(tempfile.mkdtemp(prefix=f"af-tf-{module_name}-{organization_id[:8]}-{run_id[:8]}-"))
    for entry in src.iterdir():
        if entry.is_file():
            shutil.copy2(entry, work / entry.name)
    if shared.is_dir():
        for entry in shared.iterdir():
            if entry.is_file() and entry.name != "backend.tf":
                dest = work / entry.name
                if not dest.exists():
                    shutil.copy2(entry, dest)
    return work


async def terraform_plan_module(
    *,
    module_name: str,
    organization_id: str,
    run_id: str,
    vars: dict[str, Any] | None = None,
    extra_files: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Stage a per-tenant terraform module into a tmp dir, run init + validate.

    Path A (offline, no AWS credentials) — validates HCL syntax, variable
    wiring, provider constraints, and module schema without making any AWS
    API calls. ``terraform plan`` is unsafe in this mode because modules
    with data sources (e.g. ``aws_vpc``, ``aws_subnet`` in the networking
    module) require live AWS auth even during plan. ``terraform validate``
    is the canonical static-analysis check and does NOT need credentials.

    ``extra_files`` lets callers drop generated ``.tf.json`` files (e.g.
    per-service ECS task defs) into the workdir before validate.

    Returns a dict with ``ok``, ``returncode`` (0 = valid; non-zero =
    error), ``working_dir``, ``init_stdout/stderr``,
    ``validate_stdout/stderr``, ``duration_ms``. The dict key
    ``plan_stdout`` / ``plan_stderr`` is kept as an alias for
    ``validate_*`` so downstream report templates don't break when the
    apply path lands.
    """
    if _is_scaffold_mode():
        slog.info(
            "terraform_plan_module.scaffold",
            module=module_name,
            organization_id=organization_id,
            run_id=run_id,
        )
        return {
            "ok": True,
            "module": module_name,
            "working_dir": "",
            "returncode": 0,
            "init_stdout": "scaffold",
            "validate_stdout": "scaffold",
            "plan_stdout": "scaffold",
            "duration_ms": 0,
        }

    started = time.perf_counter()
    work = _stage_terraform_module(
        module_name=module_name, organization_id=organization_id, run_id=run_id
    )
    slog.info(
        "terraform_plan_module.staged",
        module=module_name,
        organization_id=organization_id,
        run_id=run_id,
        working_dir=str(work),
        vars_keys=sorted((vars or {}).keys()),
        extra_files=sorted((extra_files or {}).keys()),
    )

    for filename, contents in (extra_files or {}).items():
        (work / filename).write_text(contents, encoding="utf-8")

    tfvars_payload = {
        "organization_id": organization_id,
        "run_id": run_id,
        **(vars or {}),
    }
    (work / "terraform.auto.tfvars.json").write_text(
        json.dumps(tfvars_payload, default=str, indent=2), encoding="utf-8"
    )

    settings = get_settings()
    bin_path = settings.devops_terraform_binary

    def _run(cmd: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 — caller-controlled args, no shell
            cmd,
            cwd=str(work),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    # init -backend=false avoids any S3/DynamoDB lookups (the partial backend
    # in _shared/backend.tf is already stripped during staging, but this is
    # belt-and-braces for Path A).
    init_cmd = [bin_path, "init", "-input=false", "-no-color", "-backend=false"]
    slog.info(
        "terraform_plan_module.init.start",
        module=module_name,
        organization_id=organization_id,
        run_id=run_id,
        cmd=init_cmd,
    )
    init_proc = await asyncio.to_thread(_run, init_cmd)
    slog.info(
        "terraform_plan_module.init.done",
        module=module_name,
        organization_id=organization_id,
        run_id=run_id,
        returncode=init_proc.returncode,
        stderr_tail=init_proc.stderr[-500:] if init_proc.stderr else "",
    )
    if init_proc.returncode != 0:
        return {
            "ok": False,
            "module": module_name,
            "working_dir": str(work),
            "returncode": init_proc.returncode,
            "init_stdout": init_proc.stdout,
            "init_stderr": init_proc.stderr,
            "validate_stdout": "",
            "validate_stderr": "",
            "plan_stdout": "",
            "plan_stderr": "",
            "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        }

    validate_cmd = [bin_path, "validate", "-no-color", "-json"]
    slog.info(
        "terraform_plan_module.validate.start",
        module=module_name,
        organization_id=organization_id,
        run_id=run_id,
        cmd=validate_cmd,
    )
    validate_proc = await asyncio.to_thread(_run, validate_cmd)
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    ok = validate_proc.returncode == 0
    slog.info(
        "terraform_plan_module.validate.done",
        module=module_name,
        organization_id=organization_id,
        run_id=run_id,
        returncode=validate_proc.returncode,
        ok=ok,
        duration_ms=duration_ms,
        stderr_tail=validate_proc.stderr[-500:] if validate_proc.stderr else "",
    )
    return {
        "ok": ok,
        "module": module_name,
        "working_dir": str(work),
        "returncode": validate_proc.returncode,
        "init_stdout": init_proc.stdout,
        "init_stderr": init_proc.stderr,
        "validate_stdout": validate_proc.stdout,
        "validate_stderr": validate_proc.stderr,
        "plan_stdout": validate_proc.stdout,
        "plan_stderr": validate_proc.stderr,
        "duration_ms": duration_ms,
    }


# ---------------------------------------------------------------------------
# AWS Secrets Manager
# ---------------------------------------------------------------------------


async def secrets_manager_create(*, name: str, values: dict[str, str]) -> dict[str, Any]:
    """Create-or-update a Secrets Manager secret with a JSON blob of ``values``."""
    if _is_scaffold_mode():
        return {"ok": True, "secret_name": name, "keys": sorted(values.keys())}

    import json

    client = _boto3_client("secretsmanager")
    payload = json.dumps(values)

    def _put() -> dict[str, Any]:
        try:
            resp = client.create_secret(Name=name, SecretString=payload)
        except client.exceptions.ResourceExistsException:
            resp = client.put_secret_value(SecretId=name, SecretString=payload)
        return resp

    resp = await asyncio.to_thread(_put)
    return {
        "ok": True,
        "secret_name": name,
        "secret_arn": resp.get("ARN") or resp.get("Arn"),
        "keys": sorted(values.keys()),
    }


# ---------------------------------------------------------------------------
# AWS CodeDeploy
# ---------------------------------------------------------------------------


async def codedeploy_create_application(
    *, app_name: str, compute_platform: str = "ECS"
) -> dict[str, Any]:
    """Idempotently create a CodeDeploy application."""
    if _is_scaffold_mode():
        return {"ok": True, "app_name": app_name, "compute_platform": compute_platform}

    client = _boto3_client("codedeploy")

    def _create() -> dict[str, Any]:
        try:
            return client.create_application(
                applicationName=app_name, computePlatform=compute_platform
            )
        except client.exceptions.ApplicationAlreadyExistsException:
            return {"applicationId": None, "existed": True}

    resp = await asyncio.to_thread(_create)
    return {
        "ok": True,
        "app_name": app_name,
        "compute_platform": compute_platform,
        "application_id": resp.get("applicationId"),
        "existed": resp.get("existed", False),
    }


async def codedeploy_create_deployment_group(
    *, app_name: str, deployment_group: str, service_role_arn: str
) -> dict[str, Any]:
    """Idempotently create a CodeDeploy deployment group."""
    if _is_scaffold_mode():
        return {
            "ok": True,
            "app_name": app_name,
            "deployment_group": deployment_group,
        }

    client = _boto3_client("codedeploy")

    def _create() -> dict[str, Any]:
        try:
            return client.create_deployment_group(
                applicationName=app_name,
                deploymentGroupName=deployment_group,
                serviceRoleArn=service_role_arn,
            )
        except client.exceptions.DeploymentGroupAlreadyExistsException:
            return {"deploymentGroupId": None, "existed": True}

    resp = await asyncio.to_thread(_create)
    return {
        "ok": True,
        "app_name": app_name,
        "deployment_group": deployment_group,
        "deployment_group_id": resp.get("deploymentGroupId"),
        "existed": resp.get("existed", False),
    }


async def codedeploy_create_deployment(*, app_name: str, deployment_group: str) -> dict[str, Any]:
    if _is_scaffold_mode():
        return {
            "ok": True,
            "app_name": app_name,
            "deployment_group": deployment_group,
            "deployment_id": f"d-{app_name[:12]}",
        }

    client = _boto3_client("codedeploy")

    def _create() -> dict[str, Any]:
        return client.create_deployment(
            applicationName=app_name,
            deploymentGroupName=deployment_group,
        )

    resp = await asyncio.to_thread(_create)
    return {
        "ok": True,
        "app_name": app_name,
        "deployment_group": deployment_group,
        "deployment_id": resp.get("deploymentId"),
    }


# ---------------------------------------------------------------------------
# AWS Route 53
# ---------------------------------------------------------------------------


async def route53_upsert(*, zone_id: str, record_name: str, alb_dns_name: str) -> dict[str, Any]:
    if _is_scaffold_mode():
        return {
            "ok": True,
            "zone_id": zone_id,
            "record_name": record_name,
            "target": alb_dns_name,
        }

    client = _boto3_client("route53")
    change_batch = {
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": record_name,
                    "Type": "A",
                    "AliasTarget": {
                        # Default to us-east-1 zone if the caller doesn't override;
                        # ALB zone hosted-id lookup belongs in the node, not here.
                        "HostedZoneId": "Z35SXDOTRQ7X7K",
                        "DNSName": alb_dns_name,
                        "EvaluateTargetHealth": False,
                    },
                },
            }
        ]
    }

    def _upsert() -> dict[str, Any]:
        return client.change_resource_record_sets(HostedZoneId=zone_id, ChangeBatch=change_batch)

    resp = await asyncio.to_thread(_upsert)
    return {
        "ok": True,
        "zone_id": zone_id,
        "record_name": record_name,
        "target": alb_dns_name,
        "change_id": resp.get("ChangeInfo", {}).get("Id"),
    }


# ---------------------------------------------------------------------------
# AWS ACM
# ---------------------------------------------------------------------------


async def acm_request_certificate(*, domain: str) -> dict[str, Any]:
    if _is_scaffold_mode():
        return {"ok": True, "domain": domain, "status": "Issued"}

    client = _boto3_client("acm")

    def _request() -> dict[str, Any]:
        return client.request_certificate(DomainName=domain, ValidationMethod="DNS")

    resp = await asyncio.to_thread(_request)
    return {
        "ok": True,
        "domain": domain,
        "certificate_arn": resp.get("CertificateArn"),
        "status": "PENDING_VALIDATION",
    }


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------


async def github_upsert_file(*, repo_url: str, path: str, content: str) -> dict[str, Any]:
    """Create-or-update ``path`` on the default branch of ``repo_url``.

    Honors ``settings.devops_github_dry_run`` — when true (the default),
    no commit is pushed; the wrapper returns ``dry_run=True`` and logs the
    payload size. Requires ``settings.github_token`` in real-push mode.
    """
    settings = get_settings()
    scaffold = _is_scaffold_mode()

    if scaffold:
        return {
            "ok": True,
            "repo_url": repo_url,
            "path": path,
            "bytes": len(content.encode("utf-8")),
        }

    if settings.devops_github_dry_run:
        logger.info(
            "github_upsert_file dry-run: repo=%s path=%s bytes=%d",
            repo_url,
            path,
            len(content.encode("utf-8")),
        )
        return {
            "ok": True,
            "repo_url": repo_url,
            "path": path,
            "bytes": len(content.encode("utf-8")),
            "dry_run": True,
        }

    token = settings.github_token
    if not token:
        raise RuntimeError(
            "github_upsert_file: settings.github_token is empty; "
            "set GITHUB_TOKEN or flip devops_github_dry_run back to True"
        )

    from github import Github  # PyGithub

    def _commit() -> dict[str, Any]:
        gh = Github(token)
        # Accept either full URL or "owner/repo"
        slug = repo_url
        if "://" in slug:
            slug = slug.split("github.com/", 1)[-1]
        slug = slug.rstrip("/").removesuffix(".git")
        repo = gh.get_repo(slug)
        msg = f"chore(ci): autofounder upsert {path}"
        try:
            existing = repo.get_contents(path, ref=repo.default_branch)
            sha = getattr(existing, "sha", None) if not isinstance(existing, list) else None
            res = repo.update_file(path, msg, content, sha or "", branch=repo.default_branch)
        except Exception:
            res = repo.create_file(path, msg, content, branch=repo.default_branch)
        commit = res.get("commit") if isinstance(res, dict) else None
        sha_out = commit.sha if commit is not None else None
        return {"branch": repo.default_branch, "commit_sha": sha_out}

    info = await asyncio.to_thread(_commit)
    return {
        "ok": True,
        "repo_url": repo_url,
        "path": path,
        "bytes": len(content.encode("utf-8")),
        "branch": info["branch"],
        "commit_sha": info["commit_sha"],
        "dry_run": False,
    }


# ---------------------------------------------------------------------------
# HTTP health check
# ---------------------------------------------------------------------------


async def http_health_check(*, endpoint: str) -> dict[str, Any]:
    """GET ``endpoint`` and report status + latency."""
    if _is_scaffold_mode():
        return {
            "ok": True,
            "endpoint": endpoint,
            "status_code": 200,
            "latency_ms": 120.0,
        }

    import time as _time

    timeout = httpx.Timeout(10.0, connect=5.0)
    start = _time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(endpoint)
        latency_ms = (_time.perf_counter() - start) * 1000.0
        return {
            "ok": 200 <= resp.status_code < 400,
            "endpoint": endpoint,
            "status_code": resp.status_code,
            "latency_ms": round(latency_ms, 1),
        }
    except httpx.HTTPError as exc:
        latency_ms = (_time.perf_counter() - start) * 1000.0
        return {
            "ok": False,
            "endpoint": endpoint,
            "status_code": 0,
            "latency_ms": round(latency_ms, 1),
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


_TOOL_DISPATCH: dict[str, Callable[..., Awaitable[dict[str, Any]]]] = {
    "terraform_run": terraform_run,
    "terraform_plan_module": terraform_plan_module,
    "secrets_manager_create": secrets_manager_create,
    "codedeploy_create_application": codedeploy_create_application,
    "codedeploy_create_deployment_group": codedeploy_create_deployment_group,
    "codedeploy_create_deployment": codedeploy_create_deployment,
    "route53_upsert": route53_upsert,
    "acm_request_certificate": acm_request_certificate,
    "github_upsert_file": github_upsert_file,
    "http_health_check": http_health_check,
}


class LocalToolRegistry(ToolRegistryProtocol):
    """DevOps tool registry. Real boto3/PyGithub/subprocess by default;
    falls back to canned dicts when ``settings.devops_tools_mode='scaffold'``.
    """

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        fn = _TOOL_DISPATCH.get(tool_name)
        if fn is None:
            raise KeyError(f"DevOps tool '{tool_name}' not registered")
        slog.info("devops.tool.call", tool=tool_name, arg_keys=sorted(args.keys()))
        started = time.perf_counter()
        try:
            result = await fn(**args)
        except Exception as exc:
            slog.error(
                "devops.tool.error",
                tool=tool_name,
                error_type=type(exc).__name__,
                error=str(exc)[:500],
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
            )
            raise
        slog.info(
            "devops.tool.done",
            tool=tool_name,
            ok=bool(result.get("ok")) if isinstance(result, dict) else True,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        return result
