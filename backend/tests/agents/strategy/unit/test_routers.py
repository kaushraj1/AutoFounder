from app.agents.strategy.routers import (
    route_after_audit,
    route_after_join,
    route_after_normalize,
    route_terminal,
)
from app.agents.strategy.schema import StrategistState


def test_route_after_normalize():
    s = StrategistState(organization_id="org_1", idea_raw="Raw idea text details")
    assert route_after_normalize(s) == [
        "size_market",
        "discover_competitors",
        "mine_keywords",
        "generate_personas",
        "analyze_trends",
    ]

    s.fatal_error = "Something bad happened"
    assert route_after_normalize(s) == ["error_handler"]


def test_route_after_join():
    s = StrategistState(organization_id="org_1", idea_raw="Raw idea text details")
    assert route_after_join(s) == "audit_bias"

    s.error_count = 3  # retry_policy.max_retries is 3 by default
    assert route_after_join(s) == "error_handler"


def test_route_after_audit():
    s = StrategistState(organization_id="org_1", idea_raw="Raw idea text details")
    assert route_after_audit(s) == "synthesize_canvas"

    s.fatal_error = "Audit fatal error"
    assert route_after_audit(s) == "error_handler"


def test_route_terminal():
    s = StrategistState(organization_id="org_1", idea_raw="Raw idea text details")
    assert route_terminal(s) == "error_handler"  # missing report

    s.report_markdown = "## Report content"
    assert route_terminal(s) == "end"

    s.fatal_error = "Render failed"
    assert route_terminal(s) == "error_handler"
