from app.agents.strategy.schema import StrategistState


def route_after_normalize(state: StrategistState) -> list[str]:
    """Route to parallel research nodes or error handler."""
    if state.fatal_error:
        return ["error_handler"]
    return [
        "size_market",
        "discover_competitors",
        "mine_keywords",
        "generate_personas",
        "analyze_trends",
    ]


def route_after_join(state: StrategistState) -> str:
    """Route to bias audit if retries did not fail fatally."""
    if state.error_count >= state.retry_policy.max_retries or state.fatal_error:
        return "error_handler"
    return "audit_bias"


def route_after_audit(state: StrategistState) -> str:
    """Route to canvas synthesis if bias audit was successful."""
    if state.fatal_error:
        return "error_handler"
    return "synthesize_canvas"


def route_terminal(state: StrategistState) -> str:
    """Determine whether to end normally or route to error sink."""
    if state.fatal_error or not state.report_markdown:
        return "error_handler"
    return "end"
