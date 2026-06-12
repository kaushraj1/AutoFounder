"""Integration tests — tool failure degradation (AF-044, T4, T9)."""

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
        "approval_status": "approved",
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
_SOCIAL = ({"x_thread": ["T1", "T2"], "linkedin_post": "LI post", "show_hn_post": "HN", "status": "draft"}, 60)
_EMAIL = ({"onboarding": [{"subject": "W", "preview_text": "P", "body_html": "<p>H</p>",
                             "body_text": "H", "send_at_days_offset": 0}], "reactivation": [], "status": "draft"}, 80)
_VISUAL_PROMPTS = ({"logo": {"asset_type": "logo", "dall_e_prompt": "Logo prompt", "generated_url": None, "status": "pending"},
                    "og_image": {"asset_type": "og_image", "dall_e_prompt": "OG prompt", "generated_url": None, "status": "pending"},
                    "social_card": {"asset_type": "social_card", "dall_e_prompt": "Social", "generated_url": None, "status": "pending"},
                    "email_banner": {"asset_type": "email_banner", "dall_e_prompt": "Banner", "generated_url": None, "status": "pending"},
                    "total_generated": 0}, 30)
_HALL_PASS = ({"critical_count": 0, "warning_count": 0, "passed": True, "findings": []}, 80)
_GTM = ("# GTM Report\n\nCompleted despite tool failures.", 80)


class TestToolFailureDegradation:
    """T4: DALL-E rate limit → prompt-only degradation.
    T9: Buffer + Typefully both fail → posts stored as draft, non-fatal.
    """

    @pytest.mark.asyncio
    async def test_dalle_failure_degrades_to_prompt_only(self) -> None:
        """T4: DALL-E generates URL=None (failed) but graph continues — non-fatal."""
        fixture = _load_fixture("shipfast")
        initial = _build_initial_state(fixture)

        # DALL-E always returns prompt-only (no URL)
        async def fake_dalle(prompt, *, size="1024x1024", quality="standard", style="vivid", asset_type="unknown"):
            return {"asset_type": asset_type, "dall_e_prompt": prompt, "generated_url": None, "status": "failed"}

        with (
            patch("app.agents.marketing.nodes.analyse_brand.call_llm", return_value=_BRAND),
            patch("app.agents.marketing.nodes.generate_landing_page.call_llm", return_value=_LP),
            patch("app.agents.marketing.nodes.generate_seo_blogs.call_llm", return_value=_BLOGS),
            patch("app.agents.marketing.nodes.generate_product_hunt_kit.call_llm", return_value=_PH),
            patch("app.agents.marketing.nodes.generate_social_posts.call_llm", return_value=_SOCIAL),
            patch("app.agents.marketing.nodes.generate_email_sequences.call_llm", return_value=_EMAIL),
            patch("app.agents.marketing.nodes.generate_visual_assets.call_llm", return_value=_VISUAL_PROMPTS),
            patch("app.agents.marketing.nodes.hallucination_check.call_llm", return_value=_HALL_PASS),
            patch("app.agents.marketing.nodes.render_gtm_report.call_llm_text", return_value=_GTM),
            patch("app.agents.marketing.nodes.analyse_brand.tavily_search", return_value={"results": []}),
            patch("app.agents.marketing.nodes.generate_visual_assets.dalle_generate", side_effect=fake_dalle),
            patch("app.agents.marketing.nodes.schedule_posts.typefully_schedule",
                  return_value={"thread_id": "t1", "status": "scheduled", "channel": "x"}),
            patch("app.agents.marketing.nodes.schedule_posts.buffer_schedule",
                  return_value={"post_id": "b1", "status": "scheduled", "channel": "linkedin"}),
            patch("app.agents.marketing.nodes.schedule_posts.resend_broadcast",
                  return_value={"email_id": "r1", "status": "sent"}),
        ):
            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # T4: Graph should complete successfully despite DALL-E failure
        assert final_state["validated"] is True
        assert final_state["hallucination_passed"] is True
        assert final_state["approval_status"] == "approved"

        # Visual assets should have prompts but no generated URLs
        visual = final_state.get("visual_asset_bundle", {})
        assert visual.get("total_generated", 0) == 0  # No images actually generated
        logo = visual.get("logo")
        if logo:
            assert logo.get("generated_url") is None
            assert logo.get("dall_e_prompt")  # Prompt should still be present

        # GTM report generated
        assert "# GTM Report" in final_state.get("gtm_report_markdown", "")

    @pytest.mark.asyncio
    async def test_buffer_and_typefully_both_fail_gracefully(self) -> None:
        """T9: Buffer + Typefully both fail → posts stored as draft, non-fatal."""
        fixture = _load_fixture("petconnect")
        initial = _build_initial_state(fixture)

        # Both scheduling services fail
        async def fake_typefully_fail(*args, **kwargs):
            raise RuntimeError("Typefully API is down")

        async def fake_buffer_fail(*args, **kwargs):
            raise RuntimeError("Buffer API is down")

        with (
            patch("app.agents.marketing.nodes.analyse_brand.call_llm", return_value=_BRAND),
            patch("app.agents.marketing.nodes.generate_landing_page.call_llm", return_value=_LP),
            patch("app.agents.marketing.nodes.generate_seo_blogs.call_llm", return_value=_BLOGS),
            patch("app.agents.marketing.nodes.generate_product_hunt_kit.call_llm", return_value=_PH),
            patch("app.agents.marketing.nodes.generate_social_posts.call_llm", return_value=_SOCIAL),
            patch("app.agents.marketing.nodes.generate_email_sequences.call_llm", return_value=_EMAIL),
            patch("app.agents.marketing.nodes.generate_visual_assets.call_llm", return_value=_VISUAL_PROMPTS),
            patch("app.agents.marketing.nodes.hallucination_check.call_llm", return_value=_HALL_PASS),
            patch("app.agents.marketing.nodes.render_gtm_report.call_llm_text", return_value=_GTM),
            patch("app.agents.marketing.nodes.analyse_brand.tavily_search", return_value={"results": []}),
            patch("app.agents.marketing.nodes.generate_visual_assets.dalle_generate",
                  return_value={"generated_url": None, "status": "failed"}),
            # Both scheduling tools fail at the SDK level
            patch("app.agents.marketing.tools.typefully_schedule.httpx.AsyncClient") as mock_typ,
            patch("app.agents.marketing.tools.buffer_schedule.httpx.AsyncClient") as mock_buf,
            patch("app.agents.marketing.nodes.schedule_posts.resend_broadcast",
                  return_value={"email_id": "r1", "status": "sent"}),
        ):
            # Make HTTP calls fail
            mock_typ.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=RuntimeError("Connection refused")
            )
            mock_buf.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=RuntimeError("Connection refused")
            )

            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # T9: Graph should complete (scheduling failure is non-fatal)
        assert final_state["validated"] is True
        assert final_state["hallucination_passed"] is True
        # GTM report should still be generated
        assert "# GTM Report" in final_state.get("gtm_report_markdown", "")

    @pytest.mark.asyncio
    async def test_tavily_failure_falls_back_to_llm_knowledge(self) -> None:
        """Tavily failure → brand analysis uses LLM knowledge only (non-fatal)."""
        fixture = _load_fixture("devpulse")
        initial = _build_initial_state(fixture)

        with (
            patch("app.agents.marketing.nodes.analyse_brand.call_llm", return_value=_BRAND),
            patch("app.agents.marketing.nodes.generate_landing_page.call_llm", return_value=_LP),
            patch("app.agents.marketing.nodes.generate_seo_blogs.call_llm", return_value=_BLOGS),
            patch("app.agents.marketing.nodes.generate_product_hunt_kit.call_llm", return_value=_PH),
            patch("app.agents.marketing.nodes.generate_social_posts.call_llm", return_value=_SOCIAL),
            patch("app.agents.marketing.nodes.generate_email_sequences.call_llm", return_value=_EMAIL),
            patch("app.agents.marketing.nodes.generate_visual_assets.call_llm", return_value=_VISUAL_PROMPTS),
            patch("app.agents.marketing.nodes.hallucination_check.call_llm", return_value=_HALL_PASS),
            patch("app.agents.marketing.nodes.render_gtm_report.call_llm_text", return_value=_GTM),
            # Tavily returns fallback (no API key configured)
            patch("app.agents.marketing.nodes.analyse_brand.tavily_search",
                  return_value={"results": [], "fallback": True}),
            patch("app.agents.marketing.nodes.generate_visual_assets.dalle_generate",
                  return_value={"generated_url": None, "status": "failed"}),
            patch("app.agents.marketing.nodes.schedule_posts.typefully_schedule",
                  return_value={"thread_id": "t1", "status": "scheduled", "channel": "x"}),
            patch("app.agents.marketing.nodes.schedule_posts.buffer_schedule",
                  return_value={"post_id": "b1", "status": "scheduled", "channel": "linkedin"}),
            patch("app.agents.marketing.nodes.schedule_posts.resend_broadcast",
                  return_value={"email_id": "r1", "status": "sent"}),
        ):
            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # Should complete successfully even without Tavily
        assert final_state["validated"] is True
        assert final_state["brand_voice"] == "tech"
        assert "# GTM Report" in final_state.get("gtm_report_markdown", "")
