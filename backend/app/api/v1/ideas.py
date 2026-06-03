"""Idea intake endpoint (Pillar 1 entrypoint)."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_principal
from app.core.security import Principal
from app.schemas.idea import IdeaCreate
from app.schemas.run import RunRead
from app.services import run_service

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.post(
    "",
    response_model=RunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a startup idea and start a validation run",
)
async def submit_idea(
    idea: IdeaCreate,
    principal: Principal = Depends(get_principal),
) -> RunRead:
    """Create a new run for the submitted idea, scoped to the caller's organization."""
    return run_service.create_run(idea, organization_id=principal.organization_id)
