from __future__ import annotations

from pathlib import Path

from app.eval.baseline import load_baseline, save_baseline


def test_load_baseline_missing_returns_none(tmp_path: Path) -> None:
    assert load_baseline(tmp_path) is None


def test_save_and_load_baseline_roundtrip(tmp_path: Path) -> None:
    save_baseline(tmp_path, 0.875)
    assert load_baseline(tmp_path) == 0.875


def test_save_baseline_overwrites(tmp_path: Path) -> None:
    save_baseline(tmp_path, 0.5)
    save_baseline(tmp_path, 0.9)
    assert load_baseline(tmp_path) == 0.9
