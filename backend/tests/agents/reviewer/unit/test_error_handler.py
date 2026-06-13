"""Unit — error_handler escalation helpers (_summarise_failures, _alert_slack)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.agents.reviewer.nodes.error_handler import _alert_slack, _summarise_failures
from app.agents.reviewer.schema import NodeStatus, NodeTrace
from tests.agents.reviewer.conftest import make_state


def test_summarise_failures_from_node_traces() -> None:
    state = make_state(node_traces=[NodeTrace(node="run_unit_tests", status=NodeStatus.FAILED)])
    assert "run_unit_tests" in _summarise_failures(state)


def test_summarise_failures_from_current_failures() -> None:
    state = make_state(current_failures=["lint: 3 errors"])
    assert "lint: 3 errors" in _summarise_failures(state)


def test_summarise_failures_default() -> None:
    assert "unspecified" in _summarise_failures(make_state())


@respx.mock
async def test_alert_slack_posts_payload() -> None:
    route = respx.post("https://hooks.slack.test/x").mock(return_value=httpx.Response(200))
    state = make_state(owasp_violations=["A03:2021-Injection [semgrep:sqli] db.py"])
    await _alert_slack(state, "owasp hard block", "https://hooks.slack.test/x")
    assert route.called
    payload = json.loads(route.calls[0].request.content)
    assert "owasp hard block" in payload["text"]
    assert "A03" in payload["text"]


@pytest.mark.asyncio
async def test_alert_slack_no_webhook_is_noop() -> None:
    # No webhook configured → returns without attempting any HTTP call (no raise).
    await _alert_slack(make_state(), "reason", "")
