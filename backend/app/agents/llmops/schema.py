"""AF-045 LLMOps Agent — data schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentTrace(BaseModel):
    """A single agent execution trace from any pillar."""

    agent_id: str
    run_id: str
    organization_id: str
    tokens_used: int
    elapsed_seconds: float
    verify_passed: bool
    error_count: int = 0
    coverage_score: float | None = None
    timestamp: str  # ISO format


class PromptOptimization(BaseModel):
    agent_id: str
    template_name: str
    current_score: float
    optimized_prompt_snippet: str
    improvement_delta: float
    recommendation: str  # "promote" | "test" | "discard"


class ModelRoutingUpdate(BaseModel):
    task_class: str
    current_model: str
    recommended_model: str
    reason: str
    expected_cost_delta_usd: float


class DriftAlert(BaseModel):
    agent_id: str
    metric: str  # "coverage_score" | "verify_pass_rate" | "avg_tokens"
    baseline: float
    current: float
    drift_pct: float
    severity: str  # "warning" | "critical"


class FinOpsReport(BaseModel):
    period: str  # "weekly"
    total_tokens: int
    total_cost_usd: float
    cost_by_agent: dict[str, float]
    cost_by_org: dict[str, float]
    top_expensive_runs: list[dict[str, Any]]
    optimization_savings_usd: float


class LLMOpsInput(BaseModel):
    run_id: str
    organization_id: str
    analysis_period_days: int = 7
    traces: list[AgentTrace] = Field(default_factory=list)


class LLMOpsOutput(BaseModel):
    run_id: str
    organization_id: str
    prompt_optimizations: list[PromptOptimization]
    routing_updates: list[ModelRoutingUpdate]
    drift_alerts: list[DriftAlert]
    finops_report: FinOpsReport
    summary_markdown: str
    total_llm_tokens_used: int = 0
