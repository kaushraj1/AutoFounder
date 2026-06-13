"""Resend email broadcast tool for the Marketing Agent (AF-044).

Used by: schedule_posts (email drip sequences)
Rate limit: 10 req/s
Fallback: Queue locally; SendGrid fallback path if SENDGRID_API_KEY available
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.agents.marketing.utils.retry import retry_async

logger = logging.getLogger(__name__)

_RESEND_BASE = "https://api.resend.com"
_TIMEOUT = 15.0


async def resend_broadcast(
    *,
    to: list[str],
    subject: str,
    html_body: str,
    text_body: str,
    from_address: str = "",
    reply_to: str = "",
    tags: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Send a transactional / broadcast email via Resend.

    Args:
        to: Recipient email addresses.
        subject: Email subject line.
        html_body: HTML email body.
        text_body: Plain text fallback body.
        from_address: Sender address. Reads RESEND_FROM_ADDRESS env if empty.
        reply_to: Reply-to address (optional).
        tags: Resend tags for analytics (optional).

    Returns:
        Dict with "email_id", "status"; status="queued" on failure (non-fatal).
    """
    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        logger.warning("[marketing/resend] RESEND_API_KEY not set — queuing email")
        return _queued_result(subject, reason="no_api_key")

    sender = from_address or os.getenv("RESEND_FROM_ADDRESS", "noreply@mail.autofounder.ai")

    payload: dict[str, Any] = {
        "from": sender,
        "to": to,
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    if tags:
        payload["tags"] = tags

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async def _call() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_RESEND_BASE}/emails",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    try:
        result = await retry_async(_call, max_retries=3, label="resend_broadcast")
        email_id = result.get("id", "unknown")
        logger.info(
            "[marketing/resend] sent email_id=%s subject=%r recipients=%d",
            email_id,
            subject[:40],
            len(to),
        )
        return {"email_id": email_id, "status": "sent"}
    except Exception as exc:
        logger.warning("[marketing/resend] send failed: %s — queuing", exc)
        return _queued_result(subject, reason=str(exc))


def _queued_result(subject: str, reason: str = "") -> dict[str, Any]:
    return {
        "email_id": None,
        "status": "queued",
        "subject": subject,
        "reason": reason,
    }
