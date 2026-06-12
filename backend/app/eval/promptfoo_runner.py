"""Subprocess wrapper around the Promptfoo CLI.

Promptfoo (https://promptfoo.dev) runs an agent's golden-set prompts against
real model providers and asserts on the responses (JSON shape checks,
LLM-as-judge rubrics, etc). It ships as an npm package and is invoked here via
``npx`` so no Python binding is required — see ``backend/tests/golden/<agent>/``
for golden-set configs.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


class PromptfooError(RuntimeError):
    """Raised when the Promptfoo CLI fails to run or its output can't be parsed."""


def run_promptfoo(config_path: Path, *, extra_args: tuple[str, ...] = ()) -> dict:
    """Run ``npx promptfoo eval`` against ``config_path`` and return the parsed results.

    Results are written to a temporary JSON file via Promptfoo's ``-o`` flag and
    read back, since Promptfoo's stdout is human-readable progress output, not JSON.
    """
    if not config_path.exists():
        raise PromptfooError(f"Promptfoo config not found at: {config_path}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "results.json"
        cmd = [
            "npx",
            "promptfoo",
            "eval",
            "--config",
            str(config_path),
            "--output",
            str(output_path),
            "--no-cache",
            *extra_args,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise PromptfooError(
                f"promptfoo eval failed (exit {proc.returncode}) for {config_path}:\n"
                f"{proc.stdout}\n{proc.stderr}"
            )
        if not output_path.exists():
            raise PromptfooError(f"promptfoo eval produced no output file for {config_path}")
        try:
            return json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PromptfooError(f"promptfoo eval produced invalid JSON: {exc}") from exc


def score_from_results(results: dict) -> float:
    """Reduce a Promptfoo results document to a single pass-rate score in ``[0, 1]``.

    Promptfoo's ``-o results.json`` document nests stats under
    ``results.stats.{successes,failures}``. A golden set with zero test cases
    scores ``0.0`` (treated as a failure rather than a vacuous pass).
    """
    stats = results.get("results", {}).get("stats", {})
    successes = stats.get("successes", 0)
    failures = stats.get("failures", 0)
    total = successes + failures
    if total == 0:
        return 0.0
    return successes / total
