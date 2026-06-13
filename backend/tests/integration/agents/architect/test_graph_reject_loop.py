"""Integration test — Founder rejects → re-plan loop (AF-040).

Simulates: first HITL = rejected → graph loops back to select_stack
→ second HITL = approved → graph ends cleanly.
"""

from __future__ import annotations

import pytest

from app.agents.architect.graph import build_architect_graph
from tests.integration.agents.architect.fake_llm import patch_llm


@pytest.fixture()
def rejected_then_approved_state() -> dict:
    """State where Founder initially rejects, then approves on loop."""
    return {
        "run_id": "inttest-reject-001",
        "organization_id": "org-test",
        "idea_normalised": "A secrets management SaaS",
        "viability_band": "high",
        "lean_canvas": {},
        "prd": "Simple PRD for testing reject loop",
        # Start with rejected — the hitl_gate node reads this
        "approval_status": "rejected",
        "rejection_comment": "Please add a mobile-first stack option",
        "errors": [],
        "llm_tokens_used": 0,
    }


class TestRejectLoop:
    def test_rejected_state_re_routes_to_select_stack(self, rejected_then_approved_state):
        """Graph should route back into select_stack when rejected.

        We patch the HITL router so after the first rejection it becomes
        approved, simulating the re-design cycle completing.
        """
        call_count = {"hitl": 0}

        def _fake_route_after_hitl(state):
            call_count["hitl"] += 1
            if call_count["hitl"] == 1:
                return "select_stack"  # first call → rejected, re-design
            return "end"  # second call → approved

        with patch_llm():
            from unittest.mock import patch as mock_patch

            with mock_patch(
                "app.agents.architect.graph.route_after_hitl",
                side_effect=_fake_route_after_hitl,
            ):
                graph = build_architect_graph()
                # Force approved on second pass so test terminates
                state = {**rejected_then_approved_state, "approval_status": "approved"}
                result = graph.invoke(state)

        assert result["approval_status"] == "approved"

    def test_rejection_comment_preserved_in_state(self, rejected_then_approved_state):
        """Rejection comment must survive the state transition."""
        state = {**rejected_then_approved_state, "approval_status": "approved"}
        with patch_llm():
            result = build_architect_graph().invoke(state)

        assert result.get("rejection_comment") == "Please add a mobile-first stack option"
