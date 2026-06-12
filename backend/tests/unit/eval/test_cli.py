from __future__ import annotations

from pathlib import Path

import pytest

from app.eval import cli, gate


def test_cli_passes_on_first_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "promptfoo.yaml"
    config_path.write_text("description: test\n", encoding="utf-8")

    monkeypatch.setattr(
        gate,
        "run_promptfoo",
        lambda config: {"results": {"stats": {"successes": 10, "failures": 0}}},
    )

    exit_code = cli.main(["architect", str(config_path)])
    assert exit_code == 0


def test_cli_fails_on_regression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "promptfoo.yaml"
    config_path.write_text("description: test\n", encoding="utf-8")
    gate.save_baseline(tmp_path, 0.9)

    monkeypatch.setattr(
        gate,
        "run_promptfoo",
        lambda config: {"results": {"stats": {"successes": 6, "failures": 4}}},
    )

    exit_code = cli.main(["architect", str(config_path)])
    assert exit_code == 1
    assert "FAIL" in capsys.readouterr().err
