"""Unit tests for guardrail audit & lineage emit."""

from __future__ import annotations

from typing import Any

import pytest

from app.guardrails import audit
from app.guardrails.schema import GuardrailContext, GuardrailStage, GuardResult


def test_build_record_maps_decision_and_detail() -> None:
    ctx = GuardrailContext(organization_id="org-1", run_id="r1", agent_id="a1")
    result = GuardResult.block(GuardrailStage.policy, "denied")
    rec = audit.build_record(ctx, result)
    assert rec.organization_id == "org-1"
    assert rec.stage is GuardrailStage.policy
    assert rec.decision.value == "deny"
    assert rec.detail["reason"] == "denied"
    assert rec.ts  # ISO timestamp stamped


async def test_emit_lineage_no_durable_store_returns_false() -> None:
    ctx = GuardrailContext(organization_id="org-1")  # no session, no bucket
    res = GuardResult.ok(GuardrailStage.input, {"prompt": "hi"})
    assert await audit.emit_lineage(ctx, res) is False


async def test_emit_lineage_with_session_is_durable(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def _fake_emit(session: Any, **kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(audit, "emit_audit_event", _fake_emit)
    ctx = GuardrailContext(organization_id="org-1", run_id="r1", agent_id="a1", session=object())
    res = GuardResult.block(GuardrailStage.input, "injection", flags=["injection:high"])

    durable = await audit.emit_lineage(ctx, res)
    assert durable is True
    assert captured["action"] == "guardrail.input.deny"
    assert captured["outcome"] == "blocked"
    assert captured["resource_type"] == "guardrail_stage"


async def test_emit_lineage_swallows_session_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _boom(session: Any, **kwargs: Any) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(audit, "emit_audit_event", _boom)
    ctx = GuardrailContext(organization_id="org-1", session=object())
    res = GuardResult.ok(GuardrailStage.input)
    # Must not raise; durable write failed so returns False.
    assert await audit.emit_lineage(ctx, res) is False
