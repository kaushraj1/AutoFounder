"""Integration tests — hallucination retry (AF-044, T5, T6)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

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


_CLEAN_HALL = ({"critical_count": 0, "warning_count": 0, "passed": True, "findings": []}, 100)
_FAIL_HALL = ({"critical_count": 1, "warning_count": 0, "passed": False,
               "findings": [{"claim": "Unlimited storage", "source_node": "landing_page",
                             "severity": "CRITICAL", "reason": "Not in feature list", "corrected_claim": ""}]}, 100)

_BRAND = ({"brand_voice": "technical", "positioning_statement": "Pos",
            "unique_value_proposition": "UVP", "seo_keyword_targets": [{"keyword": "saas"}],
            "competitor_gaps": [], "target_audience_summary": "Devs"}, 50)
_LP = ({"hero_headline": "Ship Fast", "hero_subheadline": "Sub",
         "hero_cta_text": "Start", "hero_cta_url": "https://x.com",
         "features_section": [], "social_proof_section": "", "pricing_section": [],
         "faq_section": [], "cta_footer_text": "", "meta_tags": None, "status": "draft"}, 100)
_BLOGS = ({"blogs": [{"title": "B", "target_keyword": "k", "secondary_keywords": [],
                       "body_markdown": "Body", "meta_description": "M", "word_count": 10, "status": "draft"}]}, 100)
_PH = ({"tagline": "Ship fast", "description": "SaaS boilerplate.",
         "first_comment": "Hello PH!", "maker_note": "Built.",
         "gallery_captions": [], "topics": [], "status": "draft"}, 100)
_SOCIAL = ({"x_thread": ["T1"], "linkedin_post": "LI", "show_hn_post": "HN", "status": "draft"}, 50)
_EMAIL = ({"onboarding": [{"subject": "W", "preview_text": "P", "body_html": "<p>H</p>",
                             "body_text": "H", "send_at_days_offset": 0}], "reactivation": [], "status": "draft"}, 100)
_VISUAL = ({"logo": None, "og_image": None, "social_card": None, "email_banner": None, "total_generated": 0}, 30)
_GTM = ("# GTM Report", 100)


class TestHallucinationRetry:
    """T5: Hallucination detected → auto-correct on retry → passes on 2nd attempt."""

    @pytest.mark.asyncio
    async def test_hallucination_fails_then_passes_on_retry(self) -> None:
        """T5: First hallucination check fails; second attempt passes."""
        fixture = _load_fixture("shipfast")
        initial = _build_initial_state(fixture)

        # Hallucination: fail first call, pass second
        hall_side_effects = [_FAIL_HALL, _CLEAN_HALL]
        hall_call_count = 0

        def hall_effect(*args, **kwargs):
            nonlocal hall_call_count
            r = hall_side_effects[min(hall_call_count, len(hall_side_effects) - 1)]
            hall_call_count += 1
            return r

        with (
            patch("app.agents.marketing.nodes.analyse_brand.call_llm", return_value=_BRAND) as _,
            patch("app.agents.marketing.nodes.generate_landing_page.call_llm", return_value=_LP) as _,
            patch("app.agents.marketing.nodes.generate_seo_blogs.call_llm", return_value=_BLOGS) as _,
            patch("app.agents.marketing.nodes.generate_product_hunt_kit.call_llm", return_value=_PH) as _,
            patch("app.agents.marketing.nodes.generate_social_posts.call_llm", return_value=_SOCIAL) as _,
            patch("app.agents.marketing.nodes.generate_email_sequences.call_llm", return_value=_EMAIL) as _,
            patch("app.agents.marketing.nodes.generate_visual_assets.call_llm", return_value=_VISUAL) as _,
            patch("app.agents.marketing.nodes.hallucination_check.call_llm", side_effect=hall_effect),
            patch("app.agents.marketing.nodes.render_gtm_report.call_llm_text", return_value=_GTM) as _,
            patch("app.agents.marketing.nodes.analyse_brand.tavily_search", return_value={"results": []}) as _,
            patch("app.agents.marketing.nodes.generate_visual_assets.dalle_generate", return_value={"generated_url": None, "status": "failed"}) as _,
            patch("app.agents.marketing.nodes.schedule_posts.typefully_schedule", return_value={"thread_id": "t1", "status": "scheduled", "channel": "x"}) as _,
            patch("app.agents.marketing.nodes.schedule_posts.buffer_schedule", return_value={"post_id": "b1", "status": "scheduled", "channel": "linkedin"}) as _,
            patch("app.agents.marketing.nodes.schedule_posts.resend_broadcast", return_value={"email_id": "r1", "status": "sent"}) as _,
        ):
            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # T5: Should have retried and passed
        assert final_state["hallucination_passed"] is True
        assert hall_call_count == 2, f"Expected 2 hallucination checks (got {hall_call_count})"
        assert final_state.get("hallucination_retry_count", 0) >= 1

    @pytest.mark.asyncio
    async def test_exhausted_retries_routes_to_error_handler(self) -> None:
        """T6: 2 retries exhausted → error_handler, Slack alert."""
        fixture = _load_fixture("shipfast")
        initial = _build_initial_state(fixture)

        # Hallucination: always fails
        hall_always_fail = _FAIL_HALL

        with (
            patch("app.agents.marketing.nodes.analyse_brand.call_llm", return_value=_BRAND) as _,
            patch("app.agents.marketing.nodes.generate_landing_page.call_llm", return_value=_LP) as _,
            patch("app.agents.marketing.nodes.generate_seo_blogs.call_llm", return_value=_BLOGS) as _,
            patch("app.agents.marketing.nodes.generate_product_hunt_kit.call_llm", return_value=_PH) as _,
            patch("app.agents.marketing.nodes.generate_social_posts.call_llm", return_value=_SOCIAL) as _,
            patch("app.agents.marketing.nodes.generate_email_sequences.call_llm", return_value=_EMAIL) as _,
            patch("app.agents.marketing.nodes.generate_visual_assets.call_llm", return_value=_VISUAL) as _,
            patch("app.agents.marketing.nodes.hallucination_check.call_llm", return_value=hall_always_fail) as _,
            patch("app.agents.marketing.nodes.analyse_brand.tavily_search", return_value={"results": []}) as _,
            patch("app.agents.marketing.nodes.generate_visual_assets.dalle_generate", return_value={"generated_url": None, "status": "failed"}) as _,
            patch("app.agents.marketing.nodes.error_handler.httpx.AsyncClient") as _,
        ):
            graph = build_marketer_graph()
            final_state = await graph.ainvoke(initial)

        # T6: hallucination_passed should still be False (retries exhausted)
        # The graph ends at error_handler — no scheduling or report
        assert not final_state.get("scheduled_post_ids")
        assert not final_state.get("gtm_report_markdown")
