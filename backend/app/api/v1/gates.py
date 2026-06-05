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
from app.schemas.run import RunStatus

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

        # Update run status based on decision
        if decision.decision == GateState.approved:
            run_result = await db.session.execute(select(Run).where(Run.id == run_id))
            run = run_result.scalar_one_or_none()
            if run:
                run.status = RunStatus.running
        elif decision.decision == GateState.rejected:
            run_result = await db.session.execute(select(Run).where(Run.id == run_id))
            run = run_result.scalar_one_or_none()
            if run:
                run.status = RunStatus.failed

        await db.session.commit()
        await db.audit(
            "decide",
            "gates",
            str(gate_id),
            run_id=str(run_id),
            metadata={"decision": decision.decision},
        )

        gate_read = GateRead.model_validate(gate)

    return ResponseEnvelope(data=gate_read, meta=meta)
