"""AF-050: LLM-as-judge eval harness for agent outputs.

Runs golden set evaluations per agent using an LLM judge, computes an
:class:`EvalReport`, and gates CI by detecting score regression greater than
``regression_threshold`` from the stored baseline.

Complements the Promptfoo-based harness (``app.eval.gate``) with an
in-process Python alternative that does not require the ``npx`` toolchain.

Usage::

    from app.eval.harness import EvalHarness, EvalCase
    from app.eval.golden_sets import STRATEGY_GOLDEN_CASES

    harness = EvalHarness(llm_router=router)
    cases = [EvalCase(**c) for c in STRATEGY_GOLDEN_CASES]
    report = await harness.evaluate("strategy", cases, baseline_score=0.85)
    if report.regression_detected:
        raise RuntimeError(f"Eval regression: {report.regression_delta:.3f}")
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("app.eval.harness")


class EvalCase(BaseModel):
    """A single evaluation test case."""

    case_id: str
    """Unique identifier for this test case (e.g. ``"strategy-001"``)."""

    agent_id: str
    """The agent being evaluated (e.g. ``"strategy"``)."""

    input: dict[str, Any]
    """Input payload passed to the agent."""

    expected_output: dict[str, Any]
    """Expected output shape / values used by the LLM judge rubric."""

    rubric: str
    """Natural language scoring criteria for the LLM judge."""


class EvalResult(BaseModel):
    """Result for a single evaluation case."""

    case_id: str
    score: float
    """Score in ``[0.0, 1.0]`` assigned by the LLM judge."""

    reasoning: str
    """Judge's explanation for the assigned score."""

    passed: bool
    """Whether the score meets the passing threshold (>= 0.5)."""

    issues: list[str] = []
    """List of specific issues identified by the judge."""


class EvalReport(BaseModel):
    """Aggregated results for an agent's full golden set."""

    agent_id: str
    total_cases: int
    passed_cases: int
    average_score: float
    baseline_score: float | None
    regression_detected: bool
    regression_delta: float
    """Positive means regression (score dropped); negative means improvement."""

    results: list[EvalResult]


_JUDGE_PROMPT_TEMPLATE = """\
You are an expert AI system evaluator. Score the following agent output on a scale of 0.0 to 1.0.

## Scoring Rubric
{rubric}

## Expected Output Characteristics
{expected_output}

## Actual Output
{actual_output}

Respond ONLY in valid JSON with this exact structure:
{{
  "score": <float 0.0-1.0>,
  "reasoning": "<one-sentence explanation>",
  "passed": <true if score >= 0.5>,
  "issues": ["<issue 1>", "<issue 2>"]
}}
"""

_PASS_THRESHOLD = 0.5


class EvalHarness:
    """Run golden set evaluations and gate on regression.

    Args:
        llm_router: Any object implementing ``async complete(task_class, prompt, **kw) -> str``.
        regression_threshold: Maximum allowed score drop as a fraction (default 0.02 = 2%).
    """

    def __init__(self, llm_router: Any, *, regression_threshold: float = 0.02) -> None:
        self.llm = llm_router
        self.regression_threshold = regression_threshold

    async def evaluate(
        self,
        agent_id: str,
        cases: list[EvalCase],
        *,
        actual_outputs: list[dict[str, Any]] | None = None,
        baseline_score: float | None = None,
    ) -> EvalReport:
        """Run all cases through the LLM judge and compute an EvalReport.

        Args:
            agent_id: Identifier of the agent being evaluated.
            cases: List of :class:`EvalCase` instances to judge.
            actual_outputs: Corresponding actual outputs from the agent. When
                ``None`` the ``expected_output`` is used as a self-consistency
                check (useful for smoke-testing the harness itself).
            baseline_score: Prior baseline score to compare against for
                regression detection. ``None`` on first run — always passes.

        Returns:
            :class:`EvalReport` with per-case results, aggregate score, and
            regression flag.
        """
        if actual_outputs is None:
            actual_outputs = [case.expected_output for case in cases]

        results: list[EvalResult] = []
        for case, actual in zip(cases, actual_outputs, strict=False):
            result = await self._judge_single(case, actual)
            results.append(result)
            logger.debug(
                "EvalHarness: case=%s score=%.3f passed=%s",
                case.case_id,
                result.score,
                result.passed,
            )

        total = len(results)
        passed_cases = sum(1 for r in results if r.passed)
        average_score = sum(r.score for r in results) / total if total > 0 else 0.0

        regression_detected, regression_delta = self._detect_regression(
            average_score, baseline_score
        )

        logger.info(
            "EvalHarness: agent=%s cases=%d passed=%d avg=%.3f "
            "baseline=%s regression=%s delta=%.4f",
            agent_id,
            total,
            passed_cases,
            average_score,
            baseline_score,
            regression_detected,
            regression_delta,
        )

        return EvalReport(
            agent_id=agent_id,
            total_cases=total,
            passed_cases=passed_cases,
            average_score=average_score,
            baseline_score=baseline_score,
            regression_detected=regression_detected,
            regression_delta=regression_delta,
            results=results,
        )

    async def _judge_single(
        self, case: EvalCase, actual_output: dict[str, Any]
    ) -> EvalResult:
        """LLM-as-judge: score the actual output against expected + rubric.

        Calls the LLM with a structured prompt and parses the JSON response.
        Falls back to a zero score with an error message if the LLM call or
        JSON parsing fails.

        Args:
            case: The evaluation case containing expected output and rubric.
            actual_output: The actual agent output to score.

        Returns:
            :class:`EvalResult` with score, reasoning, and issues.
        """
        prompt = _JUDGE_PROMPT_TEMPLATE.format(
            rubric=case.rubric,
            expected_output=json.dumps(case.expected_output, indent=2),
            actual_output=json.dumps(actual_output, indent=2),
        )

        try:
            raw = await self.llm.complete(
                task_class="eval_judge", prompt=prompt, json_mode=True
            )
            data = self._parse_judge_response(raw)
            return EvalResult(
                case_id=case.case_id,
                score=float(data.get("score", 0.0)),
                reasoning=str(data.get("reasoning", "")),
                passed=bool(data.get("passed", False)),
                issues=list(data.get("issues", [])),
            )
        except Exception as exc:
            logger.error(
                "EvalHarness/_judge_single: case=%s failed: %s", case.case_id, exc
            )
            return EvalResult(
                case_id=case.case_id,
                score=0.0,
                reasoning=f"Judge call failed: {exc}",
                passed=False,
                issues=[f"Judge error: {exc}"],
            )

    def _detect_regression(
        self, current: float, baseline: float | None
    ) -> tuple[bool, float]:
        """Compare ``current`` score against ``baseline``.

        Args:
            current: Current evaluation score (0.0–1.0).
            baseline: Prior baseline score, or ``None`` for first-ever run.

        Returns:
            Tuple of ``(regression_detected, delta)`` where delta is positive
            when the score dropped and negative when it improved.
        """
        if baseline is None:
            return False, 0.0
        delta = baseline - current  # positive = regression
        regression_detected = delta > self.regression_threshold
        return regression_detected, delta

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_judge_response(self, raw: str) -> dict[str, Any]:
        """Parse the LLM judge's JSON response, stripping markdown fences."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            # Drop opening fence line (```json or ```)
            lines = lines[1:] if lines[0].startswith("```") else lines
            # Drop closing fence line
            lines = lines[:-1] if lines and lines[-1].startswith("```") else lines
            cleaned = "\n".join(lines).strip()
        return json.loads(cleaned)  # type: ignore[return-value]
