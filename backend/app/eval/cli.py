"""CLI entrypoint for the eval harness.

Usage::

    uv run python -m app.eval <agent> <path/to/promptfoo.yaml> \
        [--update-baseline] [--threshold-pct 2.0]

Exits non-zero (via :class:`app.eval.gate.RegressionGateError`) when an
agent's golden-set score regresses beyond the threshold, so CI can use this
as a quality gate on prompt-affecting changes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.eval.gate import DEFAULT_REGRESSION_THRESHOLD_PCT, RegressionGateError, run_gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an agent's Promptfoo golden set.")
    parser.add_argument("agent", help="Agent ID, e.g. 'architect'")
    parser.add_argument("config", type=Path, help="Path to the agent's promptfoo.yaml")
    parser.add_argument(
        "--threshold-pct",
        type=float,
        default=DEFAULT_REGRESSION_THRESHOLD_PCT,
        help="Max allowed score regression, as a percent of baseline (default: 2.0)",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write the new score as the baseline even if it didn't regress",
    )
    args = parser.parse_args(argv)

    try:
        result = run_gate(
            agent=args.agent,
            config_path=args.config,
            threshold_pct=args.threshold_pct,
            update_baseline=args.update_baseline,
        )
    except RegressionGateError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: {result.model_dump_json()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
