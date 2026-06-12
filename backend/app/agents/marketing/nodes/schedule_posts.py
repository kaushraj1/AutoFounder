"""Node 12 — schedule_posts (AF-044).

Pushes approved content to Buffer (LinkedIn), Typefully (X), and Resend (email).
Product Hunt is always manual — outputs a reminder note.
Non-fatal: scheduling failures mark content as "draft".

Reads:  approved_content_types, social_post_bundle, email_sequences
Writes: scheduled_post_ids
"""

from __future__ import annotations

import logging

from app.agents.marketing.state import MarketerState
from app.agents.marketing.tools.buffer_schedule import buffer_schedule
from app.agents.marketing.tools.resend_broadcast import resend_broadcast
from app.agents.marketing.tools.typefully_schedule import typefully_schedule

logger = logging.getLogger(__name__)


async def schedule_posts(state: MarketerState) -> MarketerState:
    """LangGraph node: push approved content to scheduling platforms."""
    logger.info("[marketing] schedule_posts — start")

    approved = set(state.get("approved_content_types") or [])
    errors: list[str] = list(state.get("errors", []))
    scheduled: dict = {}

    # ---- X thread via Typefully ----
    if "social_posts" in approved:
        social = state.get("social_post_bundle", {})
        x_thread = social.get("x_thread", [])
        if x_thread:
            result = await typefully_schedule(x_thread)
            scheduled["x"] = result
            logger.info("[marketing] schedule_posts — X thread: status=%s", result.get("status"))
        else:
            logger.warning("[marketing] schedule_posts — no X thread to schedule")

    # ---- LinkedIn via Buffer ----
    if "social_posts" in approved:
        social = state.get("social_post_bundle", {})
        linkedin_post = social.get("linkedin_post", "")
        if linkedin_post:
            result = await buffer_schedule(linkedin_post, channel="linkedin")
            scheduled["linkedin"] = result
            logger.info(
                "[marketing] schedule_posts — LinkedIn: status=%s", result.get("status")
            )

    # ---- Email Day-0 via Resend ----
    if "email_sequences" in approved:
        email_seqs = state.get("email_sequences", {})
        onboarding = email_seqs.get("onboarding", [])
        if onboarding:
            day0 = onboarding[0]
            result = await resend_broadcast(
                to=["{{FOUNDER_EMAIL}}"],  # placeholder — production wires real list
                subject=day0.get("subject", ""),
                html_body=day0.get("body_html", ""),
                text_body=day0.get("body_text", ""),
                tags=[{"name": "sequence", "value": "onboarding_day0"}],
            )
            scheduled["email_day0"] = result
            logger.info(
                "[marketing] schedule_posts — Email day0: status=%s", result.get("status")
            )

    # ---- Product Hunt — always manual ----
    if "product_hunt_kit" in approved:
        scheduled["product_hunt"] = {
            "status": "manual",
            "note": "Product Hunt launch requires manual submission at producthunt.com",
        }
        logger.info("[marketing] schedule_posts — Product Hunt: manual reminder set")

    logger.info(
        "[marketing] schedule_posts — done, channels=%s", list(scheduled.keys())
    )

    return {
        **state,
        "scheduled_post_ids": scheduled,
        "errors": errors,
    }
