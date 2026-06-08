import logging
from datetime import UTC, datetime

import httpx

from app.agents.strategy.schema import NodeStatus, StrategistState

logger = logging.getLogger("app.agents.strategy.error_handler")

SLACK_WEBHOOK = "SLACK_WEBHOOK_STRATEGIST"  # resolved from environment


async def error_handler(state: StrategistState) -> dict:
    """
    Central error sink. Attempts graceful recovery where possible;
    sets fatal_error and triggers human escalation otherwise.
    """
    failed_nodes = [
        t
        for t in state.node_traces
        if t.status == NodeStatus.FAILED and t.retry_count >= state.retry_policy.max_retries
    ]

    if not failed_nodes:
        logger.warning(
            "error_handler invoked but no fatally failed nodes found. run_id=%s", state.run_id
        )
        return {}

    error_summary = "; ".join(f"{t.node}: {t.error}" for t in failed_nodes)
    logger.error("Fatal errors in run %s: %s", state.run_id, error_summary)

    # Notify ops channel
    await _post_slack_alert(state, error_summary)

    return {
        "fatal_error": (
            f"Fatal errors after {state.retry_policy.max_retries} retries: {error_summary}"
        ),
        "is_complete": False,
    }


async def _post_slack_alert(state: StrategistState, error_summary: str) -> None:
    import os

    webhook_url = os.environ.get(SLACK_WEBHOOK)
    if not webhook_url:
        logger.warning("Slack webhook not configured — skipping alert")
        return

    payload = {
        "text": (
            f":red_circle: *Strategist Agent Fatal Error*\n"
            f"*Run ID*: `{state.run_id}`\n"
            f"*Tenant*: `{state.organization_id}`\n"
            f"*Idea*: {state.idea_normalised or state.idea_raw[:80]}\n"
            f"*Error*: {error_summary}\n"
            f"*Time*: {datetime.now(UTC).isoformat()}"
        )
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(webhook_url, json=payload, timeout=5)
        except Exception as exc:
            logger.error("Failed to post Slack alert: %s", exc)
