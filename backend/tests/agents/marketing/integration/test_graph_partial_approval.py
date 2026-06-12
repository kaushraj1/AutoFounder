"""Integration tests — partial approval (AF-044, T7)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.marketing.graph import build_marketer_graph

_FIXTURES = Path(__file__).parent.parent.parent.parent / "fixtures" / "mock_products"


def _load_fixture(name: str) -> dict:
    with open(_FIXTURES / f"{name}.json") as f:
        return json.load(f)


def _build_initial_state(fixture: dict, *, approval_status: str = "approved") -> dict:
    return {
        "run_id": fixture["run_id"],
        "organization_id": fixture["organization_id"],
        "idea_normalised": fixture["idea_normalised"],
        "brand_config": fixture["brand_config"],
        "feature_list": fixture["feature_list"],
        "lean_canvas_json": fixture.get("lean_canvas_json", {}),
        "personas": fixture.get("personas", []),
        "live_url": fixture.get("live_url", ""),
        "approval_status": approval_status,
        # Partial: pre-set which types are approved so launch_control_center reads them
        "approved_content_types": ["landing_page", "social_posts", "email_sequences"],
        "errors": [],
        "llm_tokens_used": 0,
        "images_generated": 0,
        "hallucination_retry_count": 0,
    }


# Shared mock return values
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
_GTM = ("# GTM Report — partial approval", 80)


class TestPartialApproval:
    """T7: Founder partially approves content — only approved types are scheduled."""

    @pytest.mark.asyncio
    async def test_partial_approval_schedules_only_approved_types(self) -> None:
        """T7: partial status → only approved content types get scheduled."""
        fixture = _load_fixture("devpulse")
        initial = _build_initial_state(fixture, approval_status="partial")
        # approved_content_types = ["landing_page", "social_posts", "email_sequences"]
        # rejected = ["seo_blogs", "product_hunt_kit", "visual_assets"]

        schedule_calls: list[str] = []

        async def fake_typefully(tweets, **kw):
            schedule_calls.append("x")
            return {"thread_id": "t1", "status": "scheduled", "channel": "x"}

        async def fake_buffer(content, **kw):
            schedule_calls.append("linkedin")
            return {"post_id": "b1", "status": "scheduled", "channel": "linkedin"}

        async def fake_resend(**kw):
            schedule_calls.append("email")
            return {"email_id": "r1", "status": "sent"}

        with (
            patch("app.agents.marketing.nodes.analyse_brand.call_llm", return_value=_BRAND),
            patch("app.agents.marketing.nodes.generate_landing_page.call_llm", return_value=_LP),
            patch("app.agents.marketing.nodes.generate_seo_blogs.call_llm", return_value=_BLOGS),
            patch("app.agents.marketing.nodes.generate_product_hunt_kit.call_llm", return_value=_PH),
            patch("app.agents.marketing.nodes.generate_social_posts.call_llm", return_value=_SOCIAL),
            patch("app.agents.marketing.nodes.generate_email_sequences.call_llm", return_value=_EMAIL),
            patch("app.agents.marketing.nodes.generate_visual_assets.call_llm", return_value=_VISUAL),
            patch("app.agents.marketing.nodes.hallucination_check.call_llm", return_value=_HALL_PASS),
            patch("app.agents.marketing.nodes.render_gtm_report.call_llm_text", return_value=_GTM),
            patch("app.agents.marketing.nodes.analyse_brand.tavily_search", return_value={"results": []}),
            patch("app.agents.marketing.nodes.generate_visual_assets.dalle_generate",
                  return_value={"generated_url": None, "status": "failed"}),
            patch("app.agents.marketing.nodes.schedule_posts.typefully_schedule", side_effect=fake_typefully),
            patch("app.agents.marketing.nodes.schedule_posts.buffer_schedule", side_effect=fake_buffer),
            patch("app.agents.marketing.nodes.schedule_posts.resend_broadcast", side_effect=fake_resend),
        ):
            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # T7: approval_status == "partial"
        assert final_state["approval_status"] == "partial"

        # X and LinkedIn should be scheduled (social_posts is approved)
        assert "x" in schedule_calls
        assert "linkedin" in schedule_calls

        # Email should be scheduled (email_sequences is approved)
        assert "email" in schedule_calls

        # Rejected content types should be in state
        rejected = final_state.get("rejected_content_types", [])
        # seo_blogs, product_hunt_kit, visual_assets should NOT be in approved
        approved = final_state.get("approved_content_types", [])
        assert "seo_blogs" not in approved or "seo_blogs" in rejected

        # GTM report should still be generated
        assert "# GTM Report" in final_state.get("gtm_report_markdown", "")

    @pytest.mark.asyncio
    async def test_full_rejection_routes_to_error_handler(self) -> None:
        """T7 edge: Full rejection → error_handler, no scheduling."""
        fixture = _load_fixture("calmhq")
        initial = _build_initial_state(fixture, approval_status="rejected")
        initial["approved_content_types"] = []

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
            patch("app.agents.marketing.nodes.error_handler.httpx.AsyncClient"),
        ):
            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # No scheduling should have happened
        assert not final_state.get("scheduled_post_ids")
        # Approval status is rejected
        assert final_state["approval_status"] == "rejected"
