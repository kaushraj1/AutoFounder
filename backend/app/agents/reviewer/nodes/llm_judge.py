"""Node 9 — llm_judge: readability / maintainability / security scoring (plan §3.4).

The model proposes scores, but objective floors (MIN_*) are enforced in code so a
generous judge can never approve code that misses a hard threshold.
"""

from __future__ import annotations

from typing import Any

from jinja2 import Template

from app.agents.reviewer.schema import (
    MIN_MAINTAINABILITY,
    MIN_READABILITY,
    MIN_SECURITY_POSTURE,
    LLMJudgeScore,
    ReviewerState,
)
from app.agents.reviewer.utils.llm_parse import parse_with_correction
from app.agents.reviewer.utils.redact import redact_url
from app.agents.reviewer.utils.retry import with_retry


@with_retry("llm_judge")
async def llm_judge(state: ReviewerState, agent: Any) -> dict[str, Any]:
    raw_template = agent.prompts.get("reviewer/llm_judge")
    rendered = Template(raw_template).render(
        repo_url=redact_url(state.repo_url),
        branch=state.branch,
        has_python=state.has_python,
        has_typescript=state.has_typescript,
        heal_cycle=state.heal_cycle,
        code_artifacts=state.code_artifacts,
        lint_results=state.lint_results,
        unit_test_result=state.unit_test_result,
        e2e_test_result=state.e2e_test_result,
        security_findings=state.security_findings,
        feature_list=state.feature_list,
    )
    raw = await agent._call_llm(task_class="reviewer_judge", prompt=rendered, json_mode=True)
    score = await parse_with_correction(
        agent=agent,
        task_class="reviewer_judge",
        raw_output=raw,
        schema=LLMJudgeScore,
        original_prompt=rendered,
    )

    floors_ok = (
        score.readability >= MIN_READABILITY
        and score.maintainability >= MIN_MAINTAINABILITY
        and score.security_posture >= MIN_SECURITY_POSTURE
    )
    score.approved = score.approved and floors_ok

    tokens = (len(rendered) + len(raw)) // 4
    return {
        "llm_judge_score": score,
        "total_llm_tokens_used": state.total_llm_tokens_used + tokens,
    }
