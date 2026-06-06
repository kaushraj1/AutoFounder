"""HITL gate manager — handles creation, transitions, and timeouts (AF-034)."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gate import Gate
from app.orchestrator.hitl.notifier import emit_gate_required

logger = logging.getLogger(__name__)


def safe_uuid(val: Any) -> Any:
    """Safely parse a UUID, returning the original value if it's not a valid UUID string."""
    if not val:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, TypeError):
        return val


# Map LangGraph gate nodes to database gate kinds
NODE_TO_GATE_KIND = {
    "validation_gate": "validation_approve",
    "architecture_gate": "architecture_approve",
    "infra_spend_gate": "infra_spend_approve",
    "launch_gate": "launch_approve",
}

# Map LangGraph gate nodes to the corresponding state pillar index
NODE_TO_PILLAR = {
    "validation_gate": 1,
    "architecture_gate": 2,
    "infra_spend_gate": 5,
    "launch_gate": 6,
}


async def check_and_create_gate(
    run_id: str,
    org_id: str,
    snapshot: Any,
    db_session: AsyncSession,
    graph: Any,
    config: dict[str, Any],
) -> None:
    """Check if the graph is paused at an interrupt gate. If so, create the DB record and notify."""
    next_nodes = list(snapshot.next or ())
    if not next_nodes:
        return

    gate_node = next_nodes[0]
    if gate_node not in NODE_TO_GATE_KIND:
        return

    gate_kind = NODE_TO_GATE_KIND[gate_node]
    pillar = NODE_TO_PILLAR.get(gate_node, 1)

    # Check if a pending gate of this kind already exists for the run
    result = await db_session.execute(
        select(Gate).where(
            Gate.run_id == safe_uuid(run_id),
            Gate.kind == gate_kind,
            Gate.state == "pending",
        )
    )
    existing: Any = None
    if hasattr(result, "scalar_one_or_none"):
        existing = result.scalar_one_or_none()
    elif hasattr(result, "scalars"):
        existing = result.scalars().first()
    else:
        existing = result.first()

    if existing:
        if isinstance(existing, tuple):
            existing = existing[0]
        # If it already exists, make sure graph active_gate_id is in sync
        current_active = (snapshot.values or {}).get("active_gate_id")
        if not current_active:
            await graph.aupdate_state(
                config,
                {
                    "active_gate_id": str(existing.id)
                    if not isinstance(existing, dict)
                    else str(existing.get("id"))
                },
            )
        return

    # Extract display data from snapshot values
    payload: dict[str, Any] = {}
    if gate_kind == "validation_approve":
        payload = snapshot.values.get("strategy_output") or {}
    elif gate_kind == "architecture_approve":
        payload = snapshot.values.get("architecture_output") or {}
    elif gate_kind == "infra_spend_approve":
        payload = snapshot.values.get("deployment_output") or {}
    elif gate_kind == "launch_approve":
        payload = snapshot.values.get("marketing_output") or {}

    # Define a default timeout of 24 hours
    timeout_at = datetime.now(UTC) + timedelta(hours=24)
    gate_id = uuid.uuid4()

    logger.info("Creating pending HITL gate: run=%s, kind=%s, id=%s", run_id, gate_kind, gate_id)

    gate = Gate(
        id=gate_id,
        run_id=safe_uuid(run_id),
        organization_id=safe_uuid(org_id),
        kind=gate_kind,
        state="pending",
        payload=payload,
        timeout_at=timeout_at,
    )
    if hasattr(db_session, "add"):
        db_session.add(gate)
    if hasattr(db_session, "commit"):
        await db_session.commit()

    # Inject active_gate_id back into LangGraph state
    await graph.aupdate_state(config, {"active_gate_id": str(gate_id)})

    # Emit gate.required event
    await emit_gate_required(
        run_id=run_id,
        org_id=org_id,
        pillar=pillar,
        gate_id=str(gate_id),
        kind=gate_kind,
        display_data=payload,
        timeout_at=timeout_at,
    )


async def check_gate_timeouts(db_session: AsyncSession, engine: Any) -> None:
    """Find pending gates that have exceeded their timeout and transition them to timed_out."""
    now = datetime.now(UTC)
    result = await db_session.execute(
        select(Gate).where(
            Gate.state == "pending",
            Gate.timeout_at <= now,
        )
    )
    timed_out_gates: Any
    if hasattr(result, "scalars"):
        timed_out_gates = result.scalars().all()
    else:
        timed_out_gates = result.all()

    for item in timed_out_gates:
        gate: Any = item[0] if isinstance(item, tuple) else item
        logger.warning("HITL gate timed out: gate=%s, run=%s", gate.id, gate.run_id)
        gate.state = "timed_out"
        if hasattr(db_session, "commit"):
            await db_session.commit()

        # Resume engine under timed_out decision
        await engine.resume(str(gate.run_id), gate_decision="timed_out")
