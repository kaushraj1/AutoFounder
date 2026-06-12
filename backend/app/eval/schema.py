"""Eval result schema shared by the Promptfoo runner, regression gate, and CI."""

from __future__ import annotations

from pydantic import BaseModel


class EvalResult(BaseModel):
    """Outcome of running an agent's golden set through the eval harness.

    ``baseline`` and ``regression_pct`` are ``None`` the first time a golden
    set is scored, since there is nothing yet to compare against — the gate
    treats that case as a pass and writes ``score`` as the new baseline.
    """

    agent: str
    golden_set: str
    score: float
    baseline: float | None = None
    regression_pct: float | None = None
    passed: bool
