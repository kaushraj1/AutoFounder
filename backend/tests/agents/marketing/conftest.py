"""Test fixtures and fakes for Marketing Agent tests (AF-044).

Provides:
  - MarketingFakeLLMRouter  — pre-built JSON responses per task type
  - MarketingFakeToolRegistry — mock tool calls (no real HTTP)
  - mock_udal — dummy UDAL object
  - shipfast_input — MarketerInput from shipfast fixture
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from app.agents.marketing.schema import BrandConfig, FeatureList, MarketerInput

_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "mock_products"


# ---------------------------------------------------------------------------
# Fake LLM Router — returns structured JSON per prompt task
# ---------------------------------------------------------------------------


class MarketingFakeLLMRouter:
    """Fake LLM Router for Marketing Agent tests.

    Returns pre-built JSON responses that match each prompt template's
    expected output schema. Configure `fail_on` to simulate LLM failures.
    """

    def __init__(self) -> None:
        self.called_prompts: list[str] = []
        self.fail_on: str | None = None  # e.g. "analyse_brand" to fail that prompt
        self.hallucination_critical_count: int = 0  # set > 0 to trigger retry
        self._hallucination_call_count: int = 0

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.called_prompts.append(prompt[:100])

        if self.fail_on and self.fail_on in prompt:
            raise RuntimeError(f"FakeLLM: simulated failure for '{self.fail_on}'")

        return self._response_for(prompt)

    def _response_for(self, prompt: str) -> str:
        # Detect which template is being rendered by checking key phrases
        if "brand voice" in prompt.lower() and "positioning statement" in prompt.lower():
            return self._analyse_brand_response()
        elif "hero_headline" in prompt or "landing page" in prompt.lower():
            return self._landing_page_response()
        elif "seo blog" in prompt.lower() or "blog drafts" in prompt.lower():
            return self._seo_blogs_response()
        elif "product hunt" in prompt.lower() or "tagline" in prompt.lower() and "≤60" in prompt:
            return self._product_hunt_response()
        elif "x_thread" in prompt or "x thread" in prompt.lower():
            return self._social_posts_response()
        elif "onboarding" in prompt.lower() and "reactivation" in prompt.lower():
            return self._email_sequences_response()
        elif "dall-e" in prompt.lower() or "dall_e_prompt" in prompt:
            return self._visual_assets_response()
        elif "hallucination" in prompt.lower() or "fact-checker" in prompt.lower():
            return self._hallucination_response()
        elif "gtm" in prompt.lower() or "go-to-market" in prompt.lower():
            return "# GTM Launch Report\n\n## Executive Summary\n- Content generated successfully."
        return json.dumps({"result": "ok"})

    def _analyse_brand_response(self) -> str:
        return json.dumps(
            {
                "brand_voice": "technical, direct, developer-first",
                "positioning_statement": "For indie hackers who want to ship fast, ShipFast is the only SaaS boilerplate that pre-wires auth, payments, and email so you can launch in a weekend.",
                "unique_value_proposition": "Ship a production-ready SaaS in a weekend, not months.",
                "seo_keyword_targets": [
                    {
                        "keyword": "nextjs saas boilerplate",
                        "intent": "commercial",
                        "notes": "high volume",
                    },
                    {
                        "keyword": "ship saas fast",
                        "intent": "informational",
                        "notes": "growing trend",
                    },
                    {"keyword": "saas starter kit", "intent": "commercial", "notes": "head term"},
                ],
                "competitor_gaps": [
                    "Most boilerplates don't include billing out of the box",
                    "No alternatives ship with a landing page template",
                ],
                "target_audience_summary": "Indie hackers and solo founders who want to validate and launch SaaS products quickly without spending weeks on infrastructure.",
            }
        )

    def _landing_page_response(self) -> str:
        return json.dumps(
            {
                "hero_headline": "Ship Your SaaS in a Weekend",
                "hero_subheadline": "The Next.js boilerplate with auth, payments, and email pre-wired.",
                "hero_cta_text": "Get ShipFast →",
                "hero_cta_url": "https://shipfast.dev",
                "features_section": [
                    {
                        "title": "Auth in 5 minutes",
                        "description": "Magic link and Google OAuth pre-configured with Supabase.",
                    },
                    {
                        "title": "Stripe billing",
                        "description": "Monthly and annual subscription plans, ready to go.",
                    },
                    {
                        "title": "Email with Resend",
                        "description": "Transactional emails pre-wired and tested.",
                    },
                ],
                "social_proof_section": "Join 2,000+ indie hackers who shipped with ShipFast. [PLACEHOLDER]",
                "pricing_section": [
                    {
                        "tier_name": "Starter",
                        "price": "$149",
                        "description": "One-time purchase, lifetime updates",
                        "cta": "Buy Now",
                    },
                    {
                        "tier_name": "All-Access",
                        "price": "$299",
                        "description": "All templates + future additions",
                        "cta": "Get All-Access",
                    },
                ],
                "faq_section": [
                    {
                        "question": "What stack does ShipFast use?",
                        "answer": "Next.js 14 App Router, Supabase, Stripe, and Resend.",
                    },
                    {
                        "question": "Is this a one-time purchase?",
                        "answer": "Yes — one-time fee, lifetime updates.",
                    },
                ],
                "cta_footer_text": "Ready to ship? Get ShipFast today.",
                "meta_tags": {
                    "title_tag": "ShipFast — Next.js SaaS Boilerplate",
                    "meta_description": "Ship your SaaS in a weekend with ShipFast. Pre-wired auth, payments, and email. One-time purchase.",
                    "og_title": "ShipFast — Ship a SaaS in a Weekend",
                    "og_description": "Next.js boilerplate with Supabase, Stripe, and Resend pre-configured.",
                },
                "status": "draft",
            }
        )

    def _seo_blogs_response(self) -> str:
        return json.dumps(
            {
                "blogs": [
                    {
                        "title": "Why Indie Hackers Spend 3 Weeks on Setup (And How to Fix It)",
                        "target_keyword": "nextjs saas boilerplate",
                        "secondary_keywords": ["ship saas fast", "saas starter"],
                        "body_markdown": "## The Setup Tax\n\nEvery SaaS founder knows it. You have an idea, you open VS Code, and then... weeks go by before you write a single line of product code.\n\nThis is the setup tax. Auth, payments, email, database — each one a rabbit hole. ShipFast eliminates this.\n\n## What ShipFast Includes\n\n- **Auth**: Supabase magic link and Google OAuth pre-configured\n- **Stripe billing**: Monthly and annual plans out of the box\n- **Email**: Resend for transactional emails\n- **UI**: Tailwind CSS + shadcn/ui components\n\n## How to Ship in a Weekend\n\n1. Clone ShipFast\n2. Configure your `.env`\n3. Deploy to Vercel\n4. Launch\n\nStart at [shipfast.dev](https://shipfast.dev).",
                        "meta_description": "Discover how ShipFast's Next.js boilerplate eliminates weeks of setup with pre-wired auth, payments, and email.",
                        "word_count": 350,
                        "status": "draft",
                    }
                ]
            }
        )

    def _product_hunt_response(self) -> str:
        return json.dumps(
            {
                "tagline": "Ship your SaaS in a weekend, not months",
                "description": "ShipFast is a Next.js boilerplate with auth, Stripe billing, and Resend email pre-wired. Skip the setup, launch your idea.",
                "first_comment": "Hey Product Hunt! 👋\n\nI built ShipFast because I was tired of spending 3 weeks on setup before writing a line of product code.\n\nShipFast ships with:\n✅ Supabase auth (magic link + Google)\n✅ Stripe subscriptions\n✅ Resend transactional email\n\nTry it at https://shipfast.dev",
                "maker_note": "Built this to scratch my own itch — now 2,000+ indie hackers use it. Would love your feedback!",
                "gallery_captions": [
                    "Auth in 5 minutes",
                    "Stripe billing pre-wired",
                    "Deploy to Vercel instantly",
                    "Full Next.js 14 App Router",
                ],
                "topics": ["Developer Tools", "SaaS", "Productivity", "Boilerplate"],
                "status": "draft",
            }
        )

    def _social_posts_response(self) -> str:
        return json.dumps(
            {
                "x_thread": [
                    "🚀 Announcing ShipFast — ship your SaaS in a weekend, not months.",
                    "The problem: Every indie hacker spends 3 weeks on auth, payments, and email. That's 3 weeks not building your actual product.",
                    "ShipFast ships with:\n✅ Supabase auth\n✅ Stripe billing\n✅ Resend email\n✅ Tailwind + shadcn/ui",
                    "One-time purchase. Lifetime updates. Get started at https://shipfast.dev 👇",
                ],
                "linkedin_post": "Excited to launch ShipFast! 🚀\n\nAfter watching indie hackers spend weeks on boilerplate setup, I built the solution: a Next.js SaaS boilerplate with everything pre-wired.\n\n✅ Auth: Supabase magic link + Google OAuth\n✅ Billing: Stripe subscriptions\n✅ Email: Resend\n\nShip your idea this weekend: https://shipfast.dev",
                "show_hn_post": "Show HN: ShipFast – Next.js SaaS boilerplate with auth, Stripe, and Resend pre-wired\n\nI built ShipFast after noticing most indie hackers spend 2-3 weeks on infrastructure before writing product code. The goal was to eliminate the setup tax entirely.\n\nThe stack: Next.js 14 App Router, Supabase (auth + database), Stripe (subscriptions), Resend (email), Tailwind CSS + shadcn/ui.\n\nLimitations: it's opinionated — if you want a different stack, this won't help.\n\nhttps://shipfast.dev — any feedback welcome.",
                "status": "draft",
            }
        )

    def _email_sequences_response(self) -> str:
        return json.dumps(
            {
                "onboarding": [
                    {
                        "subject": "Welcome to ShipFast 🚀",
                        "preview_text": "Your boilerplate is ready. Let's ship.",
                        "body_html": "<p>Hi there!</p><p>Welcome to <strong>ShipFast</strong>. Your boilerplate is ready to clone.</p><p><a href='https://shipfast.dev/docs'>Read the quick-start guide →</a></p>",
                        "body_text": "Hi there!\n\nWelcome to ShipFast. Your boilerplate is ready to clone.\n\nRead the quick-start guide: https://shipfast.dev/docs",
                        "send_at_days_offset": 0,
                    },
                    {
                        "subject": "Your first feature: Auth in 5 min",
                        "preview_text": "Supabase auth is already wired in.",
                        "body_html": "<p>Day 1 tip: Your auth is pre-configured. Add your Supabase keys and you're done.</p>",
                        "body_text": "Day 1 tip: Your auth is pre-configured. Add your Supabase keys and you're done.",
                        "send_at_days_offset": 1,
                    },
                ],
                "reactivation": [
                    {
                        "subject": "Still haven't shipped? Let's fix that",
                        "preview_text": "Your ShipFast licence is waiting for you.",
                        "body_html": "<p>Hey! You haven't launched yet — what's holding you back?</p><p><a href='https://shipfast.dev'>Get back on track →</a></p>",
                        "body_text": "Hey! You haven't launched yet — what's holding you back?\n\nhttps://shipfast.dev",
                        "send_at_days_offset": 30,
                    }
                ],
                "status": "draft",
            }
        )

    def _visual_assets_response(self) -> str:
        return json.dumps(
            {
                "logo": {
                    "asset_type": "logo",
                    "dall_e_prompt": "Minimalist vector logo for a developer tool called ShipFast. A stylised rocket in orange (#FF6B35) with clean lines against a white background. Flat design, no text, no typography. Modern, professional, suitable for both light and dark backgrounds. Square format.",
                    "generated_url": None,
                    "status": "pending",
                },
                "og_image": {
                    "asset_type": "og_image",
                    "dall_e_prompt": "Abstract OG image 1200x630 for ShipFast. Left side: space for text overlay (gradient from dark navy to transparent). Right side: stylised rocket launch with orange and purple accents. Modern SaaS aesthetic, no text, no typography. Professional, clean.",
                    "generated_url": None,
                    "status": "pending",
                },
                "social_card": {
                    "asset_type": "social_card",
                    "dall_e_prompt": "Square 1080x1080 social media card for ShipFast. Bold geometric design with orange (#FF6B35) as primary colour. Abstract rocket motif. Dark background (#1A1A2E). Modern, eye-catching, suitable for Twitter/LinkedIn announcement. No text.",
                    "generated_url": None,
                    "status": "pending",
                },
                "email_banner": {
                    "asset_type": "email_banner",
                    "dall_e_prompt": "Wide email banner 600x200 for ShipFast. Horizontal gradient from dark navy to vibrant orange. Abstract geometric shapes suggesting speed and motion. Clean, professional SaaS aesthetic. No text, no typography.",
                    "generated_url": None,
                    "status": "pending",
                },
                "total_generated": 0,
            }
        )

    def _hallucination_response(self) -> str:
        critical = self.hallucination_critical_count
        # After first call with criticals, reset to 0 for retry simulation
        if self._hallucination_call_count == 0 and critical > 0:
            self._hallucination_call_count += 1
            findings = [
                {
                    "claim": "Supports unlimited projects",
                    "source_node": "landing_page",
                    "severity": "CRITICAL",
                    "reason": "feature_list does not mention unlimited projects",
                    "corrected_claim": "Supports up to 10 projects on Pro plan",
                }
            ]
        else:
            critical = 0
            findings = []
            self._hallucination_call_count += 1

        return json.dumps(
            {
                "critical_count": critical,
                "warning_count": 0,
                "passed": critical == 0,
                "findings": findings,
            }
        )


# ---------------------------------------------------------------------------
# Fake Tool Registry
# ---------------------------------------------------------------------------


class MarketingFakeToolRegistry:
    """Fake tool registry returning mock responses for all marketing tools."""

    def __init__(self) -> None:
        self.called_tools: list[tuple[str, dict]] = []
        self.should_fail: bool = False
        self.fail_tool: str | None = None

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        self.called_tools.append((tool_name, args))
        if self.should_fail and (self.fail_tool is None or self.fail_tool == tool_name):
            raise RuntimeError(f"FakeTool: simulated failure for '{tool_name}'")

        if tool_name == "tavily_search":
            return {
                "results": [
                    {
                        "title": "Competitor",
                        "url": "https://example.com",
                        "content": "Sample content",
                    }
                ]
            }
        elif tool_name == "ahrefs_keywords":
            return [{"keyword": "saas boilerplate", "monthly_volume": 5400, "difficulty": 42}]
        elif tool_name == "dalle_generate":
            return {"generated_url": None, "status": "failed", "asset_type": "logo"}
        elif tool_name == "buffer_schedule":
            return {"post_id": "buf_123", "status": "scheduled", "channel": "linkedin"}
        elif tool_name == "typefully_schedule":
            return {"thread_id": "typ_456", "status": "scheduled", "channel": "x"}
        elif tool_name == "resend_broadcast":
            return {"email_id": "res_789", "status": "sent"}
        return {}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_llm() -> MarketingFakeLLMRouter:
    return MarketingFakeLLMRouter()


@pytest.fixture
def fake_tools() -> MarketingFakeToolRegistry:
    return MarketingFakeToolRegistry()


@pytest.fixture
def mock_udal() -> Any:
    class DummyUDAL:
        organization_id = "org-test"

    return DummyUDAL()


@pytest.fixture
def shipfast_fixture() -> dict[str, Any]:
    with open(_FIXTURES_DIR / "shipfast.json") as f:
        return json.load(f)


@pytest.fixture
def shipfast_input(shipfast_fixture: dict[str, Any]) -> MarketerInput:
    """MarketerInput built from the shipfast fixture."""
    data = shipfast_fixture
    return MarketerInput(
        run_id=UUID(data["run_id"]),
        organization_id=data["organization_id"],
        idea_normalised=data["idea_normalised"],
        brand_config=BrandConfig(**data["brand_config"]),
        feature_list=FeatureList(**data["feature_list"]),
        lean_canvas_json=data.get("lean_canvas_json", {}),
        personas=data.get("personas", []),
        live_url=data.get("live_url", ""),
        approval_status=data.get("approval_status", "approved"),
    )


@pytest.fixture
def base_state(shipfast_fixture: dict[str, Any]) -> dict[str, Any]:
    """Minimal MarketerState for graph testing."""
    data = shipfast_fixture
    return {
        "run_id": data["run_id"],
        "organization_id": data["organization_id"],
        "idea_normalised": data["idea_normalised"],
        "brand_config": data["brand_config"],
        "feature_list": data["feature_list"],
        "lean_canvas_json": data.get("lean_canvas_json", {}),
        "personas": data.get("personas", []),
        "live_url": data.get("live_url", ""),
        "approval_status": data.get("approval_status", "approved"),
        "errors": [],
        "llm_tokens_used": 0,
        "images_generated": 0,
    }
