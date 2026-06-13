"""Run schemas — the unit of work created when a founder submits an idea."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RunStatus(StrEnum):
    """Lifecycle states for a run."""

    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class RunRead(BaseModel):
    """A run as returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pillar: str
    status: RunStatus
    created_at: datetime
