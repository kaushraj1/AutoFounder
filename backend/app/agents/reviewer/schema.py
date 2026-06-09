"""Pydantic schemas + graph state for AF-042 Reviewer / Self-Healer Agent (Pillar 4).

Single source of truth for every type threaded through the Reviewer LangGraph.
Parallel test/scan nodes write distinct keys; shared accumulators
(``node_traces``, ``error_count``, ``total_tool_calls``) use ``operator.add``
reducers so concurrent branch writes merge instead of clobbering.
"""

from __future__ import annotations

import operator
import time
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Constants (Appendix A decision log: D2 / D4 / D5 / D6)
# ---------------------------------------------------------------------------

MAX_HEAL_CYCLES = 5
"""D2 — bounded self-heal loop; after 5 cycles the failure is structural → escalate."""

COVERAGE_THRESHOLD = 80.0
"""D6 — unit-test coverage gate (%). Below this after heal cycles → escalate."""

MIN_READABILITY = 70
MIN_MAINTAINABILITY = 70
MIN_SECURITY_POSTURE = 60
"""LLM-judge gate floors (Workflow Design step 6)."""

SANDBOX_SPINUP_SLA_SECONDS = 10.0
SANDBOX_HARD_KILL_SECONDS = 30.0


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NodeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GateStatus(StrEnum):
    """Outcome of a single quality gate (lint / unit / e2e / scan / sonar)."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    HEAL = "heal"
    ESCALATE = "escalate"


class SeverityLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OWASPCategory(StrEnum):
    """OWASP Top 10 (2021) categories used to tag security findings."""

    A01_BROKEN_ACCESS_CONTROL = "A01:2021-Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021-Cryptographic Failures"
    A03_INJECTION = "A03:2021-Injection"
    A04_INSECURE_DESIGN = "A04:2021-Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021-Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021-Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021-Identification and Authentication Failures"
    A08_INTEGRITY_FAILURES = "A08:2021-Software and Data Integrity Failures"
    A09_LOGGING_FAILURES = "A09:2021-Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021-Server-Side Request Forgery"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class CodeArtifact(BaseModel):
    """A file (or stack manifest entry) discovered while ingesting the repo."""

    path: str
    language: str  # "python" | "typescript" | "javascript" | "dockerfile" | "other"
    lines: int = 0


class LintResult(BaseModel):
    """One linter / formatter outcome (ESLint, Prettier, Ruff, Black)."""

    tool: str
    status: GateStatus = GateStatus.PASSED
    error_count: int = 0
    warning_count: int = 0
    fixable_count: int = 0
    messages: list[str] = Field(default_factory=list)


class TestFailure(BaseModel):
    """A single failing test, used by triage + auto-heal."""

    __test__ = False  # not a pytest test class (name starts with "Test")

    test_id: str
    file_path: str | None = None
    message: str = ""


class TestSuiteResult(BaseModel):
    """Aggregated result of a test runner (Jest / pytest / Playwright)."""

    __test__ = False  # not a pytest test class (name starts with "Test")

    runner: str
    status: GateStatus = GateStatus.PASSED
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    coverage_pct: float | None = Field(default=None, ge=0, le=100)
    failures: list[TestFailure] = Field(default_factory=list)

    @field_validator("coverage_pct")
    @classmethod
    def _coverage_in_range(cls, v: float | None) -> float | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("coverage_pct must be between 0 and 100")
        return v


class SecurityFinding(BaseModel):
    """A normalised finding from any scanner (Trivy/Semgrep/Bandit/Snyk/Gitleaks)."""

    tool: str
    severity: SeverityLevel
    rule_id: str
    file_path: str
    line: int | None = None
    message: str
    owasp_category: OWASPCategory | None = None
    cwe: str | None = None
    auto_fixable: bool = False
    suppressed: bool = False


class SonarMetrics(BaseModel):
    """SonarQube quality-gate snapshot."""

    quality_gate_passed: bool = False
    bugs: int = 0
    vulnerabilities: int = 0
    code_smells: int = 0
    coverage_pct: float | None = None
    duplicated_lines_pct: float | None = None


class LLMJudgeScore(BaseModel):
    """LLM-as-judge scores (0-100) + derived approval flag."""

    readability: int = Field(..., ge=0, le=100)
    maintainability: int = Field(..., ge=0, le=100)
    security_posture: int = Field(..., ge=0, le=100)
    overall: int = Field(..., ge=0, le=100)
    approved: bool = False
    rationale: str = ""


class HealCycle(BaseModel):
    """One iteration of the self-heal loop (audit trail)."""

    cycle: int
    issues_targeted: list[str] = Field(default_factory=list)
    patches_applied: list[str] = Field(default_factory=list)
    files_patched: list[str] = Field(default_factory=list)
    outcome: str = "pending"  # "pending" | "improved" | "no_change" | "failed"
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NodeTrace(BaseModel):
    """Per-node execution record (status + timing + retries)."""

    node: str
    status: NodeStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    retry_count: int = 0
    sla_breached: bool = False


class RetryPolicy(BaseModel):
    max_retries: int = 2
    backoff_seconds: list[int] = Field(default_factory=lambda: [2, 5, 15])


# ---------------------------------------------------------------------------
# Agent input
# ---------------------------------------------------------------------------


class ReviewerInput(BaseModel):
    """Contract handed in by the Orchestrator (sourced from the Coder Agent, AF-041)."""

    run_id: UUID = Field(default_factory=uuid4)
    organization_id: str
    coder_run_id: UUID | None = None
    repo_url: str
    pr_number: int = 0
    branch: str = "main"
    local_path: str | None = Field(
        default=None,
        description="Optional already-cloned path (used by tests / Coder handoff).",
    )
    feature_list: list[str] = Field(
        default_factory=list,
        description="Optional Pillar-2 feature list for the judge's implements-features check.",
    )


# ---------------------------------------------------------------------------
# Root graph state
# ---------------------------------------------------------------------------


class ReviewerState(BaseModel):
    """Single source of truth threaded through every Reviewer node.

    Parallel branches write distinct keys (``lint_results``, ``unit_test_result``,
    ...). Shared accumulators use ``operator.add`` reducers so concurrent writes
    merge. All other fields are last-write-wins.
    """

    # Identity
    run_id: UUID = Field(default_factory=uuid4)
    organization_id: str
    coder_run_id: UUID | None = None
    repo_url: str
    pr_number: int = 0
    branch: str = "main"
    local_path: str | None = None
    feature_list: list[str] = Field(default_factory=list)

    # Ingest
    code_artifacts: list[CodeArtifact] = Field(default_factory=list)
    has_python: bool = False
    has_typescript: bool = False
    workdir: str | None = None

    # Sandbox
    sandbox_container_id: str | None = None
    sandbox_image_tag: str | None = None
    sandbox_spinup_seconds: float | None = None

    # Gate results (populated by the 5 parallel nodes)
    lint_results: list[LintResult] = Field(default_factory=list)
    unit_test_result: TestSuiteResult | None = None
    e2e_test_result: TestSuiteResult | None = None
    security_findings: list[SecurityFinding] = Field(default_factory=list)
    sonarqube_metrics: SonarMetrics | None = None

    # Judge + triage
    llm_judge_score: LLMJudgeScore | None = None
    current_failures: list[str] = Field(default_factory=list)
    owasp_violations: list[str] = Field(default_factory=list)
    review_decision: ReviewDecision | None = None
    escalation_reason: str | None = None

    # Self-heal loop
    heal_cycle: int = 0
    heal_history: list[HealCycle] = Field(default_factory=list)

    # Report / output
    review_report_markdown: str | None = None
    review_report_uri: str | None = None
    github_pr_comment_url: str | None = None
    is_approved: bool = False

    # Execution metadata
    node_traces: Annotated[list[NodeTrace], operator.add] = Field(default_factory=list)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    total_llm_tokens_used: int = 0
    total_tool_calls: Annotated[int, operator.add] = 0
    error_count: Annotated[int, operator.add] = 0
    started_at_unix_ms: int = Field(default_factory=lambda: int(time.time() * 1000))

    # Terminal flags
    is_complete: bool = False
    fatal_error: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ---------------------------------------------------------------------------
# Flat output adapter → DevOps Agent (Pillar 5) / RunState / gRPC
# ---------------------------------------------------------------------------


class ReviewerOutput(BaseModel):
    """Stable, flat handoff consumed by DevOps (P5) + Code Review Studio (AF-057).

    Mirrors the ``ReviewerOutput`` protobuf (proto/reviewer_output.proto).
    """

    run_id: str
    organization_id: str
    coder_run_id: str | None = None
    repo_url: str
    branch: str
    pr_number: int
    review_decision: str
    is_approved: bool
    unit_test_coverage: float = 0.0
    security_finding_count: int = 0
    critical_finding_count: int = 0
    llm_judge_overall: int = 0
    heal_cycles_used: int = 0
    review_report_url: str | None = None
    github_pr_comment_url: str | None = None
    escalation_reason: str | None = None
    owasp_violations: list[str] = Field(default_factory=list)
    completed_at_unix_ms: int = 0
    total_llm_tokens_used: int = 0

    @classmethod
    def from_state(cls, s: ReviewerState, *, completed_at_unix_ms: int) -> ReviewerOutput:
        coverage = 0.0
        if s.unit_test_result and s.unit_test_result.coverage_pct is not None:
            coverage = s.unit_test_result.coverage_pct

        critical = sum(
            1
            for f in s.security_findings
            if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH) and not f.suppressed
        )

        return cls(
            run_id=str(s.run_id),
            organization_id=s.organization_id,
            coder_run_id=str(s.coder_run_id) if s.coder_run_id else None,
            repo_url=s.repo_url,
            branch=s.branch,
            pr_number=s.pr_number,
            review_decision=str(s.review_decision or ReviewDecision.ESCALATE),
            is_approved=s.is_approved,
            unit_test_coverage=coverage,
            security_finding_count=len([f for f in s.security_findings if not f.suppressed]),
            critical_finding_count=critical,
            llm_judge_overall=s.llm_judge_score.overall if s.llm_judge_score else 0,
            heal_cycles_used=s.heal_cycle,
            review_report_url=s.review_report_uri,
            github_pr_comment_url=s.github_pr_comment_url,
            escalation_reason=s.escalation_reason,
            owasp_violations=list(s.owasp_violations),
            completed_at_unix_ms=completed_at_unix_ms,
            total_llm_tokens_used=s.total_llm_tokens_used,
        )
