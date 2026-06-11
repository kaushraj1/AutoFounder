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
        from sqlalchemy import text
        
        # Resolve or create a default workspace for the organization
        res = await db.session.execute(text("SELECT id FROM workspaces LIMIT 1;"))
        row = res.fetchone()
        if row:
            workspace_id = row[0]
        else:
            workspace_id = uuid.uuid4()
            await db.session.execute(
                text("INSERT INTO workspaces (id, organization_id, name, created_by) VALUES (:id, :org, 'Default Workspace', 'system');"),
                {"id": workspace_id, "org": uuid.UUID(udal.organization_id)}
            )
            
        new_run = Run(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            organization_id=uuid.UUID(udal.organization_id),
            pillar="strategy",
            status=RunStatus.queued,
            plan={},
            created_at=datetime.now(UTC),
            idea_text=idea.text,
            idea_meta={},
            created_by="founder",
        )
        db.session.add(new_run)
        await db.session.commit()
        await db.audit("create", "runs", str(new_run.id))
        run_read = RunRead.model_validate(new_run)

    return ResponseEnvelope(data=run_read, meta=meta)
