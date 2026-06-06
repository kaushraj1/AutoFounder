"""Gate schemas for Human-in-the-loop approvals."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


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
    payload: dict = {}
    decided_by: str | None = None
    decided_at: datetime | None = None
    timeout_at: datetime | None = None
    created_at: datetime

    @field_validator("payload", mode="before")
    @classmethod
    def default_payload(cls, v: Any) -> Any:
        if v is None:
            return {}
        return v


class GateDecision(BaseModel):
    decision: GateState
    notes: str | None = None
