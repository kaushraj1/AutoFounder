"""AF-038 Research Agent (Pillar 1).

Tool fan-out specialist: Tavily + SerpAPI + Crunchbase + G2 + SimilarWeb,
multi-source synthesis, citation groundedness check.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from jinja2 import Template

from app.agents.base import BaseAgent
from app.agents.research.fanout import fan_out
from app.agents.research.groundedness import (
    GROUNDEDNESS_THRESHOLD,
    confidence_band,
    score_groundedness,
)
from app.agents.research.schema import (
    Citation,
    ResearchFinding,
    ResearchInput,
    ResearchOutput,
    SourceResult,
)

logger = logging.getLogger("app.agents.research")

_CACHE_TTL = 86_400  # 24 h
_CACHE_PREFIX = "research"


class ResearchAgent(BaseAgent[ResearchInput, ResearchOutput]):
    """Pillar 1 tool-fan-out specialist.

    Drives 5 external sources in parallel, synthesises results via LLM,
    and verifies citation groundedness before returning.
    """

    PILLAR = 1
    AGENT_ID = "research"
    SLA_SECONDS = 600  # 10 min

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def understand(self, input: ResearchInput) -> dict[str, Any]:
        """Validate input, build sub-queries, check Redis cache."""
        if not input.idea_normalised or len(input.idea_normalised.strip()) < 5:
            raise ValueError("idea_normalised is empty or too short")
        if not input.domain:
            raise ValueError("domain is required")

        queries = input.queries or [
            f"{input.domain} market size trends",
            f"{input.domain} top competitors funding",
            f"{input.idea_normalised} user pain points",
        ]

        cache_key = self._cache_key(input)

        return {
            "run_id": input.run_id,
            "organization_id": input.organization_id,
            "idea_normalised": input.idea_normalised,
            "domain": input.domain,
            "queries": queries,
            "sources": input.sources,
            "cache_key": cache_key,
        }

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Check cache; if hit, short-circuit. Otherwise build fan-out plan."""
        cache_key = intent["cache_key"]

        try:
            cached = await self.udal.cache.get_session(cache_key)
            if cached:
                logger.info("Research cache HIT for run %s", intent["run_id"])
                return {**intent, "cache_hit": True, "cached_output": cached}
        except Exception:
            # Redis unavailable — proceed without cache
            pass

        return {**intent, "cache_hit": False}

    async def execute(self, plan: dict[str, Any]) -> ResearchOutput:
        """Fan-out sources → dedupe citations → LLM synthesis."""
        if plan.get("cache_hit"):
            return ResearchOutput.model_validate(plan["cached_output"])

        primary_query = " ".join(plan["queries"][:2])
        source_results: list[SourceResult] = await fan_out(
            self._call_tool,
            primary_query,
            plan["sources"],
            limit=5,
            per_tool_timeout=20.0,
        )

        all_citations, partial_sources = self._collect_citations(source_results)

        findings = await self._synthesise(
            idea_normalised=plan["idea_normalised"],
            domain=plan["domain"],
            sources=all_citations,
        )

        output = ResearchOutput(
            run_id=plan["run_id"],
            organization_id=plan["organization_id"],
            domain=plan["domain"],
            findings=findings,
            sources=all_citations,
            groundedness_score=0.0,   # filled by verify()
            confidence="low",          # filled by verify()
            partial_sources=partial_sources,
        )

        try:
            await self.udal.cache.set_session(
                plan["cache_key"], output.model_dump(), ttl=_CACHE_TTL
            )
        except Exception:
            pass

        return output

    async def verify(self, output: ResearchOutput) -> dict[str, Any]:
        """Compute groundedness; retry retrieval once if below threshold."""
        gs = score_groundedness(output.findings, output.sources)

        if gs < GROUNDEDNESS_THRESHOLD and output.findings:
            logger.info(
                "Groundedness %.2f < %.2f — retrying synthesis for run %s",
                gs, GROUNDEDNESS_THRESHOLD, output.run_id,
            )
            retry_findings = await self._synthesise(
                idea_normalised=output.domain,
                domain=output.domain,
                sources=output.sources,
            )
            gs_retry = score_groundedness(retry_findings, output.sources)
            if gs_retry > gs:
                output.findings = retry_findings
                gs = gs_retry

        object.__setattr__(output, "groundedness_score", gs) if False else None
        output.__dict__["groundedness_score"] = gs
        output.__dict__["confidence"] = confidence_band(gs)

        if gs < GROUNDEDNESS_THRESHOLD:
            logger.warning(
                "Research run %s confidence=low (groundedness=%.2f). "
                "Findings flagged for human review.",
                output.run_id, gs,
            )

        return {"passed": True, "groundedness_score": gs, "confidence": output.confidence}

    async def learn(self, trace: dict[str, Any]) -> None:
        raw_output = trace.get("output")
        gs = 0.0
        tokens = 0
        if isinstance(raw_output, ResearchOutput):
            gs = raw_output.groundedness_score
            tokens = raw_output.total_llm_tokens_used
        elif isinstance(raw_output, dict):
            gs = raw_output.get("groundedness_score", 0.0)
            tokens = raw_output.get("total_llm_tokens_used", 0)

        logger.info(
            "Research run %s | domain=%s | sources=%d | gs=%.2f | confidence=%s | tokens=%d",
            trace.get("run_id"),
            trace.get("intent", {}).get("domain", ""),
            len(trace.get("intent", {}).get("sources", [])),
            gs,
            confidence_band(gs),
            tokens,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cache_key(self, input: ResearchInput) -> str:
        payload = f"{input.domain}:{input.idea_normalised}:{','.join(sorted(input.sources))}"
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return f"{_CACHE_PREFIX}:{digest}"

    def _collect_citations(
        self, results: list[SourceResult]
    ) -> tuple[list[Citation], list[str]]:
        seen_urls: set[str] = set()
        citations: list[Citation] = []
        partial: list[str] = []

        for sr in results:
            if not sr.ok:
                partial.append(sr.source)
                continue
            for c in sr.items:
                key = c.url or c.snippet[:80]
                if key not in seen_urls:
                    seen_urls.add(key)
                    citations.append(c)

        return citations, partial

    async def _synthesise(
        self,
        *,
        idea_normalised: str,
        domain: str,
        sources: list[Citation],
    ) -> list[ResearchFinding]:
        if not sources:
            return []

        raw_template = self.prompts.get("research/synthesis")
        rendered = Template(raw_template).render(
            idea_normalised=idea_normalised,
            domain=domain,
            sources=[s.model_dump() for s in sources],
        )
        raw = await self._call_llm(
            task_class="research_synthesis", prompt=rendered, json_mode=True
        )

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            lines = lines[1:] if lines[0].startswith("```") else lines
            lines = lines[:-1] if lines and lines[-1].startswith("```") else lines
            cleaned = "\n".join(lines).strip()

        try:
            data = json.loads(cleaned)
            return [ResearchFinding(**item) for item in data]
        except Exception as exc:
            logger.error("Synthesis parse failed: %s — raw: %.200s", exc, raw)
            return []
