"""Node 11 — launch_control_center (AF-044).

HITL gate — polls Redis for Founder approval before scheduling.
Timeout: 30 minutes → TIMED_OUT state → Slack + email alert.

Standalone/test mode: reads approval_status directly from state (set to "approved"
to skip polling, same pattern as ArchitectAgent's hitl_gate).

Production mode: polls Redis key `marketer:approval:{run_id}` at 15s intervals.
The Founder Portal (Raunak AF-059) writes to this key.

Reads:  run_id, approval_status (pre-set for test mode)
Writes: approval_status, approved_content_types, rejected_content_types
"""

from __future__ import annotations

import asyncio
import logging
import os

from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 15
_TIMEOUT_SECONDS = 30 * 60  # 30 minutes
_REDIS_KEY_PREFIX = "marketer:approval:"

# Content types that can be individually approved/rejected
_ALL_CONTENT_TYPES = [
    "landing_page",
    "seo_blogs",
    "product_hunt_kit",
    "social_posts",
    "email_sequences",
    "visual_assets",
]


async def launch_control_center(state: MarketerState) -> MarketerState:
    """LangGraph node: HITL approval gate.

    Test mode: reads approval_status from state (caller sets "approved").
    Production: polls Redis for Founder decision.
    """
    run_id = state.get("run_id", "unknown")
    pre_set_status = (state.get("approval_status") or "").strip()

    # ---- Test / standalone mode: approval already set in state ----
    if pre_set_status in ("approved", "rejected", "partial"):
        logger.info(
            "[marketing] launch_control_center — test mode, status=%s run_id=%s",
            pre_set_status,
            run_id,
        )
        return _build_approval_state(state, pre_set_status)

    # ---- Production mode: poll Redis ----
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        logger.warning(
            "[marketing] launch_control_center — REDIS_URL not set, auto-approving (dev fallback)"
        )
        return _build_approval_state(state, "approved")

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url, decode_responses=True)
        redis_key = f"{_REDIS_KEY_PREFIX}{run_id}"

        logger.info(
            "[marketing] launch_control_center — polling Redis key=%s (timeout=%ds)",
            redis_key,
            _TIMEOUT_SECONDS,
        )

        elapsed = 0
        while elapsed < _TIMEOUT_SECONDS:
            value = await client.get(redis_key)
            if value:
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                status = value.strip().lower()
                logger.info("[marketing] launch_control_center — Founder responded: %s", status)
                await client.aclose()
                return _build_approval_state(state, status)

            await asyncio.sleep(_POLL_INTERVAL_SECONDS)
            elapsed += _POLL_INTERVAL_SECONDS

        # Timeout reached
        await client.aclose()
        logger.warning("[marketing] launch_control_center — TIMED_OUT after %ds", _TIMEOUT_SECONDS)
        return _build_approval_state(state, "timed_out")

    except Exception as exc:
        logger.error("[marketing] launch_control_center — Redis error: %s", exc)
        # Non-fatal: auto-approve on Redis failure in development
        if os.getenv("APP_ENV", "development") == "development":
            logger.warning("[marketing] launch_control_center — Redis failed, auto-approving (dev)")
            return _build_approval_state(state, "approved")
        return _build_approval_state(state, "timed_out")


def _build_approval_state(state: MarketerState, status: str) -> MarketerState:
    """Build state update based on approval status."""
    errors: list[str] = list(state.get("errors", []))

    # Determine approved/rejected content types
    if status == "approved":
        approved = list(_ALL_CONTENT_TYPES)
        rejected: list[str] = []
    elif status == "rejected":
        approved = []
        rejected = list(_ALL_CONTENT_TYPES)
        errors.append("launch_control_center: Founder rejected all content")
    elif status == "partial":
        # Partial approval: check individual type decisions from state
        # Production: these would come from Redis hash fields
        # Test: pass approved_content_types directly in state
        approved = list(state.get("approved_content_types") or _ALL_CONTENT_TYPES[:3])
        rejected = [ct for ct in _ALL_CONTENT_TYPES if ct not in approved]
    elif status == "timed_out":
        approved = []
        rejected = []
        errors.append("launch_control_center: approval timed out after 30 minutes")
    else:
        approved = list(_ALL_CONTENT_TYPES)
        rejected = []

    return {
        **state,
        "approval_status": status,
        "approved_content_types": approved,
        "rejected_content_types": rejected,
        "errors": errors,
    }
