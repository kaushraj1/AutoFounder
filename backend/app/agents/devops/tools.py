"""Structured async wrappers used by DevOps nodes.

These are scaffold implementations so the graph is runnable without cloud access.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base import ToolRegistryProtocol

logger = logging.getLogger("app.agents.devops.tools")


async def terraform_run(*, action: str, working_dir: str, vars: dict[str, Any]) -> dict[str, Any]:
	return {
		"ok": True,
		"action": action,
		"working_dir": working_dir,
		"vars": vars,
		"stdout": "scaffold terraform execution",
	}


async def secrets_manager_create(*, name: str, values: dict[str, str]) -> dict[str, Any]:
	return {"ok": True, "secret_name": name, "keys": sorted(values.keys())}


async def codedeploy_create_deployment(*, app_name: str, deployment_group: str) -> dict[str, Any]:
	return {
		"ok": True,
		"app_name": app_name,
		"deployment_group": deployment_group,
		"deployment_id": f"d-{app_name[:12]}",
	}


async def route53_upsert(*, zone_id: str, record_name: str, alb_dns_name: str) -> dict[str, Any]:
	return {
		"ok": True,
		"zone_id": zone_id,
		"record_name": record_name,
		"target": alb_dns_name,
	}


async def acm_request_certificate(*, domain: str) -> dict[str, Any]:
	return {"ok": True, "domain": domain, "status": "Issued"}


async def github_upsert_file(*, repo_url: str, path: str, content: str) -> dict[str, Any]:
	return {
		"ok": True,
		"repo_url": repo_url,
		"path": path,
		"bytes": len(content.encode("utf-8")),
	}


async def http_health_check(*, endpoint: str) -> dict[str, Any]:
	return {"ok": True, "endpoint": endpoint, "status_code": 200, "latency_ms": 120.0}


# Dispatch table consumed by LocalToolRegistry. Add new wrappers here.
_TOOL_DISPATCH = {
	"terraform_run": terraform_run,
	"secrets_manager_create": secrets_manager_create,
	"codedeploy_create_deployment": codedeploy_create_deployment,
	"route53_upsert": route53_upsert,
	"acm_request_certificate": acm_request_certificate,
	"github_upsert_file": github_upsert_file,
	"http_health_check": http_health_check,
}


class LocalToolRegistry(ToolRegistryProtocol):
	"""DevOps tool registry. Dispatches by name to scaffold wrappers above.

	When real AWS IAM is attached (ECS task role or local dev role), these
	scaffolds will be swapped for boto3-backed calls without changing this
	dispatch contract.
	"""

	async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
		fn = _TOOL_DISPATCH.get(tool_name)
		if fn is None:
			raise KeyError(f"DevOps tool '{tool_name}' not registered")
		logger.info("devops tool call: %s", tool_name)
		return await fn(**args)