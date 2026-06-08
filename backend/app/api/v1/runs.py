"""Run query endpoints."""

import base64
import json
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, select

from app.api.deps import get_meta, get_udal
from app.core.errors import NotFoundError
from app.db.udal import UDAL
from app.models.run import Run
from app.schemas.common import Meta, PaginatedResponseEnvelope, PaginationInfo, ResponseEnvelope
from app.schemas.run import RunRead

router = APIRouter(prefix="/runs", tags=["runs"])


def encode_cursor(run_id: str, created_at: str) -> str:
    """Encode (run_id, created_at) into an opaque URL-safe cursor string."""
    payload = json.dumps({"id": run_id, "ca": created_at})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """Decode a cursor string back to its {id, ca} dict; raises ValueError on corruption."""
    try:
        return json.loads(base64.urlsafe_b64decode(cursor).decode())
    except Exception as e:
        raise ValueError("Invalid cursor format") from e


@router.get("", response_model=PaginatedResponseEnvelope[RunRead], summary="List runs")
async def list_runs(
    udal: Annotated[UDAL, Depends(get_udal)],
    meta: Annotated[Meta, Depends(get_meta)],
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = None,
    order: str = Query("desc", regex="^(asc|desc)$"),
) -> PaginatedResponseEnvelope[RunRead]:
    """List runs for the caller's organization with cursor-based pagination."""
    async with udal.relational() as db:
        # Get total count
        total_result = await db.session.execute(select(func.count()).select_from(Run))
        total_count = total_result.scalar_one()

        query = select(Run)

        if cursor:
            try:
                cursor_data = decode_cursor(cursor)
                last_id = uuid.UUID(cursor_data["id"])
                last_ca_dt = datetime.fromisoformat(cursor_data["ca"])

                # Compound condition handles tie-breaking: if two runs share
                # the same created_at, sort stability is guaranteed by id.
                if order == "desc":
                    query = query.where(
                        (Run.created_at < last_ca_dt)
                        | ((Run.created_at == last_ca_dt) & (Run.id < last_id))
                    )
                else:
                    query = query.where(
                        (Run.created_at > last_ca_dt)
                        | ((Run.created_at == last_ca_dt) & (Run.id > last_id))
                    )
            except Exception:
                # If cursor is invalid, we fallback to ignoring it
                pass

        if order == "desc":
            query = query.order_by(desc(Run.created_at), desc(Run.id))
        else:
            query = query.order_by(asc(Run.created_at), asc(Run.id))

        # Fetch limit+1 to detect has_more without a second COUNT query.
        query = query.limit(limit + 1)
        result = await db.session.execute(query)
        runs = result.scalars().all()
        await db.audit("read", "runs")

        has_more = len(runs) > limit
        data_runs = runs[:limit]

        next_cursor = None
        if has_more and data_runs:
            last_run = data_runs[-1]
            next_cursor = encode_cursor(str(last_run.id), last_run.created_at.isoformat())

        run_reads = [RunRead.model_validate(r) for r in data_runs]

    pagination = PaginationInfo(cursor=next_cursor, has_more=has_more, total=total_count)

    return PaginatedResponseEnvelope(data=run_reads, pagination=pagination, meta=meta)


@router.get("/{run_id}", response_model=ResponseEnvelope[RunRead], summary="Get a run by id")
async def get_run(
    run_id: uuid.UUID,
    udal: Annotated[UDAL, Depends(get_udal)],
    meta: Annotated[Meta, Depends(get_meta)],
) -> ResponseEnvelope[RunRead]:
    """Fetch a single run, or 404 if it does not exist for this organization."""
    async with udal.relational() as db:
        result = await db.session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise NotFoundError("Run not found")
        await db.audit("read", "runs", str(run_id))
        run_read = RunRead.model_validate(run)

    return ResponseEnvelope(data=run_read, meta=meta)


@router.delete("/{run_id}", response_model=ResponseEnvelope[bool], summary="Cancel a run")
async def cancel_run(
    run_id: uuid.UUID,
    udal: Annotated[UDAL, Depends(get_udal)],
    meta: Annotated[Meta, Depends(get_meta)],
) -> ResponseEnvelope[bool]:
    """Cancel and delete a run by ID."""
    async with udal.relational() as db:
        result = await db.session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise NotFoundError("Run not found")
        await db.session.delete(run)
        await db.session.commit()
        await db.audit("delete", "runs", str(run_id))

    return ResponseEnvelope(data=True, meta=meta)
