"""PRD markdown rendering and artifact persistence for AF-039."""

from __future__ import annotations

import logging
from typing import Any

from app.agents.product_planner.schema import ProductPlannerOutput

logger = logging.getLogger("app.agents.product_planner.persistence")


def render_prd_markdown(output: ProductPlannerOutput) -> str:
    """Deterministic markdown assembly from structured output. No LLM."""
    prd = output.prd
    lines: list[str] = []

    lines += [f"# {prd.title}", "", prd.overview, "", f"**Problem:** {prd.problem_statement}", ""]

    lines += ["## Goals", ""]
    lines += [f"- {g}" for g in prd.goals]
    lines += [""]

    if prd.non_goals:
        lines += ["## Non-Goals", ""]
        lines += [f"- {ng}" for ng in prd.non_goals]
        lines += [""]

    lines += ["## Target Users", ""]
    lines += [f"- {u}" for u in prd.target_users]
    lines += [""]

    if prd.success_metrics:
        lines += ["## Success Metrics", ""]
        lines += [f"- {m}" for m in prd.success_metrics]
        lines += [""]

    if prd.scope_in:
        lines += ["## In Scope", ""]
        lines += [f"- {s}" for s in prd.scope_in]
        lines += [""]

    if prd.scope_out:
        lines += ["## Out of Scope", ""]
        lines += [f"- {s}" for s in prd.scope_out]
        lines += [""]

    if output.requirements:
        lines += ["## Requirements", ""]
        lines += ["| ID | Kind | Priority | Statement | Traces To |"]
        lines += ["|---|---|---|---|---|"]
        for r in output.requirements:
            lines += [f"| {r.id} | {r.kind} | {r.priority} | {r.statement} | {r.traces_to} |"]
        lines += [""]

    if output.user_stories:
        lines += ["## User Stories", ""]
        for s in output.user_stories:
            lines += [
                f"### {s.id} — {s.epic or 'General'}",
                f"**As** {s.role} ({s.persona}), **I want** {s.want}, **so that** {s.benefit}",
                f"**Priority:** {s.priority}",
                "**Acceptance Criteria:**",
            ]
            lines += [f"- {ac}" for ac in s.acceptance_criteria]
            lines += [""]

    if output.roadmap:
        lines += ["## Roadmap", ""]
        for m in output.roadmap:
            weeks = f" ({m.target_weeks} weeks)" if m.target_weeks else ""
            lines += [
                f"### {m.phase} — {m.title}{weeks}",
                m.objective,
            ]
            if m.epics:
                lines += ["**Epics:** " + ", ".join(m.epics)]
            if m.user_story_ids:
                lines += ["**Stories:** " + ", ".join(m.user_story_ids)]
            lines += [""]

    lines += [
        "---",
        f"*Coverage score: {output.coverage_score:.2f} | Confidence: {output.confidence}*",
    ]

    return "\n".join(lines)


async def persist_prd(udal: Any, *, run_id: str, org_id: str, markdown: str) -> str | None:
    """Upload PRD markdown via UDAL object store. Returns public URL or None on failure."""
    path = f"prds/{run_id}/prd.md"
    try:
        uri: str = await udal.object().upload(path, markdown.encode("utf-8"), "text/markdown")
        logger.info("PRD persisted for run %s → %s", run_id, uri)
        return uri
    except Exception as exc:
        logger.warning("PRD persistence failed for run %s: %s", run_id, exc)
        return None
