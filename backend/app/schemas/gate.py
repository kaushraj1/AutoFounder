"""Gate schemas for Human-in-the-loop approvals."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GateState(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    timed_out = "timed_out"


class GateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    kind: str
    state: GateState
    decided_by: str | None = None
    decided_at: datetime | None = None
    created_at: datetime


class GateDecision(BaseModel):
    decision: GateState
    notes: str | None = None
