"""Pillar 2 — Architect Agent data models (AF-040).

FeatureList is the canonical ground truth consumed by:
  - Kartik / Pillar 3 (Coder Agent): ERD + OpenAPI + features to build
  - Pallavi / Pillar 6 (Marketing Agent): hallucination cross-reference guard
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FeatureList(BaseModel):
    """Critical output — FATAL for Pillar 6 if empty."""

    features: list[str]
    integrations: list[str] = Field(default_factory=list)
    pricing_tiers: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("features")
    @classmethod
    def features_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError(
                "FeatureList.features cannot be empty — FATAL: Pillar 6 refuses to run without it"
            )
        return v


class Requirement(BaseModel):
    """A single functional or non-functional requirement extracted from the PRD."""

    id: str
    kind: str  # "FR" | "NFR"
    description: str
    priority: str  # "P0" | "P1" | "P2"


class ArchitectOutput(BaseModel):
    """Full output of the Architect Agent handed to Pillar 3 and stored in UDAL."""

    run_id: UUID
    organization_id: str
    requirements: list[Requirement]
    erd_mermaid: str
    openapi_3_1: dict[str, Any]
    stack: dict[str, str]  # {frontend, backend, db, infra}
    microservice_boundaries: list[str]
    auth_strategy: dict[str, Any]
    scaling_plan: dict[str, Any]
    cost_estimate: dict[str, Any]  # {monthly_usd: float, breakdown: dict}
    feature_list: FeatureList
    approval_status: str = "pending"  # "pending" | "approved" | "rejected"
