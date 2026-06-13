"""Create per-run secrets in AWS Secrets Manager.

Calls ``secrets_manager_create`` for every unique secret name referenced
by the coder's services. Tool wrapper handles scaffold vs real boto3.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agents.devops.schema import NodeStatus, NodeTrace, SecretRef
from app.core.logging import bind_log_context


async def provision_secrets(state: dict, agent: Any | None = None) -> dict:
    state = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)
    organization_id = state.get("organization_id", "tenant")
    run_prefix = str(state.get("run_id", "run"))[:8]
    bind_log_context(
        organization_id=str(state.get("organization_id", "")),
        run_id=str(state.get("run_id", "")),
        agent_id="devops",
        node="provision_secrets",
    )
    secret_names: set[str] = set()

    for service in state.get("services", []):
        for ref in service.get("env_secret_refs", []):
            if ref:
                secret_names.add(ref)

    secrets: list[SecretRef] = []
    for name in sorted(secret_names):
        full_name = f"{organization_id[:16]}/{run_prefix}/{name}"
        secret_arn: str | None = None
        if agent is not None:
            try:
                result = await agent._call_tool(
                    "secrets_manager_create",
                    {"name": full_name, "values": {"value": "TBD"}},
                )
                secret_arn = result.get("secret_arn")
            except Exception:
                secret_arn = None
        secrets.append(
            SecretRef(
                secret_name=full_name,
                secret_arn=secret_arn,
                keys=["value"],
            )
        )

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
