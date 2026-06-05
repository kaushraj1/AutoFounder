"""LLMOps FinOps cost telemetry endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.api.deps import get_meta, get_udal
from app.db.udal import UDAL
from app.schemas.common import Meta, ResponseEnvelope
from app.schemas.cost import CostRead

router = APIRouter(prefix="/llmops", tags=["llmops"])


@router.get("/cost", response_model=ResponseEnvelope[CostRead], summary="Get FinOps cost telemetry")
async def get_cost(
    udal: Annotated[UDAL, Depends(get_udal)],
    meta: Annotated[Meta, Depends(get_meta)],
) -> ResponseEnvelope[CostRead]:
    """Retrieve the accumulated token usage costs across all runs for the tenant."""
    async with udal.relational() as db:
        # Compute sum from the cost_ledger table
        result = await db.session.execute(
            text("SELECT COALESCE(SUM(cost_usd), 0.0) FROM cost_ledger")
        )
        total_cost = result.scalar() or 0.0
        await db.audit("read", "cost_telemetry")

        cost_read = CostRead(total_cost_usd=float(total_cost))

    return ResponseEnvelope(data=cost_read, meta=meta)
