"""Feedback collection endpoint for LLMOps RLHF."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import get_meta, get_udal
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.udal import UDAL
from app.models.run import Run
from app.schemas.common import Meta, ResponseEnvelope
from app.schemas.feedback import FeedbackCreate

logger = get_logger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=ResponseEnvelope[bool], summary="Submit user feedback")
async def intake_feedback(
    feedback: FeedbackCreate,
    udal: Annotated[UDAL, Depends(get_udal)],
    meta: Annotated[Meta, Depends(get_meta)],
) -> ResponseEnvelope[bool]:
    """Collect user feedback rating and comments for optimization metrics."""
    async with udal.relational() as db:
        # Check if the run exists first
        run_result = await db.session.execute(select(Run).where(Run.id == feedback.run_id))
        run = run_result.scalar_one_or_none()
        if not run:
            raise NotFoundError("Run not found")

        # Emit audit trail
        metadata = {
            "rating": feedback.rating,
            "comment": feedback.comment,
            "step_id": feedback.step_id,
        }
        await db.audit(
            "create",
            "feedback",
            str(feedback.run_id),
            run_id=str(feedback.run_id),
            metadata=metadata,
        )
        logger.info(
            "feedback.received",
            run_id=str(feedback.run_id),
            rating=feedback.rating,
            comment=feedback.comment,
        )

    return ResponseEnvelope(data=True, meta=meta)
