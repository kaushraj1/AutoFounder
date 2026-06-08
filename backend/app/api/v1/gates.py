"""HITL gate endpoints."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import get_meta, get_principal, get_udal
from app.core.errors import ConflictError, NotFoundError
from app.core.security import Principal
from app.db.udal import UDAL
from app.models.gate import Gate
from app.models.run import Run
from app.schemas.common import Meta, ResponseEnvelope
from app.schemas.gate import GateDecision, GateRead, GateState

router = APIRouter(prefix="/runs/{run_id}/gates", tags=["gates"])


@router.post(
    "/{gate_id}",
    response_model=ResponseEnvelope[GateRead],
    summary="Approve / reject a HITL gate",
)
async def decide_gate(
    run_id: uuid.UUID,
    gate_id: uuid.UUID,
    decision: GateDecision,
    udal: Annotated[UDAL, Depends(get_udal)],
    meta: Annotated[Meta, Depends(get_meta)],
    principal: Annotated[Principal, Depends(get_principal)],
) -> ResponseEnvelope[GateRead]:
    """Approve or reject a pending human-in-the-loop gate approval."""
    async with udal.relational() as db:
        # Check if gate exists for this run
        result = await db.session.execute(
            select(Gate).where(Gate.id == gate_id, Gate.run_id == run_id)
        )
        gate = result.scalar_one_or_none()
        if not gate:
            raise NotFoundError("Gate not found for specified run")

        if gate.state != GateState.pending:
            raise ConflictError("Gate has already been decided")

        # Update gate decision state
        gate.state = decision.decision
        gate.decided_by = principal.organization_id
        gate.decided_at = datetime.now(UTC)

        # Get run to determine pillar and update status
        run_result = await db.session.execute(select(Run).where(Run.id == run_id))
        run = run_result.scalar_one_or_none()
        pillar = int(run.pillar) if run and run.pillar and run.pillar.isdigit() else 1

        if run:
            if decision.decision == GateState.approved:
                run.status = "running"
            elif decision.decision == GateState.rejected:
                run.status = "failed"

        await db.session.commit()
        await db.audit(
            "decide",
            "gates",
            str(gate_id),
            run_id=str(run_id),
            metadata={"decision": decision.decision},
        )

        gate_read = GateRead.model_validate(gate)

    # Trigger resume or publish event outside transaction (AF-034)
    from app.core.config import get_settings

    settings = get_settings()

    if settings.sqs_gate_decisions_queue_url:
        from app.orchestrator.events.producer import event_producer

        await event_producer.publish_event(
            event_type="gate.decided",
            organization_id=principal.organization_id,
            run_id=str(run_id),
            pillar=pillar,
            payload={
                "run_id": str(run_id),
                "gate_id": str(gate_id),
                "decision": decision.decision,
                "pivot_text": decision.notes,
            },
        )
    else:
        from app.db.redis_pool import get_redis
        from app.db.session import SessionLocal
        from app.orchestrator.engine import OrchestratorEngine

        engine = OrchestratorEngine(session_factory=SessionLocal, redis=get_redis())
        await engine.resume(
            run_id=str(run_id),
            gate_decision=decision.decision,
            pivot_text=decision.notes,
        )

    return ResponseEnvelope(data=gate_read, meta=meta)
