"""Founder Portal endpoint for the DevOps agent's pre-flight HITL spend gate.

This is a **second**, narrower HITL surface — distinct from `gates.py`:

* `gates.py` decides ORCHESTRATOR-level gates (`validation_gate`,
  `architecture_gate`, `infra_spend_gate`, `launch_gate`). Each is a `Gate`
  DB row attached to a `Run`; the decision drives `OrchestratorEngine.resume()`
  (or an SQS `gate.decided` event) which lifts a LangGraph `interrupt_before`.

* This file decides the DEVOPS-INTERNAL pre-flight gate that lives inside the
  `DevOpsAgent` subgraph (`app/agents/devops/nodes/hitl_spend_gate.py`). That
  node auto-approves under `settings.devops_spend_gate_cap_usd` ($150) and
  otherwise polls Redis at `{devops_hitl_redis_key_prefix}:{run_id}`. This
  endpoint writes the approve/reject value into that key so the polling loop
  can resume the subgraph before any AWS API call.

There is **no** `Gate` row for this decision (the DevOps subgraph runs entirely
inside the Pillar 5 orchestrator node), so we don't touch the gates table. We
still scope by tenant (the run must belong to `principal.organization_id`) and
emit an audit record via `UDAL.audit`.
"""

from __future__ import annotations

import uuid
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import get_meta, get_principal, get_redis, get_udal
from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError
from app.core.security import Principal
from app.db.udal import UDAL
from app.models.run import Run
from app.schemas.common import Meta, ResponseEnvelope
from app.schemas.devops_approval import (
    DevOpsSpendApprovalRequest,
    DevOpsSpendApprovalResponse,
)

router = APIRouter(prefix="/runs/{run_id}", tags=["devops-approvals"])


@router.post(
    "/devops-spend-approval",
    response_model=ResponseEnvelope[DevOpsSpendApprovalResponse],
    summary="Approve / reject the DevOps agent's pre-flight AWS spend estimate",
)
async def decide_devops_spend(
    run_id: uuid.UUID,
    body: DevOpsSpendApprovalRequest,
    udal: Annotated[UDAL, Depends(get_udal)],
    meta: Annotated[Meta, Depends(get_meta)],
    principal: Annotated[Principal, Depends(get_principal)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> ResponseEnvelope[DevOpsSpendApprovalResponse]:
    """Resolve the DevOps subgraph's pre-flight HITL spend gate via Redis.

    The DevOps agent polls Redis key
    ``{settings.devops_hitl_redis_key_prefix}:{run_id}`` while waiting for the
    founder's decision; writing `approved` or `rejected` here unblocks it.
    """
    settings = get_settings()

    # 1. Tenant scope: UDAL/RLS already filters by tenant when reading the row.
    async with udal.relational() as db:
        run_result = await db.session.execute(select(Run).where(Run.id == run_id))
        run = run_result.scalar_one_or_none()
        if run is None:
            raise NotFoundError("Run not found")

        redis_key = f"{settings.devops_hitl_redis_key_prefix}:{run_id}"

        # 2. Refuse to overwrite an existing decision (idempotency + audit clarity).
        existing = await redis.get(redis_key)
        if existing is not None:
            existing_value = (
                (existing if isinstance(existing, str) else existing.decode("utf-8"))
                .strip()
                .lower()
            )
            if existing_value in {"approved", "rejected"}:
                raise ConflictError(
                    f"DevOps spend gate for run {run_id} already decided ({existing_value})"
                )

        # 3. Write the decision. TTL = poll-timeout + buffer so the key
        # disappears after the subgraph has had a chance to read it.
        ttl_seconds = int(settings.devops_hitl_timeout_seconds) + 300
        await redis.set(redis_key, body.decision.value, ex=ttl_seconds)

        await db.audit(
            "decide",
            "devops_spend_gate",
            str(run_id),
            run_id=str(run_id),
            metadata={
                "decision": body.decision.value,
                "notes": body.notes,
                "redis_key": redis_key,
            },
        )

    return ResponseEnvelope(
        data=DevOpsSpendApprovalResponse(
            run_id=run_id,
            decision=body.decision,
            redis_key=redis_key,
        ),
        meta=meta,
    )
