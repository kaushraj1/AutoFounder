from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.eval.promptfoo_runner import PromptfooError, run_promptfoo, score_from_results


def test_score_from_results_computes_pass_rate() -> None:
    results = {"results": {"stats": {"successes": 8, "failures": 2}}}
    assert score_from_results(results) == 0.8


def test_score_from_results_handles_no_tests() -> None:
    assert score_from_results({"results": {"stats": {}}}) == 0.0


def test_run_promptfoo_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(PromptfooError, match="not found"):
        run_promptfoo(tmp_path / "missing.yaml")


def test_run_promptfoo_nonzero_exit_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "promptfoo.yaml"
    config.write_text("description: test\n", encoding="utf-8")

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="boom", stderr="error")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(PromptfooError, match="exit 1"):
        run_promptfoo(config)


def test_run_promptfoo_parses_output_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "promptfoo.yaml"
    config.write_text("description: test\n", encoding="utf-8")

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output_path = Path(cmd[cmd.index("--output") + 1])
        output_path.write_text(
            json.dumps({"results": {"stats": {"successes": 5, "failures": 0}}}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    results = run_promptfoo(config)
    assert score_from_results(results) == 1.0
