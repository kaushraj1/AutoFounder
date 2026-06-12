"""Create per-run secrets in AWS Secrets Manager (scaffold implementation)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import NodeStatus, NodeTrace, SecretRef


async def provision_secrets(state: dict) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	secret_names: set[str] = set()

	for service in state.get("services", []):
		for ref in service.get("env_secret_refs", []):
			if ref:
				secret_names.add(ref)

	secrets = [SecretRef(secret_name=name, keys=["value"]) for name in sorted(secret_names)]
	return {
		"secrets": secrets,
		"node_traces": [
			NodeTrace(
				node="provision_secrets",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}