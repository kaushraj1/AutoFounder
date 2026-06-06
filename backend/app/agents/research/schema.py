"""Pydantic schemas for AF-038 Research Agent (Pillar 1)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchInput(BaseModel):
    run_id: str
    organization_id: str
    idea_normalised: str
    domain: str
    queries: list[str] = Field(default_factory=list)
    sources: list[str] = Field(
        default_factory=lambda: ["tavily", "serpapi", "crunchbase", "g2", "similarweb"]
    )


class Citation(BaseModel):
    source: str
    url: str | None = None
    title: str | None = None
    snippet: str


class SourceResult(BaseModel):
    source: str
    ok: bool
    items: list[Citation] = Field(default_factory=list)
    error: str | None = None


class ResearchFinding(BaseModel):
    claim: str
    citations: list[int] = Field(default_factory=list)


class ResearchOutput(BaseModel):
    run_id: str
    organization_id: str
    domain: str
    findings: list[ResearchFinding]
    sources: list[Citation]
    groundedness_score: float = Field(..., ge=0.0, le=1.0)
    confidence: str  # high | medium | low
    partial_sources: list[str] = Field(default_factory=list)
    total_llm_tokens_used: int = 0
