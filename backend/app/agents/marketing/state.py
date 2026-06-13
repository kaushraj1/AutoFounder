"""LangGraph state for the Marketing Agent (AF-044).

MarketerState is the single shared dict flowing through all 13 nodes.
All fields are Optional (total=False) so nodes can run in any order.

Upstream inputs are pre-populated before graph.invoke().
Each node reads what it needs and writes its output back — LangGraph merges.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any

from typing_extensions import TypedDict


class MarketerState(TypedDict, total=False):
    # ------------------------------------------------------------------
    # Inputs (set before graph.invoke)
    # ------------------------------------------------------------------
    run_id: str
    organization_id: str
    parent_run_id: str
    idea_normalised: str
    brand_config: dict[str, Any]  # BrandConfig shape
    feature_list: dict[str, Any]  # FeatureList shape: {features, integrations, pricing_tiers}
    lean_canvas_json: dict[str, Any]
    personas: list[dict[str, Any]]
    live_url: str  # May be "" — ingest_input fills placeholder

    # ------------------------------------------------------------------
    # Node 1 — ingest_input
    # ------------------------------------------------------------------
    validated: bool
    effective_live_url: str  # live_url or "[PENDING_DEPLOY]"
    fatal_error: str | None  # non-None → route to error_handler

    # ------------------------------------------------------------------
    # Node 2 — analyse_brand
    # ------------------------------------------------------------------
    brand_voice: str
    positioning_statement: str
    unique_value_proposition: str
    seo_keyword_targets: list[str]
    competitor_gaps: list[str]
    target_audience_summary: str

    # ------------------------------------------------------------------
    # Node 3 — generate_landing_page  (parallel fan-out)
    # ------------------------------------------------------------------
    landing_page: dict[str, Any]  # LandingPage shape

    # ------------------------------------------------------------------
    # Node 4 — generate_seo_blogs  (parallel fan-out)
    # ------------------------------------------------------------------
    seo_blog_drafts: list[dict[str, Any]]  # list[SEOBlogDraft]

    # ------------------------------------------------------------------
    # Node 5 — generate_product_hunt_kit  (parallel fan-out)
    # ------------------------------------------------------------------
    product_hunt_kit: dict[str, Any]  # ProductHuntKit shape

    # ------------------------------------------------------------------
    # Node 6 — generate_social_posts  (parallel fan-out)
    # ------------------------------------------------------------------
    social_post_bundle: dict[str, Any]  # SocialPostBundle shape

    # ------------------------------------------------------------------
    # Node 7 — generate_email_sequences  (parallel fan-out)
    # ------------------------------------------------------------------
    email_sequences: dict[str, Any]  # EmailSequences shape

    # ------------------------------------------------------------------
    # Node 8 — generate_visual_assets  (parallel fan-out)
    # ------------------------------------------------------------------
    visual_asset_bundle: dict[str, Any]  # VisualAssetBundle shape

    # ------------------------------------------------------------------
    # Node 9 — parallel_join (barrier)
    # ------------------------------------------------------------------
    parallel_complete: bool
    generators_completed: list[str]  # which generator nodes finished
    generators_failed: list[str]  # graceful soft-fail

    # ------------------------------------------------------------------
    # Node 10 — hallucination_check
    # ------------------------------------------------------------------
    hallucination_report: dict[str, Any]  # HallucinationReport shape
    hallucination_passed: bool
    hallucination_retry_count: int

    # ------------------------------------------------------------------
    # Node 11 — launch_control_center (HITL)
    # ------------------------------------------------------------------
    approval_status: str  # "pending" | "approved" | "rejected" | "partial" | "timed_out"
    approved_content_types: list[str]
    rejected_content_types: list[str]

    # ------------------------------------------------------------------
    # Node 12 — schedule_posts
    # ------------------------------------------------------------------
    scheduled_post_ids: dict[str, Any]  # ScheduledPostIds shape

    # ------------------------------------------------------------------
    # Node 13 — render_gtm_report
    # ------------------------------------------------------------------
    gtm_report_markdown: str
    gtm_report_s3_uri: str

    # ------------------------------------------------------------------
    # Cross-cutting metadata
    # ------------------------------------------------------------------
    errors: Annotated[list[str], operator.add]
    llm_tokens_used: Annotated[int, operator.add]
    images_generated: Annotated[int, operator.add]
