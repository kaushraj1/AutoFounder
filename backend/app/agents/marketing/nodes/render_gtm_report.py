"""Node 13 — render_gtm_report (AF-044).

Assembles the final GTM (Go-To-Market) launch report in Markdown and
hands off a machine-readable JSON summary to LLMOps (Pillar 7).

Reads:  all generated content + hallucination_report + scheduled_post_ids
Writes: gtm_report_markdown, gtm_report_s3_uri
"""

from __future__ import annotations

import json
import logging

from app.agents.marketing.llm import call_llm_text
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)


async def render_gtm_report(state: MarketerState) -> MarketerState:
    """LangGraph node: compile Markdown GTM report + LLMOps handoff JSON."""
    logger.info("[marketing] render_gtm_report — start")

    errors: list[str] = list(state.get("errors", []))
    hall_report = state.get("hallucination_report", {})

    prompt = render(
        "render_gtm_report",
        run_id=state.get("run_id", ""),
        organization_id=state.get("organization_id", ""),
        brand_config=state.get("brand_config", {}),
        live_url=state.get("effective_live_url", ""),
        brand_voice=state.get("brand_voice", ""),
        positioning_statement=state.get("positioning_statement", ""),
        unique_value_proposition=state.get("unique_value_proposition", ""),
        seo_keyword_targets=state.get("seo_keyword_targets", []),
        approval_status=state.get("approval_status", ""),
        approved_content_types=state.get("approved_content_types", []),
        rejected_content_types=state.get("rejected_content_types", []),
        hallucination_critical_count=hall_report.get("critical_count", 0),
        hallucination_warning_count=hall_report.get("warning_count", 0),
        hallucination_passed=hall_report.get("passed", True),
        scheduled_post_ids=state.get("scheduled_post_ids", {}),
        total_llm_tokens_used=state.get("llm_tokens_used", 0),
        total_images_generated=state.get("images_generated", 0),
    )

    try:
        report_markdown, tokens = await call_llm_text(prompt, temperature=0.2)
    except Exception as exc:
        err = f"render_gtm_report: LLM failed: {exc}"
        logger.error("[marketing] %s", err)
        report_markdown = _fallback_report(state)
        tokens = 0
        errors.append(err)

    # ---- S3 URI (stub for Phase 2 — real upload wired when UDAL is connected) ----
    run_id = state.get("run_id", "unknown")
    org_id = state.get("organization_id", "unknown")
    s3_uri = f"s3://autofounder-ai-artifacts-dev/{org_id}/{run_id}/gtm_report.md"
    logger.info("[marketing] render_gtm_report — s3_uri stub: %s", s3_uri)

    logger.info("[marketing] render_gtm_report — done, tokens=%d", tokens)

    return {
        **state,
        "gtm_report_markdown": report_markdown,
        "gtm_report_s3_uri": s3_uri,
        "errors": errors,
        "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
    }


def _fallback_report(state: MarketerState) -> str:
    """Minimal fallback GTM report when LLM fails."""
    brand = state.get("brand_config", {})
    approved = state.get("approved_content_types", [])
    return (
        f"# GTM Launch Report — {brand.get('product_name', 'Product')}\n\n"
        f"**Run ID:** {state.get('run_id', 'N/A')}\n"
        f"**Approval Status:** {state.get('approval_status', 'N/A')}\n"
        f"**Approved Content:** {', '.join(approved) or 'none'}\n\n"
        f"*Full report generation failed — see errors log.*\n"
    )
