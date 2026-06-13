from __future__ import annotations

from app.eval.schema import EvalResult


def test_eval_result_defaults_for_first_run() -> None:
    result = EvalResult(agent="architect", golden_set="architect", score=0.9, passed=True)
    assert result.baseline is None
    assert result.regression_pct is None


def test_eval_result_with_regression() -> None:
    result = EvalResult(
        agent="architect",
        golden_set="architect",
        score=0.81,
        baseline=0.9,
        regression_pct=10.0,
        passed=False,
    )
    assert not result.passed
    assert result.regression_pct == 10.0
