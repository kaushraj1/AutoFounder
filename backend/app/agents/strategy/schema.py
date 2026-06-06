from __future__ import annotations

import operator
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NodeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ViabilityBand(StrEnum):
    STRONG = "strong"  # 75–100
    MODERATE = "moderate"  # 50–74
    WEAK = "weak"  # 25–49
    REJECT = "reject"  # 0–24


class BiasFlag(StrEnum):
    WESTERN_CENTRIC = "western_centric"
    RECENCY_BIAS = "recency_bias"
    SURVIVORSHIP_BIAS = "survivorship_bias"
    CONFIRMATION_BIAS = "confirmation_bias"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class MarketSize(BaseModel):
    tam_usd_bn: float = Field(..., description="Total Addressable Market, USD billions")
    sam_usd_bn: float = Field(..., description="Serviceable Addressable Market, USD billions")
    som_usd_bn: float = Field(..., description="Serviceable Obtainable Market, USD billions")
    cagr_pct: float = Field(..., description="Projected CAGR %")
    sources: list[str] = Field(default_factory=list)

    @field_validator("tam_usd_bn", "sam_usd_bn", "som_usd_bn", "cagr_pct")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Market size values must be non-negative")
        return v

    @model_validator(mode="after")
    def market_hierarchy(self) -> MarketSize:
        if not (self.tam_usd_bn >= self.sam_usd_bn >= self.som_usd_bn):
            raise ValueError("TAM >= SAM >= SOM constraint violated")
        return self


class Competitor(BaseModel):
    name: str
    url: str
    funding_usd_mn: float | None = None
    employee_range: str | None = None
    key_features: list[str] = Field(default_factory=list)
    pricing_model: str | None = None
    g2_rating: float | None = Field(None, ge=0, le=5)
    weakness: str | None = None


class Keyword(BaseModel):
    term: str
    monthly_search_volume: int | None = None
    keyword_difficulty: int | None = Field(None, ge=0, le=100)
    cpc_usd: float | None = None
    intent: str | None = None  # "informational" | "commercial" | "transactional"


class BuyerPersona(BaseModel):
    name: str
    role: str
    company_size: str
    pain_points: list[str]
    goals: list[str]
    willingness_to_pay_inr: int | None = None
    preferred_channels: list[str] = Field(default_factory=list)


class TrendSignal(BaseModel):
    source: str  # "google_trends" | "reddit" | "hackernews" | "serpapi"
    signal: str
    sentiment: str  # "positive" | "neutral" | "negative"
    evidence_url: str | None = None


class LeanCanvas(BaseModel):
    problem: list[str] = Field(..., min_length=1, max_length=3)
    customer_segments: list[str] = Field(..., min_length=1, max_length=3)
    unique_value_proposition: str
    solution: list[str] = Field(..., min_length=1, max_length=3)
    channels: list[str] = Field(default_factory=list)
    revenue_streams: list[str] = Field(default_factory=list)
    cost_structure: list[str] = Field(default_factory=list)
    key_metrics: list[str] = Field(default_factory=list)
    unfair_advantage: str
    early_adopters: str


class ViabilityScore(BaseModel):
    total: int = Field(..., ge=0, le=100)
    band: ViabilityBand = ViabilityBand.REJECT
    breakdown: dict[str, int] = Field(
        description="Component scores: market_size, competition, trend, monetisation, feasibility"
    )
    pivot_suggestions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def derive_band(self) -> ViabilityScore:
        if self.total >= 75:
            object.__setattr__(self, "band", ViabilityBand.STRONG)
        elif self.total >= 50:
            object.__setattr__(self, "band", ViabilityBand.MODERATE)
        elif self.total >= 25:
            object.__setattr__(self, "band", ViabilityBand.WEAK)
        else:
            object.__setattr__(self, "band", ViabilityBand.REJECT)
        return self


class NodeTrace(BaseModel):
    node: str
    status: NodeStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    retry_count: int = 0


class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_seconds: list[int] = Field(default_factory=lambda: [5, 15, 45])


# ---------------------------------------------------------------------------
# Root Graph State
# ---------------------------------------------------------------------------


class StrategistState(BaseModel):
    """
    Single source of truth threaded through every node in the Strategist graph.
    LangGraph merges updates via add_messages for the messages channel;
    all other fields are last-write-wins.
    """

    # Identity
    run_id: UUID = Field(default_factory=uuid4)
    organization_id: str = Field(..., description="Validated from Supabase JWT claims")
    idea_raw: str = Field(..., min_length=10, max_length=4000)

    # Normalised inputs
    idea_normalised: str | None = None
    domain: str | None = None  # e.g. "B2B SaaS", "Consumer App"
    geography_focus: str = "global"

    # Research outputs (populated by parallel nodes)
    market_size: MarketSize | None = None
    competitors: list[Competitor] = Field(default_factory=list)
    keywords: list[Keyword] = Field(default_factory=list)
    personas: list[BuyerPersona] = Field(default_factory=list)
    trend_signals: list[TrendSignal] = Field(default_factory=list)
    overall_momentum: str | None = None

    # Bias audit and corrections
    bias_flags: list[BiasFlag] = Field(default_factory=list)
    bias_corrections: list[str] = Field(default_factory=list)
    lean_canvas: LeanCanvas | None = None
    viability_score: ViabilityScore | None = None
    report_markdown: str | None = None

    # Execution metadata
    node_traces: Annotated[list[NodeTrace], operator.add] = Field(default_factory=list)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    total_llm_tokens_used: int = 0
    total_tool_calls: Annotated[int, operator.add] = 0
    error_count: Annotated[int, operator.add] = 0

    # LangGraph message channel (tool call / observation pairs)
    messages: Annotated[list[Any], add_messages] = Field(default_factory=list)

    # Terminal flag — set by router to exit the graph
    is_complete: bool = False
    fatal_error: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ---------------------------------------------------------------------------
# Flat output adapter for RunState / downstream stability
# ---------------------------------------------------------------------------


class StrategyOutput(BaseModel):
    run_id: str
    organization_id: str
    idea_normalised: str
    domain: str
    tam_sam_som: dict[str, float]
    competitors: list[Competitor]
    icps: list[BuyerPersona]
    lean_canvas: LeanCanvas
    viability_score: int  # 0-100
    viability_band: str
    bias_flags: list[str]
    pivots: list[str]
    sources: list[str]
    report_markdown: str
    total_llm_tokens_used: int

    @classmethod
    def from_state(cls, s: StrategistState) -> StrategyOutput:
        tam_sam_som = {}
        if s.market_size:
            tam_sam_som = {
                "tam_usd_bn": s.market_size.tam_usd_bn,
                "sam_usd_bn": s.market_size.sam_usd_bn,
                "som_usd_bn": s.market_size.som_usd_bn,
            }

        sources = []
        if s.market_size and s.market_size.sources:
            sources.extend(s.market_size.sources)
        sources = list(dict.fromkeys(sources))

        # A successful run (post-verify) always has a canvas. Refuse to fabricate
        # one — a missing canvas means the run failed and must not be presented as
        # a valid validation package to downstream consumers.
        if s.lean_canvas is None:
            raise ValueError(
                "Cannot build StrategyOutput: lean_canvas is missing "
                "(run did not complete successfully)"
            )
        canvas = s.lean_canvas

        return cls(
            run_id=str(s.run_id),
            organization_id=s.organization_id,
            idea_normalised=s.idea_normalised or "",
            domain=s.domain or "",
            tam_sam_som=tam_sam_som,
            competitors=s.competitors,
            icps=s.personas,
            lean_canvas=canvas,
            viability_score=s.viability_score.total if s.viability_score else 0,
            viability_band=str(s.viability_score.band) if s.viability_score else "reject",
            bias_flags=[str(flag) for flag in s.bias_flags],
            pivots=s.viability_score.pivot_suggestions if s.viability_score else [],
            sources=sources,
            report_markdown=s.report_markdown or "",
            total_llm_tokens_used=s.total_llm_tokens_used,
        )
