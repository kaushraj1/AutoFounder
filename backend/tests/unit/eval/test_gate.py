from __future__ import annotations

from pathlib import Path

import pytest

from app.eval import gate
from app.eval.baseline import load_baseline, save_baseline
from app.eval.gate import RegressionGateError, evaluate, run_gate


def test_evaluate_no_baseline_passes_and_has_no_regression() -> None:
    result = evaluate(agent="architect", golden_set="architect", score=0.9, baseline=None)
    assert result.passed
    assert result.baseline is None
    assert result.regression_pct is None


def test_evaluate_improvement_passes() -> None:
    result = evaluate(agent="architect", golden_set="architect", score=0.95, baseline=0.9)
    assert result.passed
    assert result.regression_pct < 0


def test_evaluate_small_regression_within_threshold_passes() -> None:
    # 1% drop, default threshold is 2%
    result = evaluate(agent="architect", golden_set="architect", score=0.891, baseline=0.9)
    assert result.passed
    assert result.regression_pct == pytest.approx(1.0, abs=1e-6)


def test_evaluate_large_regression_fails() -> None:
    # 10% drop, default threshold is 2%
    result = evaluate(agent="architect", golden_set="architect", score=0.81, baseline=0.9)
    assert not result.passed
    assert result.regression_pct == pytest.approx(10.0, abs=1e-6)


def test_evaluate_zero_baseline_does_not_divide_by_zero() -> None:
    result = evaluate(agent="architect", golden_set="architect", score=0.0, baseline=0.0)
    assert result.passed
    assert result.regression_pct == 0.0


def test_run_gate_first_run_writes_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "promptfoo.yaml"
    config_path.write_text("description: test\n", encoding="utf-8")

    monkeypatch.setattr(
        gate,
        "run_promptfoo",
        lambda config: {"results": {"stats": {"successes": 9, "failures": 1}}},
    )

    result = run_gate(agent="architect", config_path=config_path)
    assert result.passed
    assert result.baseline is None
    assert load_baseline(tmp_path) == 0.9


def test_run_gate_regression_raises_without_updating_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "promptfoo.yaml"
    config_path.write_text("description: test\n", encoding="utf-8")
    save_baseline(tmp_path, 0.9)

    monkeypatch.setattr(
        gate,
        "run_promptfoo",
        lambda config: {"results": {"stats": {"successes": 6, "failures": 4}}},
    )

    with pytest.raises(RegressionGateError):
        run_gate(agent="architect", config_path=config_path)

    assert load_baseline(tmp_path) == 0.9


def test_run_gate_passing_score_can_update_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "promptfoo.yaml"
    config_path.write_text("description: test\n", encoding="utf-8")
    save_baseline(tmp_path, 0.9)

    monkeypatch.setattr(
        gate,
        "run_promptfoo",
        lambda config: {"results": {"stats": {"successes": 10, "failures": 0}}},
    )

    result = run_gate(agent="architect", config_path=config_path, update_baseline=True)
    assert result.passed
    assert load_baseline(tmp_path) == 1.0
