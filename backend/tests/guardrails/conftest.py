"""Shared fixtures for guardrail tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.guardrails.schema import GuardrailContext
from app.guardrails.stages import reset_guardrail_state


@pytest.fixture(autouse=True)
def _reset_state() -> Iterator[None]:
    """Isolate the in-process stage ledgers (rate/cost/strikes/drift) per test."""
    reset_guardrail_state()
    yield
    reset_guardrail_state()


@pytest.fixture
def ctx() -> GuardrailContext:
    return GuardrailContext(organization_id="org-test", run_id="run-1", agent_id="agent.x")
