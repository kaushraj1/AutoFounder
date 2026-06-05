"""Feedback schemas for LLMOps RLHF."""

from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    run_id: UUID
    step_id: str | None = None
    rating: int = Field(..., ge=1, le=5, description="RLHF score from 1 to 5")
    comment: str | None = None
