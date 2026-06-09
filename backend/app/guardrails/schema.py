"""Guardrail pipeline data models (AF-046, CLAUDE.md §34).

The uniform contract every stage speaks: a ``GuardResult`` (pass / block / flag)
and an immutable ``LineageRecord`` written for every decision. ``GuardrailContext``
carries the per-call tenant identity and the optional service handles (audit
session, cost cache) the stages use — kept out of the Pydantic models because it
holds live, non-serialisable objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GuardrailStage(StrEnum):
    """The ordered stages every request passes through."""

    policy = "policy"
    input = "input"
    instruction = "instruction"
    execution = "execution"
    output = "output"
    monitoring = "monitoring"


# Canonical order: input stages before the LLM, execution around tools,
# output/monitoring after generation.
STAGE_ORDER: tuple[GuardrailStage, ...] = (
    GuardrailStage.policy,
    GuardrailStage.input,
    GuardrailStage.instruction,
    GuardrailStage.execution,
    GuardrailStage.output,
    GuardrailStage.monitoring,
)


class GuardSeverity(StrEnum):
    """Severity attached to a guard decision (drives alerting + audit weight)."""

    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


class GuardDecision(StrEnum):
    """The audited decision for a stage."""

    ALLOW = "allow"
    DENY = "deny"
    FLAG = "flag"


class GuardResult(BaseModel):
    """Uniform result returned by every stage and by the pipeline wrappers.

    Security stages fail *closed* (``blocked=True``); quality stages fail *open*
    with ``flags`` so a hard block never hurts UX more than the risk warrants.
    """

    stage: GuardrailStage
    blocked: bool = False
    reason: str | None = None
    severity: GuardSeverity = GuardSeverity.INFO
    sanitized_payload: dict[str, Any] | None = None
    flags: list[str] = Field(default_factory=list)

    @property
    def decision(self) -> GuardDecision:
        if self.blocked:
            return GuardDecision.DENY
        if self.flags:
            return GuardDecision.FLAG
        return GuardDecision.ALLOW

    @classmethod
    def ok(
        cls,
        stage: GuardrailStage,
        payload: dict[str, Any] | None = None,
    ) -> GuardResult:
        """A clean pass for ``stage``, optionally carrying a sanitised payload."""
        return cls(stage=stage, blocked=False, sanitized_payload=payload)

    @classmethod
    def block(
        cls,
        stage: GuardrailStage,
        reason: str,
        *,
        severity: GuardSeverity = GuardSeverity.CRITICAL,
        flags: list[str] | None = None,
    ) -> GuardResult:
        """A fail-closed block for a security stage."""
        return cls(
            stage=stage,
            blocked=True,
            reason=reason,
            severity=severity,
            flags=flags or [],
        )

    @classmethod
    def flag(
        cls,
        stage: GuardrailStage,
        flags: list[str],
        *,
        reason: str | None = None,
        severity: GuardSeverity = GuardSeverity.WARN,
        payload: dict[str, Any] | None = None,
    ) -> GuardResult:
        """A fail-open warning for a quality stage (not blocked)."""
        return cls(
            stage=stage,
            blocked=False,
            reason=reason,
            severity=severity,
            flags=flags,
            sanitized_payload=payload,
        )


class LineageRecord(BaseModel):
    """Immutable per-decision audit record (written to S3 Object Lock / audit_log)."""

    organization_id: str
    run_id: str | None = None
    agent_id: str | None = None
    stage: GuardrailStage
    decision: GuardDecision
    severity: GuardSeverity = GuardSeverity.INFO
    detail: dict[str, Any] = Field(default_factory=dict)
    ts: str  # ISO-8601 UTC; stamped by the caller (audit.emit_lineage)


@dataclass(slots=True)
class GuardrailContext:
    """Per-call identity + optional service handles handed to every stage.

    ``scopes`` / ``allowed_tools`` drive the Policy and Execution guards;
    ``session`` (AsyncSession) and ``cache`` (CacheClient) enable durable audit
    and per-tenant cost accumulation when available — both optional so stages
    stay unit-testable with no live infrastructure.
    """

    organization_id: str
    run_id: str | None = None
    agent_id: str | None = None
    role: str = "agent"
    scopes: list[str] = field(default_factory=list)
    allowed_tools: list[str] | None = None  # None => no allow-list restriction
    cost_cap_usd: float | None = None
    session: Any = None  # sqlalchemy AsyncSession — durable audit_log write
    cache: Any = None  # app.db.cache.CacheClient — per-tenant cost accumulator

    @classmethod
    def from_tenant(
        cls,
        organization_id: str,
        *,
        run_id: str | None = None,
        agent_id: str | None = None,
        role: str = "agent",
        scopes: list[str] | None = None,
        allowed_tools: list[str] | None = None,
        cost_cap_usd: float | None = None,
        session: Any = None,
        cache: Any = None,
    ) -> GuardrailContext:
        """Build a context for a tenant call (keyword-friendly factory)."""
        return cls(
            organization_id=organization_id,
            run_id=run_id,
            agent_id=agent_id,
            role=role,
            scopes=scopes or [],
            allowed_tools=allowed_tools,
            cost_cap_usd=cost_cap_usd,
            session=session,
            cache=cache,
        )
