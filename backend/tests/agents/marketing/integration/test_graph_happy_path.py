"""Integration tests — graph happy path (AF-044, T1)."""

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
        "approval_status": fixture.get("approval_status", "approved"),
        "errors": [],
        "llm_tokens_used": 0,
        "images_generated": 0,
        "hallucination_retry_count": 0,
    }


def _llm_side_effect(prompt: str, **kw) -> tuple:
    """Return appropriate mock JSON based on prompt content."""
    if "brand voice" in prompt.lower():
        return ({"brand_voice": "technical", "positioning_statement": "Test positioning",
                 "unique_value_proposition": "Test UVP", "seo_keyword_targets": ["saas"],
                 "competitor_gaps": ["Gap 1"], "target_audience_summary": "Test audience"}, 100)
    elif "hero_headline" in prompt:
        return ({"hero_headline": "Ship Fast", "hero_subheadline": "Sub",
                 "hero_cta_text": "Get Started", "hero_cta_url": "https://shipfast.dev",
                 "features_section": [{"title": "Auth", "description": "Pre-wired auth"}],
                 "social_proof_section": "", "pricing_section": [], "faq_section": [],
                 "cta_footer_text": "Start", "meta_tags": None, "status": "draft"}, 200)
    elif "blogs" in prompt.lower() or "seo" in prompt.lower():
        return ({"blogs": [{"title": "Blog 1", "target_keyword": "saas",
                            "secondary_keywords": [], "body_markdown": "# Blog\nContent here " * 100,
                            "meta_description": "Meta", "word_count": 500, "status": "draft"}]}, 200)
    elif "product hunt" in prompt.lower() or "tagline" in prompt.lower():
        return ({"tagline": "Ship fast", "description": "A boilerplate for SaaS founders.",
                 "first_comment": "Hey PH!", "maker_note": "Built to ship fast.",
                 "gallery_captions": ["Cap 1"], "topics": ["Dev Tools"], "status": "draft"}, 150)
    elif "x_thread" in prompt or "social" in prompt.lower():
        return ({"x_thread": ["Tweet 1", "Tweet 2"], "linkedin_post": "LinkedIn post",
                 "show_hn_post": "Show HN post", "status": "draft"}, 150)
    elif "onboarding" in prompt.lower():
        return ({"onboarding": [{"subject": "Welcome!", "preview_text": "Get started",
                                 "body_html": "<p>Hi</p>", "body_text": "Hi", "send_at_days_offset": 0}],
                 "reactivation": [], "status": "draft"}, 200)
    elif "dall" in prompt.lower() or "dall_e_prompt" in prompt:
        return ({"logo": {"asset_type": "logo", "dall_e_prompt": "A logo", "generated_url": None, "status": "pending"},
                 "og_image": {"asset_type": "og_image", "dall_e_prompt": "OG image", "generated_url": None, "status": "pending"},
                 "social_card": {"asset_type": "social_card", "dall_e_prompt": "Social", "generated_url": None, "status": "pending"},
                 "email_banner": {"asset_type": "email_banner", "dall_e_prompt": "Banner", "generated_url": None, "status": "pending"},
                 "total_generated": 0}, 50)
    elif "hallucination" in prompt.lower() or "fact-checker" in prompt.lower():
        return ({"critical_count": 0, "warning_count": 0, "passed": True, "findings": []}, 200)
    else:
        return ({}, 0)


class TestGraphHappyPath:
    """T1: Happy path — all content generated, approved, and scheduled."""

    @pytest.mark.asyncio
    async def test_graph_runs_to_completion(self) -> None:
        """T1: Full graph with mocked LLM + tools → complete MarketerState."""
        fixture = _load_fixture("shipfast")
        initial = _build_initial_state(fixture)

        with (
            patch("app.agents.marketing.nodes.analyse_brand.call_llm", new_callable=AsyncMock) as mock_brand,
            patch("app.agents.marketing.nodes.generate_landing_page.call_llm", new_callable=AsyncMock) as mock_lp,
            patch("app.agents.marketing.nodes.generate_seo_blogs.call_llm", new_callable=AsyncMock) as mock_blogs,
            patch("app.agents.marketing.nodes.generate_product_hunt_kit.call_llm", new_callable=AsyncMock) as mock_ph,
            patch("app.agents.marketing.nodes.generate_social_posts.call_llm", new_callable=AsyncMock) as mock_social,
            patch("app.agents.marketing.nodes.generate_email_sequences.call_llm", new_callable=AsyncMock) as mock_email,
            patch("app.agents.marketing.nodes.generate_visual_assets.call_llm", new_callable=AsyncMock) as mock_visual,
            patch("app.agents.marketing.nodes.hallucination_check.call_llm", new_callable=AsyncMock) as mock_hall,
            patch("app.agents.marketing.nodes.render_gtm_report.call_llm_text", new_callable=AsyncMock) as mock_gtm,
            patch("app.agents.marketing.nodes.analyse_brand.tavily_search", new_callable=AsyncMock) as mock_tavily,
            patch("app.agents.marketing.nodes.generate_visual_assets.dalle_generate", new_callable=AsyncMock) as mock_dalle,
            patch("app.agents.marketing.nodes.schedule_posts.typefully_schedule", new_callable=AsyncMock) as mock_typefully,
            patch("app.agents.marketing.nodes.schedule_posts.buffer_schedule", new_callable=AsyncMock) as mock_buffer,
            patch("app.agents.marketing.nodes.schedule_posts.resend_broadcast", new_callable=AsyncMock) as mock_resend,
        ):
            # Configure all mocks
            mock_brand.return_value = ({"brand_voice": "technical", "positioning_statement": "Pos",
                "unique_value_proposition": "UVP", "seo_keyword_targets": [{"keyword": "saas"}],
                "competitor_gaps": ["Gap"], "target_audience_summary": "Devs"}, 100)
            mock_lp.return_value = ({"hero_headline": "Ship Fast", "hero_subheadline": "Sub",
                "hero_cta_text": "Start", "hero_cta_url": "https://shipfast.dev",
                "features_section": [{"title": "Auth", "description": "Pre-wired"}],
                "social_proof_section": "", "pricing_section": [], "faq_section": [],
                "cta_footer_text": "Ship now", "meta_tags": None, "status": "draft"}, 200)
            mock_blogs.return_value = ({"blogs": [{"title": "Blog", "target_keyword": "kw",
                "secondary_keywords": [], "body_markdown": "# Blog\nContent", "meta_description": "Meta",
                "word_count": 300, "status": "draft"}]}, 300)
            mock_ph.return_value = ({"tagline": "Ship fast", "description": "SaaS boilerplate.",
                "first_comment": "Hello PH!", "maker_note": "Built this.",
                "gallery_captions": [], "topics": [], "status": "draft"}, 100)
            mock_social.return_value = ({"x_thread": ["Tweet 1"], "linkedin_post": "LI post",
                "show_hn_post": "HN post", "status": "draft"}, 150)
            mock_email.return_value = ({"onboarding": [{"subject": "Welcome", "preview_text": "Hi",
                "body_html": "<p>Hi</p>", "body_text": "Hi", "send_at_days_offset": 0}],
                "reactivation": [], "status": "draft"}, 200)
            mock_visual.return_value = ({"logo": {"asset_type": "logo", "dall_e_prompt": "Logo prompt",
                "generated_url": None, "status": "pending"}, "og_image": None,
                "social_card": None, "email_banner": None, "total_generated": 0}, 50)
            mock_hall.return_value = ({"critical_count": 0, "warning_count": 0, "passed": True, "findings": []}, 100)
            mock_gtm.return_value = ("# GTM Report\n\nAll content generated.", 200)
            mock_tavily.return_value = {"results": [], "fallback": True}
            mock_dalle.return_value = {"generated_url": None, "status": "failed"}
            mock_typefully.return_value = {"thread_id": "t123", "status": "scheduled", "channel": "x"}
            mock_buffer.return_value = {"post_id": "b456", "status": "scheduled", "channel": "linkedin"}
            mock_resend.return_value = {"email_id": "r789", "status": "sent"}

            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # T1 assertions
        assert final_state["validated"] is True
        assert final_state["hallucination_passed"] is True
        assert final_state["approval_status"] == "approved"
        assert "landing_page" in final_state
        assert final_state["landing_page"]["hero_headline"] == "Ship Fast"
        assert len(final_state.get("seo_blog_drafts", [])) >= 1
        assert final_state["gtm_report_markdown"].startswith("# GTM Report")
        assert not final_state.get("fatal_error")

    @pytest.mark.asyncio
    async def test_graph_fatal_error_on_empty_features(self) -> None:
        """T3: Empty feature_list → graph routes to error_handler immediately."""
        fixture = _load_fixture("shipfast")
        initial = _build_initial_state(fixture)
        initial["feature_list"] = {"features": [], "integrations": [], "pricing_tiers": []}

        with patch("app.agents.marketing.nodes.error_handler.httpx.AsyncClient"):
            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        assert final_state["validated"] is False
        assert final_state["fatal_error"] is not None
        # No generation should have occurred
        assert not final_state.get("landing_page")
        assert not final_state.get("seo_blog_drafts")
