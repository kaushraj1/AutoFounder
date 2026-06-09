"""Node 8 — test_join: synchronization barrier for the 5 parallel gates (plan §3.4)."""

from __future__ import annotations

import logging

from app.agents.reviewer.schema import ReviewerState

logger = logging.getLogger("app.agents.reviewer.nodes.test_join")


async def test_join(state: ReviewerState) -> dict:
    """Barrier where the parallel test/scan branches converge."""
    logger.info(
        "test_join: lint=%d findings=%d unit=%s for run %s",
        len(state.lint_results),
        len(state.security_findings),
        state.unit_test_result.status if state.unit_test_result else "none",
        state.run_id,
    )
    return {}
