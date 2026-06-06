"""Pydantic schemas for AF-039 Product Planner Agent (Pillar 1.5)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.strategy.schema import BuyerPersona, Competitor, LeanCanvas, StrategyOutput


class ProductPlannerInput(BaseModel):
    run_id: str
    organization_id: str
    strategy: StrategyOutput


class Requirement(BaseModel):
    id: str                         # "FR-001" | "NFR-001"
    kind: str                       # "functional" | "non_functional"
    statement: str
    priority: str                   # MoSCoW: "must" | "should" | "could" | "wont"
    rationale: str | None = None
    traces_to: str                  # canvas item or persona name this derives from


class UserStory(BaseModel):
    id: str                         # "US-001"
    persona: str                    # name of a BuyerPersona from strategy.icps
    role: str
    want: str
    benefit: str
    acceptance_criteria: list[str] = Field(..., min_length=1)
    priority: str                   # MoSCoW
    epic: str | None = None


class Milestone(BaseModel):
    phase: str                      # "MVP" | "v1" | "v2"
    title: str
    objective: str
    epics: list[str] = Field(default_factory=list)
    user_story_ids: list[str] = Field(default_factory=list)
    target_weeks: int | None = None


class PRD(BaseModel):
    title: str
    overview: str
    problem_statement: str
    goals: list[str] = Field(..., min_length=1)
    non_goals: list[str] = Field(default_factory=list)
    target_users: list[str] = Field(..., min_length=1)  # persona names
    success_metrics: list[str] = Field(default_factory=list)
    scope_in: list[str] = Field(default_factory=list)
    scope_out: list[str] = Field(default_factory=list)


class ProductPlannerOutput(BaseModel):
    run_id: str
    organization_id: str
    domain: str
    prd: PRD
    requirements: list[Requirement]
    user_stories: list[UserStory]
    roadmap: list[Milestone]
    prd_markdown: str
    prd_s3_uri: str | None = None
    coverage_score: float = Field(..., ge=0.0, le=1.0)
    confidence: str                 # high | medium | low
    total_llm_tokens_used: int = 0


__all__ = [
    "ProductPlannerInput",
    "PRD",
    "Requirement",
    "UserStory",
    "Milestone",
    "ProductPlannerOutput",
    # re-exported for consumers
    "BuyerPersona",
    "Competitor",
    "LeanCanvas",
    "StrategyOutput",
]
