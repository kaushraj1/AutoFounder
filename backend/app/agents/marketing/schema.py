"""Marketing Agent — Pillar 6 data models (AF-044).

All Pydantic models consumed/produced by the MarketingAgent StateGraph.

Key contract:
  - MarketerInput  — what upstream pillars hand in
  - MarketerOutput — what is handed to LLMOps (Pillar 7) and the Founder Portal
  - FeatureList    — imported directly from Architect (no translation layer)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# Re-export FeatureList from Architect so downstream can import from one place.
from app.agents.architect.schema import FeatureList  # noqa: F401

# ---------------------------------------------------------------------------
# Brand Config (input from Founder / brand setup)
# ---------------------------------------------------------------------------


class BrandConfig(BaseModel):
    """Founder-supplied brand parameters."""

    product_name: str
    tagline: str = ""
    logo_concept: str = ""
    primary_color: str = ""
    tone: str = "professional"  # professional | technical | inspirational | casual
    target_audience: str = ""
    website_url: str = ""


# ---------------------------------------------------------------------------
# MarketerInput — what triggers the agent
# ---------------------------------------------------------------------------


class MarketerInput(BaseModel):
    """Input handed to MarketingAgent.run().

    Sourced from:
      - Pillar 1 (StrategyAgent): idea_normalised, lean_canvas_json, personas
      - Pillar 2 (ArchitectAgent): feature_list
      - Pillar 5 (DevOpsAgent):   live_url
      - Founder setup:            brand_config, organization_id
    """

    run_id: UUID
    organization_id: str
    idea_normalised: str
    brand_config: BrandConfig
    feature_list: FeatureList  # FATAL if empty — enforced by FeatureList validator
    lean_canvas_json: dict[str, Any] = Field(default_factory=dict)
    personas: list[dict[str, Any]] = Field(default_factory=list)
    live_url: str = ""  # May be empty — fallback to placeholder
    parent_run_id: str = ""
    approval_status: str = "pending"  # "pending" | "approved" | "rejected"


# ---------------------------------------------------------------------------
# Brand Analysis (Node 2 output)
# ---------------------------------------------------------------------------


class BrandVoiceSummary(BaseModel):
    """Synthesised brand voice produced by analyse_brand node."""

    brand_voice: str  # e.g. "conversational, developer-focused, data-backed"
    positioning_statement: str
    unique_value_proposition: str
    seo_keyword_targets: list[str] = Field(default_factory=list)
    competitor_gaps: list[str] = Field(default_factory=list)
    target_audience_summary: str = ""


# ---------------------------------------------------------------------------
# Landing Page (Node 3)
# ---------------------------------------------------------------------------


class LandingPageMeta(BaseModel):
    title_tag: str
    meta_description: str
    og_title: str = ""
    og_description: str = ""


class LandingPage(BaseModel):
    hero_headline: str
    hero_subheadline: str
    hero_cta_text: str
    hero_cta_url: str
    features_section: list[dict[str, str]] = Field(
        default_factory=list
    )  # [{title, description}]
    social_proof_section: str = ""
    pricing_section: list[dict[str, Any]] = Field(default_factory=list)
    faq_section: list[dict[str, str]] = Field(default_factory=list)
    cta_footer_text: str = ""
    meta_tags: LandingPageMeta | None = None
    status: str = "draft"


# ---------------------------------------------------------------------------
# SEO Blog Draft (Node 4)
# ---------------------------------------------------------------------------


class SEOBlogDraft(BaseModel):
    title: str
    target_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)
    body_markdown: str
    meta_description: str
    word_count: int = 0
    status: str = "draft"


# ---------------------------------------------------------------------------
# Product Hunt Kit (Node 5)
# ---------------------------------------------------------------------------


class ProductHuntKit(BaseModel):
    tagline: str  # max 60 chars
    description: str  # max 260 chars
    first_comment: str  # maker's first comment (max 1,000 chars)
    maker_note: str  # personal note from maker (max 500 chars)
    gallery_captions: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    status: str = "draft"

    @field_validator("tagline")
    @classmethod
    def tagline_length(cls, v: str) -> str:
        if len(v) > 60:
            raise ValueError(f"Product Hunt tagline must be ≤60 chars (got {len(v)})")
        return v

    @field_validator("description")
    @classmethod
    def description_length(cls, v: str) -> str:
        if len(v) > 260:
            raise ValueError(f"Product Hunt description must be ≤260 chars (got {len(v)})")
        return v


# ---------------------------------------------------------------------------
# Social Posts (Node 6)
# ---------------------------------------------------------------------------


class SocialPost(BaseModel):
    channel: str  # "x" | "linkedin" | "hn"
    content: str
    hashtags: list[str] = Field(default_factory=list)
    scheduled_at: datetime | None = None
    status: str = "draft"


class SocialPostBundle(BaseModel):
    x_thread: list[str] = Field(default_factory=list)  # 4-6 tweet texts
    linkedin_post: str = ""
    show_hn_post: str = ""
    status: str = "draft"


# ---------------------------------------------------------------------------
# Email Sequences (Node 7)
# ---------------------------------------------------------------------------


class EmailMessage(BaseModel):
    subject: str
    preview_text: str
    body_html: str
    body_text: str
    send_at_days_offset: int  # days after signup: 0, 1, 3, 7, 14


class EmailSequences(BaseModel):
    onboarding: list[EmailMessage] = Field(
        default_factory=list
    )  # Day 0, 1, 3, 7, 14
    reactivation: list[EmailMessage] = Field(default_factory=list)  # 3 emails
    status: str = "draft"


# ---------------------------------------------------------------------------
# Visual Assets (Node 8)
# ---------------------------------------------------------------------------


class VisualAsset(BaseModel):
    asset_type: str  # "logo" | "og_image" | "social_card" | "email_banner"
    dall_e_prompt: str
    generated_url: str | None = None  # None if DALL-E unavailable (non-fatal)
    s3_uri: str | None = None
    status: str = "pending"  # "pending" | "generated" | "failed"


class VisualAssetBundle(BaseModel):
    logo: VisualAsset | None = None
    og_image: VisualAsset | None = None
    social_card: VisualAsset | None = None
    email_banner: VisualAsset | None = None
    total_generated: int = 0


# ---------------------------------------------------------------------------
# Hallucination Report (Node 10)
# ---------------------------------------------------------------------------


class HallucinationFinding(BaseModel):
    claim: str
    source_node: str  # which generator node produced the claim
    severity: str  # "CRITICAL" | "WARNING"
    reason: str
    corrected_claim: str = ""


class HallucinationReport(BaseModel):
    """Cross-reference result of all generated copy vs FeatureList."""

    critical_count: int = 0
    warning_count: int = 0
    passed: bool = False
    retry_count: int = 0
    findings: list[HallucinationFinding] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Scheduled Post IDs (Node 12)
# ---------------------------------------------------------------------------


class ScheduledPostIds(BaseModel):
    """IDs returned by Buffer / Typefully / Resend after scheduling."""

    x_thread_id: str | None = None
    linkedin_post_id: str | None = None
    email_campaign_id: str | None = None
    # Product Hunt is always manual
    product_hunt_status: str = "manual"  # reminder set; no API scheduling
    channel_statuses: dict[str, str] = Field(
        default_factory=dict
    )  # {"x": "scheduled", "linkedin": "draft", ...}


# ---------------------------------------------------------------------------
# MarketerOutput — emitted to LLMOps + Founder Portal
# ---------------------------------------------------------------------------


class MarketerOutput(BaseModel):
    """Full output of the Marketing Agent — handed to LLMOps (Pillar 7) and stored in UDAL.

    Also surfaced to the Founder Portal (Raunak AF-059) and Mobile Gate (Yogesh AF-068).
    """

    run_id: UUID
    parent_run_id: str = ""
    organization_id: str
    product_name: str
    live_url: str

    # Content
    landing_page: LandingPage | None = None
    seo_blog_drafts: list[SEOBlogDraft] = Field(default_factory=list)
    product_hunt_kit: ProductHuntKit | None = None
    social_post_bundle: SocialPostBundle | None = None
    email_sequences: EmailSequences | None = None
    visual_asset_bundle: VisualAssetBundle | None = None

    # Quality
    hallucination_report: HallucinationReport | None = None
    hallucination_critical_count: int = 0
    hallucination_warning_count: int = 0

    # HITL
    approval_status: str = "pending"  # "approved" | "rejected" | "partial" | "timed_out"
    approved_content_types: list[str] = Field(default_factory=list)
    rejected_content_types: list[str] = Field(default_factory=list)

    # Scheduling
    scheduled_post_ids: ScheduledPostIds | None = None

    # Artifact storage
    gtm_report_markdown: str = ""
    gtm_report_s3_uri: str = ""

    # Telemetry
    total_llm_tokens_used: int = 0
    total_images_generated: int = 0
    errors: list[str] = Field(default_factory=list)

    # Phase 2: protobuf + gRPC handoff to LLMOps
    # NOTE: marketer_output.proto compilation deferred to Phase 2 (when AF-049 LLMOps lands).
