"""AF-039 Product Planner Agent (Pillar 1.5).

Runs after founder approves the Strategy Agent's HITL gate.
Turns validated StrategyOutput into a PRD, requirements, user stories, and roadmap.
Pure LLM synthesis — no external tool calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from jinja2 import Template

from app.agents.base import BaseAgent
from app.agents.product_planner.coverage import (
    COVERAGE_THRESHOLD,
    confidence_band,
    score_coverage,
)
from app.agents.product_planner.persistence import persist_prd, render_prd_markdown
from app.agents.product_planner.schema import (
    PRD,
    Milestone,
    ProductPlannerInput,
    ProductPlannerOutput,
    Requirement,
    UserStory,
)

logger = logging.getLogger("app.agents.product_planner")

_CACHE_TTL = 86_400  # 24 h
_CACHE_PREFIX = "product_planner"


class ProductPlannerAgent(BaseAgent[ProductPlannerInput, ProductPlannerOutput]):
    """Pillar 1.5 PRD + requirements + user stories + roadmap generator.

    Staged LLM synthesis:
      generate_prd → extract_requirements → generate_user_stories → build_roadmap
    Verifies traceability coverage; retries once if below threshold.
    """

    PILLAR = 1  # conceptual stage 1.5 (post-validation-gate sub-stage of Pillar 1)
    AGENT_ID = "product_planner"
    SLA_SECONDS = 600  # 10 min

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def understand(self, input: ProductPlannerInput) -> dict[str, Any]:
        """Validate strategy present; warn on reject band; build cache key."""
        s = input.strategy
        if s.lean_canvas is None:
            raise ValueError("StrategyOutput.lean_canvas is required for PRD generation")
        if not s.icps:
            logger.warning(
                "StrategyOutput has no personas for run %s — user stories will be sparse",
                input.run_id,
            )
        if s.viability_band == "reject":
            logger.warning(
                "StrategyOutput viability_band='reject' for run %s — "
                "proceeding because agent was explicitly invoked post-approval",
                input.run_id,
            )

        cache_key = self._cache_key(input)
        return {
            "run_id": input.run_id,
            "organization_id": input.organization_id,
            "domain": s.domain,
            "strategy": s,
            "cache_key": cache_key,
        }

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Check Redis cache; short-circuit on hit."""
        cache_key = intent["cache_key"]
        try:
            cached = await self.udal.cache.get_session(cache_key)
            if cached:
                logger.info("ProductPlanner cache HIT for run %s", intent["run_id"])
                return {**intent, "cache_hit": True, "cached_output": cached}
        except Exception:
            pass
        return {**intent, "cache_hit": False}

    async def execute(self, plan: dict[str, Any]) -> ProductPlannerOutput:
        """Staged generation: PRD → requirements → user stories → roadmap."""
        if plan.get("cache_hit"):
            return ProductPlannerOutput.model_validate(plan["cached_output"])

        s = plan["strategy"]
        total_tokens = 0

        # Stage 1: generate PRD
        prd, tokens = await self._generate_prd(s)
        total_tokens += tokens

        # Stage 2: extract requirements
        requirements, tokens = await self._extract_requirements(prd, s)
        total_tokens += tokens

        # Stage 3: generate user stories
        functional_reqs = [r for r in requirements if r.kind == "functional"]
        user_stories, tokens = await self._generate_user_stories(s, functional_reqs)
        total_tokens += tokens

        # Stage 4: build roadmap
        roadmap, tokens = await self._build_roadmap(requirements, user_stories)
        total_tokens += tokens

        output = ProductPlannerOutput(
            run_id=plan["run_id"],
            organization_id=plan["organization_id"],
            domain=plan["domain"],
            prd=prd,
            requirements=requirements,
            user_stories=user_stories,
            roadmap=roadmap,
            prd_markdown="",  # filled after verify()
            coverage_score=0.0,  # filled by verify()
            confidence="low",  # filled by verify()
            total_llm_tokens_used=total_tokens,
        )

        # Render markdown and persist (best-effort)
        output.prd_markdown = render_prd_markdown(output)
        uri = await persist_prd(
            self.udal,
            run_id=plan["run_id"],
            org_id=plan["organization_id"],
            markdown=output.prd_markdown,
        )
        if uri:
            output.prd_s3_uri = uri

        try:
            await self.udal.cache.set_session(
                plan["cache_key"], output.model_dump(), ttl=_CACHE_TTL
            )
        except Exception:
            pass

        return output

    async def verify(self, output: ProductPlannerOutput) -> dict[str, Any]:
        """Compute traceability coverage; retry once if below threshold."""
        coverage = self._compute_coverage(output)

        if coverage < COVERAGE_THRESHOLD and output.requirements:
            logger.info(
                "Coverage %.2f < %.2f — retrying generation with strict trace-or-drop for run %s",
                coverage,
                COVERAGE_THRESHOLD,
                output.run_id,
            )
            retry_output = await self._retry_generation(output)
            retry_coverage = self._compute_coverage(retry_output)
            if retry_coverage > coverage:
                # Patch in-place
                output.requirements = retry_output.requirements
                output.user_stories = retry_output.user_stories
                output.roadmap = retry_output.roadmap
                output.prd_markdown = render_prd_markdown(output)
                coverage = retry_coverage

        output.__dict__["coverage_score"] = coverage
        output.__dict__["confidence"] = confidence_band(coverage)

        if coverage < COVERAGE_THRESHOLD:
            logger.warning(
                "ProductPlanner run %s confidence=low (coverage=%.2f). "
                "PRD flagged for human review.",
                output.run_id,
                coverage,
            )

        return {"passed": True, "coverage_score": coverage, "confidence": output.confidence}

    async def learn(self, trace: dict[str, Any]) -> None:
        raw_output = trace.get("output")
        coverage = 0.0
        tokens = 0
        n_reqs = 0
        n_stories = 0
        if isinstance(raw_output, ProductPlannerOutput):
            coverage = raw_output.coverage_score
            tokens = raw_output.total_llm_tokens_used
            n_reqs = len(raw_output.requirements)
            n_stories = len(raw_output.user_stories)
        elif isinstance(raw_output, dict):
            coverage = raw_output.get("coverage_score", 0.0)
            tokens = raw_output.get("total_llm_tokens_used", 0)
            n_reqs = len(raw_output.get("requirements", []))
            n_stories = len(raw_output.get("user_stories", []))

        logger.info(
            "ProductPlanner run %s | domain=%s | reqs=%d | stories=%d | "
            "coverage=%.2f | confidence=%s | tokens=%d",
            trace.get("run_id"),
            trace.get("intent", {}).get("domain", ""),
            n_reqs,
            n_stories,
            coverage,
            confidence_band(coverage),
            tokens,
        )

    # ------------------------------------------------------------------
    # Private: staged generation
    # ------------------------------------------------------------------

    async def _generate_prd(self, s: Any) -> tuple[PRD, int]:
        raw_template = self.prompts.get("product_planner/generate_prd")
        rendered = Template(raw_template).render(
            idea_normalised=s.idea_normalised,
            domain=s.domain,
            viability_score=s.viability_score,
            viability_band=s.viability_band,
            canvas=s.lean_canvas,
            personas=s.icps,
        )
        raw = await self._call_llm(
            task_class="product_planner_generation", prompt=rendered, json_mode=True
        )
        data = self._parse_json(raw, "generate_prd")
        return PRD(**data), self._count_tokens(rendered, raw)

    async def _extract_requirements(self, prd: PRD, s: Any) -> tuple[list[Requirement], int]:
        raw_template = self.prompts.get("product_planner/extract_requirements")
        rendered = Template(raw_template).render(
            prd=prd,
            canvas=s.lean_canvas,
            personas=s.icps,
        )
        raw = await self._call_llm(
            task_class="product_planner_generation", prompt=rendered, json_mode=True
        )
        data = self._parse_json(raw, "extract_requirements")
        if not isinstance(data, list):
            return [], self._count_tokens(rendered, raw)
        reqs = []
        for item in data:
            try:
                reqs.append(Requirement(**item))
            except Exception as exc:
                logger.warning("Skipping malformed requirement: %s", exc)
        return reqs, self._count_tokens(rendered, raw)

    async def _generate_user_stories(
        self, s: Any, requirements: list[Requirement]
    ) -> tuple[list[UserStory], int]:
        raw_template = self.prompts.get("product_planner/generate_user_stories")
        rendered = Template(raw_template).render(
            personas=s.icps,
            requirements=requirements,
        )
        raw = await self._call_llm(
            task_class="product_planner_generation", prompt=rendered, json_mode=True
        )
        data = self._parse_json(raw, "generate_user_stories")
        if not isinstance(data, list):
            return [], self._count_tokens(rendered, raw)
        stories = []
        for item in data:
            try:
                stories.append(UserStory(**item))
            except Exception as exc:
                logger.warning("Skipping malformed user story: %s", exc)
        return stories, self._count_tokens(rendered, raw)

    async def _build_roadmap(
        self, requirements: list[Requirement], user_stories: list[UserStory]
    ) -> tuple[list[Milestone], int]:
        raw_template = self.prompts.get("product_planner/build_roadmap")
        rendered = Template(raw_template).render(
            requirements=requirements,
            user_stories=user_stories,
        )
        raw = await self._call_llm(
            task_class="product_planner_generation", prompt=rendered, json_mode=True
        )
        data = self._parse_json(raw, "build_roadmap")
        if not isinstance(data, list):
            return [], self._count_tokens(rendered, raw)
        milestones = []
        for item in data:
            try:
                milestones.append(Milestone(**item))
            except Exception as exc:
                logger.warning("Skipping malformed milestone: %s", exc)
        return milestones, self._count_tokens(rendered, raw)

    async def _retry_generation(self, output: ProductPlannerOutput) -> ProductPlannerOutput:
        """Single retry with strict 'trace-or-drop' instruction for low-coverage runs."""
        # Re-extract requirements with a stricter trace-or-drop system message
        strict_prompt = (
            "STRICT MODE: trace-or-drop. For every requirement and user story below, "
            "keep it ONLY if you can name the exact canvas item or persona it derives from. "
            "Remove anything you cannot trace. Return the same JSON format.\n\n"
            f"Requirements to audit:\n"
            f"{json.dumps([r.model_dump() for r in output.requirements])}\n\n"
            f"User stories to audit:\n"
            f"{json.dumps([s.model_dump() for s in output.user_stories])}"
        )
        raw = await self._call_llm(
            task_class="product_planner_generation",
            prompt=strict_prompt,
            json_mode=True,
        )
        # Best-effort: try to parse two sections out; if unparseable, return original
        try:
            data = self._parse_json(raw, "retry")
            if isinstance(data, dict):
                reqs = [Requirement(**r) for r in data.get("requirements", [])]
                stories = [UserStory(**s) for s in data.get("user_stories", [])]
                if reqs or stories:
                    output.requirements = reqs or output.requirements
                    output.user_stories = stories or output.user_stories
        except Exception:
            pass
        return output

    # ------------------------------------------------------------------
    # Private: coverage
    # ------------------------------------------------------------------

    def _compute_coverage(self, output: ProductPlannerOutput) -> float:
        """Derive coverage from output alone (canvas + personas reconstructed via prd)."""
        from app.agents.strategy.schema import BuyerPersona, LeanCanvas

        # Reconstruct a minimal canvas from the PRD for scoring purposes
        problem_items = [output.prd.problem_statement] if output.prd.problem_statement else []
        solution_items = list(output.prd.scope_in)
        canvas = LeanCanvas(
            problem=problem_items or [""],
            customer_segments=output.prd.target_users or [""],
            unique_value_proposition=output.prd.overview or "",
            solution=solution_items or [""],
            unfair_advantage="",
            early_adopters="",
        )
        # Reconstruct persona stubs from target_users
        personas = [
            BuyerPersona(
                name=name,
                role=name,
                company_size="unknown",
                pain_points=[],
                goals=[],
            )
            for name in output.prd.target_users
        ]
        return score_coverage(
            output.prd, output.requirements, output.user_stories, canvas, personas
        )

    # ------------------------------------------------------------------
    # Private: helpers
    # ------------------------------------------------------------------

    def _cache_key(self, input: ProductPlannerInput) -> str:
        payload = (
            f"{input.strategy.run_id}:{input.strategy.domain}:{input.strategy.viability_score}"
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return f"{_CACHE_PREFIX}:{digest}"

    def _parse_json(self, raw: str, stage: str) -> Any:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            lines = lines[1:] if lines[0].startswith("```") else lines
            lines = lines[:-1] if lines and lines[-1].startswith("```") else lines
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except Exception as exc:
            logger.error("JSON parse failed at stage '%s': %s — raw: %.200s", stage, exc, raw)
            return {} if stage == "generate_prd" else []

    @staticmethod
    def _count_tokens(prompt: str, response: str) -> int:
        """Rough token estimate (4 chars/token) for LLMOps telemetry."""
        return (len(prompt) + len(response)) // 4
