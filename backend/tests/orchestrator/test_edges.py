"""Unit tests for `app.orchestrator.edges.route_after_pillar_5`.

Verifies the post-Pillar-5 routing reads `deployment_output.monthly_cost_usd`
(populated by the DevOps agent's cost estimator) and routes to either the
HITL `infra_spend_gate` node or directly to Pillar 6 based on the threshold.
"""

from __future__ import annotations

from app.orchestrator import edges


def test_route_after_pillar_5_under_threshold_skips_gate() -> None:
    state = {
        "deployment_output": {"monthly_cost_usd": 40.0},  # under $50
    }
    assert edges.route_after_pillar_5(state) == "run_pillar_6"


def test_route_after_pillar_5_over_threshold_fires_gate() -> None:
    state = {
        "deployment_output": {"monthly_cost_usd": 174.32},  # well over $50
    }
    assert edges.route_after_pillar_5(state) == "infra_spend_gate"


def test_route_after_pillar_5_exact_threshold_skips_gate() -> None:
    state = {
        "deployment_output": {"monthly_cost_usd": 50.0},  # exactly threshold => not >
    }
    assert edges.route_after_pillar_5(state) == "run_pillar_6"


def test_route_after_pillar_5_no_deployment_output_uses_legacy_field() -> None:
    state = {"cost_usd_cents": 6_000}  # $60
    assert edges.route_after_pillar_5(state) == "infra_spend_gate"


def test_route_after_pillar_5_no_data_at_all_skips_gate() -> None:
    state: dict = {}
    assert edges.route_after_pillar_5(state) == "run_pillar_6"
