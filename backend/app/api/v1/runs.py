"""Run query endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_principal
from app.core.security import Principal
from app.schemas.run import RunRead
from app.services import run_service

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunRead], summary="List runs")
async def list_runs(principal: Principal = Depends(get_principal)) -> list[RunRead]:
    """List runs for the caller's organization."""
    return run_service.list_runs(organization_id=principal.organization_id)


@router.get("/{run_id}", response_model=RunRead, summary="Get a run by id")
async def get_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
) -> RunRead:
    """Fetch a single run, or 404 if it does not exist for this organization."""
    try:
        return run_service.get_run(run_id, organization_id=principal.organization_id)
    except run_service.RunNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from None
