"""Artifact query endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import get_meta, get_udal
from app.core.errors import NotFoundError
from app.db.udal import UDAL
from app.models.artifact import Artifact
from app.models.run import Run
from app.schemas.artifact import ArtifactRead
from app.schemas.common import Meta, ResponseEnvelope

router = APIRouter(prefix="/runs/{run_id}/artifacts", tags=["artifacts"])


@router.get(
    "",
    response_model=ResponseEnvelope[list[ArtifactRead]],
    summary="List generated artifacts",
)
async def list_artifacts(
    run_id: uuid.UUID,
    udal: Annotated[UDAL, Depends(get_udal)],
    meta: Annotated[Meta, Depends(get_meta)],
) -> ResponseEnvelope[list[ArtifactRead]]:
    """List all generated deliverables/artifacts for a specific run."""
    async with udal.relational() as db:
        # Check if the run exists first
        run_result = await db.session.execute(select(Run).where(Run.id == run_id))
        run = run_result.scalar_one_or_none()
        if not run:
            raise NotFoundError("Run not found")

        result = await db.session.execute(
            select(Artifact).where(Artifact.run_id == run_id)
        )
        artifacts = result.scalars().all()
        await db.audit("read", "artifacts", run_id=str(run_id))

        artifact_reads = [ArtifactRead.model_validate(a) for a in artifacts]

    return ResponseEnvelope(data=artifact_reads, meta=meta)
