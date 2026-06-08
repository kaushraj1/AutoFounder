"""CLI: load a CoderOutput JSON, build DevOpsState, print it.

Run from the backend/ directory (so the `app` package resolves):
  cd backend
  .venv\\Scripts\\python.exe -m app.agents.devops.run_local \
      --input ..\\.claude\\specs\\pillar5-dummy-input.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .schema import DevOpsState
from .utils.cost import estimate_monthly_cost_usd


def _build_state(payload: dict) -> DevOpsState:
    # Dummy uses github_repo_html_url; DevOpsState calls it repo_url.
    payload.setdefault("repo_url", payload.get("github_repo_html_url", ""))
    state = DevOpsState.model_validate(payload)
    state.estimated_monthly_cost_usd = estimate_monthly_cost_usd(state.services)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the DevOps Agent locally against a CoderOutput JSON.",
    )
    parser.add_argument("--input", type=Path, required=True, help="Path to the CoderOutput JSON.")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    state = _build_state(payload)
    print(state.model_dump_json(indent=2))


if __name__ == "__main__":
    main()