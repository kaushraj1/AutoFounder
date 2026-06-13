"""Regression gate — blocks prompt promotion on a golden-set score drop.

Ties together the Promptfoo runner (``app.eval.promptfoo_runner``) and the
baseline store (``app.eval.baseline``): run the golden set, compare the
resulting score to the agent's last-known-good baseline, and fail if the
score regressed by more than ``threshold_pct``. CI runs ``run_gate`` for each
agent's golden set on prompt-affecting changes; a raised
:class:`RegressionGateError` fails the job.
"""

from __future__ import annotations

from pathlib import Path

from app.eval.baseline import load_baseline, save_baseline
from app.eval.promptfoo_runner import run_promptfoo, score_from_results
from app.eval.schema import EvalResult

#: Default maximum allowed drop in score, as a percentage of the baseline.
DEFAULT_REGRESSION_THRESHOLD_PCT = 2.0


class RegressionGateError(RuntimeError):
    """Raised by :func:`run_gate` when an agent's golden-set score regresses too much."""

    def __init__(self, result: EvalResult, threshold_pct: float) -> None:
        self.result = result
        self.threshold_pct = threshold_pct
        super().__init__(
            f"{result.agent}/{result.golden_set}: score {result.score:.4f} regressed "
            f"{result.regression_pct:.2f}% from baseline {result.baseline:.4f} "
            f"(threshold {threshold_pct:.2f}%)"
        )


def evaluate(
    *,
    agent: str,
    golden_set: str,
    score: float,
    baseline: float | None,
    threshold_pct: float = DEFAULT_REGRESSION_THRESHOLD_PCT,
) -> EvalResult:
    """Compare ``score`` against ``baseline`` and build the :class:`EvalResult`.

    No baseline yet (first run for this golden set) always passes — the
    caller is expected to persist ``score`` as the new baseline in that case.
    A score that improves on the baseline always passes regardless of
    ``threshold_pct``.
    """
    if baseline is None:
        return EvalResult(
            agent=agent,
            golden_set=golden_set,
            score=score,
            baseline=None,
            regression_pct=None,
            passed=True,
        )

    regression_pct = 0.0 if baseline == 0 else (baseline - score) / baseline * 100
    passed = regression_pct <= threshold_pct
    return EvalResult(
        agent=agent,
        golden_set=golden_set,
        score=score,
        baseline=baseline,
        regression_pct=regression_pct,
        passed=passed,
    )


def run_gate(
    *,
    agent: str,
    config_path: Path,
    threshold_pct: float = DEFAULT_REGRESSION_THRESHOLD_PCT,
    update_baseline: bool = False,
) -> EvalResult:
    """Run an agent's golden set and gate its score against its baseline.

    Raises :class:`RegressionGateError` if the score regressed beyond
    ``threshold_pct``. When ``update_baseline`` is true (or no baseline exists
    yet), the resulting score is written back as the new baseline on success.
    """
    golden_set_dir = config_path.parent
    golden_set = golden_set_dir.name

    results = run_promptfoo(config_path)
    score = score_from_results(results)
    baseline = load_baseline(golden_set_dir)

    result = evaluate(
        agent=agent,
        golden_set=golden_set,
        score=score,
        baseline=baseline,
        threshold_pct=threshold_pct,
    )

    if not result.passed:
        raise RegressionGateError(result, threshold_pct)

    if baseline is None or update_baseline:
        save_baseline(golden_set_dir, score)

    return result
