"""Unit tests for guardrail data models (GuardResult / LineageRecord)."""

from __future__ import annotations

from app.guardrails.schema import (
    GuardDecision,
    GuardrailStage,
    GuardResult,
    GuardSeverity,
    LineageRecord,
)


def test_ok_result() -> None:
    r = GuardResult.ok(GuardrailStage.input, {"prompt": "hi"})
    assert not r.blocked
    assert r.decision is GuardDecision.ALLOW
    assert r.sanitized_payload == {"prompt": "hi"}


def test_block_result_is_critical_deny() -> None:
    r = GuardResult.block(GuardrailStage.policy, "denied")
    assert r.blocked
    assert r.severity is GuardSeverity.CRITICAL
    assert r.decision is GuardDecision.DENY
    assert r.reason == "denied"


def test_flag_result_is_open_flag() -> None:
    r = GuardResult.flag(GuardrailStage.output, ["toxicity:1"], reason="bad word")
    assert not r.blocked
    assert r.decision is GuardDecision.FLAG
    assert r.flags == ["toxicity:1"]
    assert r.severity is GuardSeverity.WARN


def test_lineage_record_roundtrip() -> None:
    rec = LineageRecord(
        organization_id="org-1",
        run_id="run-1",
        agent_id="agent.x",
        stage=GuardrailStage.input,
        decision=GuardDecision.FLAG,
        detail={"flags": ["pii:email=1"]},
        ts="2026-06-09T00:00:00+00:00",
    )
    dumped = rec.model_dump()
    assert dumped["stage"] == "input"
    assert dumped["decision"] == "flag"
    assert dumped["detail"]["flags"] == ["pii:email=1"]
