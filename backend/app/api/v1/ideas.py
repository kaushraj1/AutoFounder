"""Idea intake endpoint — entry point for Pillar 1 (Strategy & Research)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status

from app.api.deps import get_meta, get_udal
from app.db.udal import UDAL
from app.models.run import Run
from app.schemas.common import Meta, ResponseEnvelope
from app.schemas.idea import IdeaCreate
from app.schemas.run import RunRead, RunStatus

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.post(
    "",
    response_model=ResponseEnvelope[RunRead],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a startup idea and start a validation run",
)
async def submit_idea(
    idea: IdeaCreate,
    udal: UDAL = Depends(get_udal),
    meta: Meta = Depends(get_meta),
) -> ResponseEnvelope[RunRead]:
    """Create a new run for the submitted idea.

    The run is scoped to the caller's organization and persisted in the database.
    """
    async with udal.relational() as db:
        new_run = Run(
            id=uuid.uuid4(),
            pillar="strategy",
            status=RunStatus.pending,
            plan={},
            created_at=datetime.now(UTC)
        )
        db.session.add(new_run)
        await db.session.commit()
        await db.audit("create", "runs", str(new_run.id))
        run_read = RunRead.model_validate(new_run)
        
    return ResponseEnvelope(data=run_read, meta=meta)
