"""Schemas for the DevOps agent's pre-flight HITL spend approval endpoint."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class DevOpsSpendDecision(StrEnum):
    """The two values the DevOps subgraph's polling loop will accept."""

    approved = "approved"
    rejected = "rejected"


class DevOpsSpendApprovalRequest(BaseModel):
    """Founder portal payload for `POST /v1/runs/{run_id}/devops-spend-approval`."""

    decision: DevOpsSpendDecision
    notes: str | None = Field(
        default=None,
        max_length=2_000,
        description="Optional human-readable rationale, persisted to the audit log only.",
    )


class DevOpsSpendApprovalResponse(BaseModel):
    """Confirmation payload returned to the caller."""

    run_id: UUID
    decision: DevOpsSpendDecision
    redis_key: str
