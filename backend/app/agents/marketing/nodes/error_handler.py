"""Error handler node for the Marketing Agent (AF-044).

Central error sink — logs all accumulated errors and sends a Slack alert.
Terminal node: graph routes here on fatal_error or exhausted hallucination retries.

Reads:  errors, fatal_error, run_id, organization_id
Writes: (no new fields; terminal)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)


async def error_handler(state: MarketerState) -> MarketerState:
    """LangGraph node: central error sink — log + Slack alert."""
    run_id = state.get("run_id", "unknown")
    org_id = state.get("organization_id", "unknown")
    errors = state.get("errors", [])
    fatal = state.get("fatal_error")

    logger.error(
        "[marketing] error_handler — run=%s org=%s fatal=%r errors=%d",
        run_id,
        org_id,
        fatal,
        len(errors),
    )
    for err in errors:
        logger.error("[marketing]   • %s", err)

    # ---- Slack alert (non-fatal if webhook not configured) ----
    webhook_url = os.getenv("SLACK_WEBHOOK_MARKETER", "")
    if webhook_url:
        await _send_slack_alert(webhook_url, run_id, org_id, fatal, errors)

    return state  # terminal — no new fields written


async def _send_slack_alert(
    webhook_url: str,
    run_id: str,
    org_id: str,
    fatal: str | None,
    errors: list[str],
) -> None:
    """Send a Slack alert via incoming webhook."""
    message: dict[str, Any] = {
        "text": f"🚨 *Marketing Agent Error* — run `{run_id}` org `{org_id}`",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🚨 *Marketing Agent (Pillar 6) — Error*\n"
                        f"*Run ID:* `{run_id}`\n"
                        f"*Org ID:* `{org_id}`\n"
                        f"*Fatal:* {fatal or 'None'}"
                    ),
                },
            },
        ],
    }
    if errors:
        error_text = "\n".join(f"• {e}" for e in errors[:10])
        message["blocks"].append({  # type: ignore[arg-type]
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Errors:*\n```{error_text}```"},
        })

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=message)
            resp.raise_for_status()
        logger.info("[marketing] error_handler — Slack alert sent")
    except Exception as exc:
        logger.warning("[marketing] error_handler — Slack alert failed: %s", exc)
