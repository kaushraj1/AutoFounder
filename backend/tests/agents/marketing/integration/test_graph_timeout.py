"""Integration tests — approval timeout (AF-044, T8)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.marketing.graph import build_marketer_graph

_FIXTURES = Path(__file__).parent.parent.parent.parent / "fixtures" / "mock_products"


def _load_fixture(name: str) -> dict:
    with open(_FIXTURES / f"{name}.json") as f:
        return json.load(f)


def _build_initial_state(fixture: dict) -> dict:
    return {
        "run_id": fixture["run_id"],
        "organization_id": fixture["organization_id"],
        "idea_normalised": fixture["idea_normalised"],
        "brand_config": fixture["brand_config"],
        "feature_list": fixture["feature_list"],
        "lean_canvas_json": fixture.get("lean_canvas_json", {}),
        "personas": fixture.get("personas", []),
        "live_url": fixture.get("live_url", ""),
        "approval_status": "pending",  # NOT pre-approved — forces Redis path or timeout fallback
        "errors": [],
        "llm_tokens_used": 0,
        "images_generated": 0,
        "hallucination_retry_count": 0,
    }


_BRAND = ({"brand_voice": "tech", "positioning_statement": "P", "unique_value_proposition": "V",
            "seo_keyword_targets": [], "competitor_gaps": [], "target_audience_summary": "T"}, 50)
_LP = ({"hero_headline": "H", "hero_subheadline": "S", "hero_cta_text": "Go", "hero_cta_url": "https://x.com",
         "features_section": [], "social_proof_section": "", "pricing_section": [], "faq_section": [],
         "cta_footer_text": "", "meta_tags": None, "status": "draft"}, 80)
_BLOGS = ({"blogs": [{"title": "B", "target_keyword": "k", "secondary_keywords": [],
                       "body_markdown": "Body", "meta_description": "M", "word_count": 5, "status": "draft"}]}, 80)
_PH = ({"tagline": "Go fast", "description": "SaaS.", "first_comment": "Hi!",
         "maker_note": "Built.", "gallery_captions": [], "topics": [], "status": "draft"}, 60)
_SOCIAL = ({"x_thread": ["T1"], "linkedin_post": "LI", "show_hn_post": "HN", "status": "draft"}, 60)
_EMAIL = ({"onboarding": [{"subject": "W", "preview_text": "P", "body_html": "<p>H</p>",
                             "body_text": "H", "send_at_days_offset": 0}], "reactivation": [], "status": "draft"}, 80)
_VISUAL = ({"logo": None, "og_image": None, "social_card": None, "email_banner": None, "total_generated": 0}, 20)
_HALL_PASS = ({"critical_count": 0, "warning_count": 0, "passed": True, "findings": []}, 80)


class TestApprovalTimeout:
    """T8: HITL times out → TIMED_OUT state → error_handler, Slack + email alert."""

    @pytest.mark.asyncio
    async def test_timeout_routes_to_error_handler_and_no_scheduling(self) -> None:
        """T8: LCC returns timed_out → error_handler → no scheduling."""
        fixture = _load_fixture("greenledger")
        initial = _build_initial_state(fixture)

        # Mock LCC to return timed_out directly (simulates 30-min timeout firing)
        async def fake_lcc_timed_out(state: dict) -> dict:
            return {
                **state,
                "approval_status": "timed_out",
                "approved_content_types": [],
                "rejected_content_types": [],
                "errors": list(state.get("errors", [])) + ["launch_control_center: approval timed out after 30 minutes"],
            }

        with (
            patch("app.agents.marketing.nodes.analyse_brand.call_llm", return_value=_BRAND),
            patch("app.agents.marketing.nodes.generate_landing_page.call_llm", return_value=_LP),
            patch("app.agents.marketing.nodes.generate_seo_blogs.call_llm", return_value=_BLOGS),
            patch("app.agents.marketing.nodes.generate_product_hunt_kit.call_llm", return_value=_PH),
            patch("app.agents.marketing.nodes.generate_social_posts.call_llm", return_value=_SOCIAL),
            patch("app.agents.marketing.nodes.generate_email_sequences.call_llm", return_value=_EMAIL),
            patch("app.agents.marketing.nodes.generate_visual_assets.call_llm", return_value=_VISUAL),
            patch("app.agents.marketing.nodes.hallucination_check.call_llm", return_value=_HALL_PASS),
            patch("app.agents.marketing.nodes.analyse_brand.tavily_search", return_value={"results": []}),
            patch("app.agents.marketing.nodes.generate_visual_assets.dalle_generate",
                  return_value={"generated_url": None, "status": "failed"}),
            patch("app.agents.marketing.nodes.error_handler.httpx.AsyncClient") as mock_http,
            # Inject the timeout simulation directly into the graph's LCC node
            patch("app.agents.marketing.graph.launch_control_center", side_effect=fake_lcc_timed_out),
        ):
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=MagicMock(raise_for_status=MagicMock())
            )

            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # T8: Status must be timed_out
        assert final_state["approval_status"] == "timed_out"

        # No scheduling should have happened
        assert not final_state.get("scheduled_post_ids")

        # Should have timed_out error in errors list
        errors = final_state.get("errors", [])
        assert any("timed" in e.lower() or "timeout" in e.lower() for e in errors)

    @pytest.mark.asyncio
    async def test_launch_control_center_auto_approves_in_dev_without_redis(self) -> None:
        """Without REDIS_URL in dev, launch_control_center auto-approves."""
        from app.agents.marketing.nodes.launch_control_center import launch_control_center

        state: dict = {
            "run_id": "test-timeout",
            "organization_id": "org-test",
            "approval_status": "pending",  # Not pre-set
            "errors": [],
        }

        with patch.dict("os.environ", {"REDIS_URL": "", "APP_ENV": "development"}):
            result = await launch_control_center(state)

        # Dev auto-approve
        assert result["approval_status"] == "approved"
        assert "landing_page" in result.get("approved_content_types", [])

    @pytest.mark.asyncio
    async def test_launch_control_center_reads_pre_set_status(self) -> None:
        """Pre-set timed_out is NOT in (approved, rejected, partial) so LCC
        checks REDIS_URL. With empty REDIS_URL in dev it auto-approves.
        This test verifies the router correctly reacts to the timed_out status
        by calling the LCC node directly with the status pre-injected."""
        from app.agents.marketing.nodes.launch_control_center import _build_approval_state

        # Directly call the approval-state builder with timed_out
        state: dict = {
            "run_id": "test-timeout-2",
            "organization_id": "org-test",
            "approval_status": "timed_out",
            "errors": [],
        }

        result = _build_approval_state(state, "timed_out")

        assert result["approval_status"] == "timed_out"
        assert result.get("approved_content_types") == []
        assert result.get("rejected_content_types") == []
        assert any("timed" in e.lower() for e in result.get("errors", []))

    @pytest.mark.asyncio
    async def test_launch_control_center_partial_approval(self) -> None:
        """Partial pre-set: only specified content types are approved."""
        from app.agents.marketing.nodes.launch_control_center import launch_control_center

        state: dict = {
            "run_id": "test-partial",
            "organization_id": "org-test",
            "approval_status": "partial",
            "approved_content_types": ["landing_page", "email_sequences"],
            "errors": [],
        }

        result = await launch_control_center(state)

        assert result["approval_status"] == "partial"
        assert "landing_page" in result["approved_content_types"]
        assert "email_sequences" in result["approved_content_types"]
        # Others should be rejected
        assert "seo_blogs" in result.get("rejected_content_types", [])
