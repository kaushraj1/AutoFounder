"""Node E — error_handler: central escalation sink (plan §3.4).

Force-teardown the sandbox, finalise the verdict as ESCALATE, persist a report,
comment on the PR, and alert ops (Slack). Never raises — it is the terminal
recovery path for both fatal errors and intentional escalations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.agents.reviewer import metrics
from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.nodes.emit_report import build_fallback_report
from app.agents.reviewer.persistence import persist_report
from app.agents.reviewer.schema import NodeStatus, ReviewDecision, ReviewerState
from app.agents.reviewer.tools import github
from app.agents.reviewer.tools import sandbox as sandbox_tool
from app.agents.reviewer.utils.redact import redact_url
from app.core.config import get_settings

logger = logging.getLogger("app.agents.reviewer.nodes.error_handler")


async def error_handler(state: ReviewerState, agent: Any) -> dict[str, Any]:
    settings = get_settings()

    # Force-teardown so no container/image is orphaned on the failure path.
    try:
        await sandbox_tool.teardown(to_sandbox(state))
    except Exception as exc:  # noqa: BLE001 - cleanup must not mask the escalation
        logger.warning("Force-teardown error (ignored): %s", exc)

    reason = state.escalation_reason or state.fatal_error or _summarise_failures(state)
    logger.error("Reviewer escalation for run %s: %s", state.run_id, reason)

    updated = state.model_copy(
        update={"review_decision": ReviewDecision.ESCALATE, "escalation_reason": reason}
    )
    markdown = build_fallback_report(updated)

    report_uri = await persist_report(
        agent.udal,
        run_id=str(state.run_id),
        org_id=state.organization_id,
        markdown=markdown,
        findings=state.security_findings,
    )
    comment_url = await github.post_pr_comment(
        state.repo_url, state.pr_number, markdown, token=settings.github_token or None
    )

    await _alert_slack(state, reason, settings.slack_webhook_reviewer)
    metrics.DECISION.labels(decision=str(ReviewDecision.ESCALATE)).inc()

    return {
        "review_decision": ReviewDecision.ESCALATE,
        "escalation_reason": reason,
        "is_approved": False,
        "is_complete": False,
        "review_report_markdown": markdown,
        "review_report_uri": report_uri,
        "github_pr_comment_url": comment_url,
    }


def _summarise_failures(state: ReviewerState) -> str:
    failed = [t.node for t in state.node_traces if t.status is NodeStatus.FAILED]
    if failed:
        return f"node failures: {', '.join(dict.fromkeys(failed))}"
    if state.current_failures:
        return "; ".join(state.current_failures[:5])
    return "unspecified review failure"


async def _alert_slack(state: ReviewerState, reason: str, webhook_url: str) -> None:
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_REVIEWER not configured — skipping alert")
        return
    payload = {
        "text": (
            ":red_circle: *Reviewer Agent — escalation*\n"
            f"*Run*: `{state.run_id}`\n"
            f"*Tenant*: `{state.organization_id}`\n"
            f"*Repo*: {redact_url(state.repo_url)} (`{state.branch}`)\n"
            f"*Reason*: {reason}\n"
            f"*OWASP*: {', '.join(state.owasp_violations) or 'none'}\n"
            f"*Time*: {datetime.now(UTC).isoformat()}"
        )
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload, timeout=5.0)
    except Exception as exc:  # noqa: BLE001 - alerting is best-effort
        logger.error("Failed to post Slack escalation alert: %s", exc)
