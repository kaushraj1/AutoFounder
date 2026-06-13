"""Eval harness (AF-050).

Promptfoo golden-set runner + regression gate shared by every pillar agent.
Each agent owns a golden set under ``backend/tests/golden/<agent>/promptfoo.yaml``
(see ``architect`` for the reference layout). The harness:

1. Runs the golden set via the Promptfoo CLI (``npx promptfoo eval``) and reduces
   the per-test pass/fail results to a single ``score`` in ``[0, 1]``.
2. Compares ``score`` against the last-known-good ``baseline`` for that agent,
   stored alongside the golden set as ``baseline.json``.
3. Raises :class:`app.eval.gate.RegressionGateError` if the score regresses by
   more than the configured threshold (default 2%), so CI can block prompt
   promotion on a quality drop.
"""

from app.eval.gate import RegressionGateError, run_gate
from app.eval.promptfoo_runner import PromptfooError, run_promptfoo, score_from_results
from app.eval.schema import EvalResult

__all__ = [
    "EvalResult",
    "PromptfooError",
    "RegressionGateError",
    "run_gate",
    "run_promptfoo",
    "score_from_results",
]
