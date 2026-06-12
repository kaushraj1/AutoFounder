"""Unit tests — conditional edge routers (AF-044)."""

from __future__ import annotations

import pytest

from app.agents.marketing.routers import (
    route_after_hallucination,
    route_after_hitl,
    route_after_ingest,
)


class TestRouteAfterIngest:
    def test_no_fatal_error_routes_to_analyse_brand(self) -> None:
        state = {"validated": True, "fatal_error": None, "errors": []}
        assert route_after_ingest(state) == "analyse_brand"

    def test_fatal_error_routes_to_error_handler(self) -> None:
        state = {
            "validated": False,
            "fatal_error": "feature_list.features is empty — FATAL",
            "errors": ["feature_list.features is empty"],
        }
        assert route_after_ingest(state) == "error_handler"

    def test_empty_fatal_error_string_routes_to_analyse_brand(self) -> None:
        state = {"validated": True, "fatal_error": "", "errors": []}
        assert route_after_ingest(state) == "analyse_brand"


class TestRouteAfterHallucination:
    def test_passed_routes_to_launch_control_center(self) -> None:
        state = {
            "hallucination_passed": True,
            "hallucination_retry_count": 0,
            "errors": [],
        }
        assert route_after_hallucination(state) == "launch_control_center"

    def test_failed_first_retry_routes_to_regenerate(self) -> None:
        state = {
            "hallucination_passed": False,
            "hallucination_retry_count": 0,
            "errors": [],
        }
        result = route_after_hallucination(state)
        assert result == "generate_landing_page"
        # retry_count should be incremented
        assert state["hallucination_retry_count"] == 1

    def test_failed_second_retry_routes_to_regenerate(self) -> None:
        state = {
            "hallucination_passed": False,
            "hallucination_retry_count": 1,
            "errors": [],
        }
        result = route_after_hallucination(state)
        assert result == "generate_landing_page"
        assert state["hallucination_retry_count"] == 2

    def test_exhausted_retries_routes_to_error_handler(self) -> None:
        """T6: After 2 retries, route to error_handler."""
        state = {
            "hallucination_passed": False,
            "hallucination_retry_count": 2,
            "errors": [],
        }
        assert route_after_hallucination(state) == "error_handler"


class TestRouteAfterHitl:
    def test_approved_routes_to_schedule(self) -> None:
        state = {"approval_status": "approved", "errors": []}
        assert route_after_hitl(state) == "schedule_posts"

    def test_partial_routes_to_schedule(self) -> None:
        state = {"approval_status": "partial", "errors": []}
        assert route_after_hitl(state) == "schedule_posts"

    def test_rejected_routes_to_error_handler(self) -> None:
        state = {"approval_status": "rejected", "errors": []}
        assert route_after_hitl(state) == "error_handler"

    def test_timed_out_routes_to_error_handler(self) -> None:
        """T8: Timeout must route to error_handler."""
        state = {"approval_status": "timed_out", "errors": []}
        assert route_after_hitl(state) == "error_handler"

    def test_pending_routes_to_error_handler(self) -> None:
        """Unknown/pending status should not route to schedule."""
        state = {"approval_status": "pending", "errors": []}
        assert route_after_hitl(state) == "error_handler"
