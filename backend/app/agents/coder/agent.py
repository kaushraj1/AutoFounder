"""AF-041 Coder Agent (Pillar 3).

Consumes ArchitectOutput and generates a complete, runnable full-stack codebase:
  - FastAPI backend (models, schemas, routers, Alembic migration)
  - Next.js 14 App Router frontend
  - Config files (Dockerfile, docker-compose, CI/CD, README)
  - Automated tests (pytest + Jest)

Pure LLM synthesis — no external tool calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from jinja2 import Template

from app.agents.base import BaseAgent
from app.agents.coder.schema import CoderInput, CoderOutput, GeneratedFile

logger = logging.getLogger("app.agents.coder")

_CACHE_TTL = 86_400  # 24 h
_CACHE_PREFIX = "coder:cache"

# Thresholds for confidence bands
_HIGH_FILE_THRESHOLD = 20
_MEDIUM_FILE_THRESHOLD = 5
_HIGH_LINE_THRESHOLD = 500
_MEDIUM_LINE_THRESHOLD = 50


class CoderAgent(BaseAgent[CoderInput, CoderOutput]):
    """Pillar 3 full-stack code generator.

    Staged LLM synthesis:
      generate_backend → generate_frontend → generate_config → generate_tests
    Verifies output completeness; sets confidence based on file/line counts.
    """

    PILLAR = 3
    AGENT_ID = "coder"
    SLA_SECONDS = 1800  # 30 min — large codebases take time

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def understand(self, input: CoderInput) -> dict[str, Any]:
        """Validate architect_output has required fields; build cache key."""
        ao = input.architect_output

        if not ao.feature_list or not ao.feature_list.features:
            raise ValueError(
                "ArchitectOutput.feature_list.features is empty — "
                "CoderAgent cannot generate code without a feature list"
            )

        if not ao.openapi_3_1:
            logger.warning(
                "ArchitectOutput.openapi_3_1 is empty for run %s — "
                "backend routes will be sparse",
                input.run_id,
            )

        if not ao.erd_mermaid:
            logger.warning(
                "ArchitectOutput.erd_mermaid is empty for run %s — "
                "database models will be inferred from features only",
                input.run_id,
            )

        cache_key = self._cache_key(input)
        # Derive a human-readable idea from the OpenAPI title if present
        idea = (
            ao.openapi_3_1.get("info", {}).get("title", "")
            if isinstance(ao.openapi_3_1, dict)
            else ""
        ) or "SaaS Application"

        return {
            "run_id": input.run_id,
            "organization_id": input.organization_id,
            "cache_key": cache_key,
            "idea": idea,
            "domain": ao.stack.get("backend", "FastAPI"),
            "architect_output": ao,
        }

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Check Redis cache; short-circuit on hit."""
        cache_key = intent["cache_key"]
        try:
            cached = await self.udal.cache.get_session(cache_key)
            if cached:
                logger.info("CoderAgent cache HIT for run %s", intent["run_id"])
                return {**intent, "cache_hit": True, "cached_output": cached}
        except Exception:
            pass
        return {**intent, "cache_hit": False}

    async def execute(self, plan: dict[str, Any]) -> CoderOutput:
        """Staged generation: backend → frontend → config → tests."""
        if plan.get("cache_hit"):
            return CoderOutput.model_validate(plan["cached_output"])

        ao = plan["architect_output"]
        idea: str = plan["idea"]
        total_tokens = 0

        # Stage 1: generate FastAPI backend
        backend_files, tokens = await self._generate_backend(ao, idea)
        total_tokens += tokens

        # Stage 2: generate Next.js frontend
        frontend_files, tokens = await self._generate_frontend(ao, idea)
        total_tokens += tokens

        # Stage 3: generate config files (Dockerfile, docker-compose, CI, README)
        config_files, tokens = await self._generate_config(ao, idea)
        total_tokens += tokens

        # Stage 4: generate test files
        backend_summary = self._summarise_files(backend_files)
        test_files, tokens = await self._generate_tests(ao, backend_summary)
        total_tokens += tokens

        all_files = backend_files + frontend_files + config_files + test_files
        total_lines = sum(f.content.count("\n") + 1 for f in all_files if f.content)

        output = CoderOutput(
            run_id=plan["run_id"],
            organization_id=plan["organization_id"],
            generated_files=all_files,
            backend_files=backend_files,
            frontend_files=frontend_files,
            config_files=config_files,
            test_files=test_files,
            total_files=len(all_files),
            total_lines=total_lines,
            total_llm_tokens_used=total_tokens,
            confidence="low",  # filled by verify()
        )

        # Persist to UDAL (best-effort)
        try:
            summary_json = json.dumps(
                {
                    "run_id": plan["run_id"],
                    "total_files": output.total_files,
                    "total_lines": output.total_lines,
                    "files": [f.path for f in all_files],
                }
            )
            obj = self.udal.object(
                bucket="coder-outputs",
                key=f"runs/{plan['run_id']}/coder_output.json",
            )
            await obj.upload(summary_json.encode())
        except Exception as exc:
            logger.warning(
                "CoderAgent: UDAL persist failed for run %s (non-fatal): %s",
                plan["run_id"],
                exc,
            )

        # Cache result
        try:
            await self.udal.cache.set_session(
                plan["cache_key"], output.model_dump(), ttl=_CACHE_TTL
            )
        except Exception:
            pass

        return output

    async def verify(self, output: CoderOutput) -> dict[str, Any]:
        """Check output completeness; set confidence band."""
        warnings: list[str] = []

        if not output.generated_files:
            output.confidence = "low"
            warnings.append("No files were generated — LLM may have failed on all stages")
            output.warnings = warnings
            return {"passed": False, "confidence": "low", "warnings": warnings}

        # Check backend has a main.py equivalent
        backend_paths = {f.path for f in output.backend_files}
        has_main = any("main.py" in p or "app.py" in p for p in backend_paths)
        if not has_main and output.backend_files:
            warnings.append("No main.py / app.py found in backend_files")

        if output.total_lines <= 0:
            output.confidence = "low"
            warnings.append("total_lines is 0 — generated files appear to be empty")
        elif (
            output.total_files >= _HIGH_FILE_THRESHOLD
            and output.total_lines >= _HIGH_LINE_THRESHOLD
        ):
            output.confidence = "high"
        elif (
            output.total_files >= _MEDIUM_FILE_THRESHOLD
            and output.total_lines >= _MEDIUM_LINE_THRESHOLD
        ):
            output.confidence = "medium"
        else:
            output.confidence = "low"
            warnings.append(
                f"Low output volume: {output.total_files} files, {output.total_lines} lines"
            )

        output.warnings = warnings

        if output.confidence == "low":
            logger.warning(
                "CoderAgent run %s confidence=low (%d files, %d lines). "
                "Codebase flagged for human review.",
                output.run_id,
                output.total_files,
                output.total_lines,
            )

        return {
            "passed": output.total_files > 0,
            "confidence": output.confidence,
            "warnings": warnings,
            "total_files": output.total_files,
            "total_lines": output.total_lines,
        }

    async def learn(self, trace: dict[str, Any]) -> None:
        """Log run telemetry to LLMOps."""
        raw_output = trace.get("output")
        total_files = 0
        total_lines = 0
        tokens = 0
        confidence = "unknown"

        if isinstance(raw_output, CoderOutput):
            total_files = raw_output.total_files
            total_lines = raw_output.total_lines
            tokens = raw_output.total_llm_tokens_used
            confidence = raw_output.confidence
        elif isinstance(raw_output, dict):
            total_files = raw_output.get("total_files", 0)
            total_lines = raw_output.get("total_lines", 0)
            tokens = raw_output.get("total_llm_tokens_used", 0)
            confidence = raw_output.get("confidence", "unknown")

        logger.info(
            "CoderAgent run %s | files=%d | lines=%d | confidence=%s | tokens=%d",
            trace.get("run_id"),
            total_files,
            total_lines,
            confidence,
            tokens,
        )

    # ------------------------------------------------------------------
    # Private: staged generation
    # ------------------------------------------------------------------

    async def _generate_backend(
        self,
        ao: Any,
        idea: str,
    ) -> tuple[list[GeneratedFile], int]:
        """Generate FastAPI backend files."""
        raw_template = self.prompts.get("coder/generate_backend")
        rendered = Template(raw_template).render(
            idea=idea,
            domain=ao.stack.get("backend", "FastAPI"),
            requirements=ao.requirements,
            erd_mermaid=ao.erd_mermaid,
            openapi_spec=ao.openapi_3_1,
            stack=ao.stack,
            features=ao.feature_list.features,
        )
        raw = await self._call_llm(
            task_class="coder_generation", prompt=rendered, json_mode=True
        )
        files = self._parse_files(raw, "generate_backend")
        return files, self._count_tokens(rendered, raw)

    async def _generate_frontend(
        self,
        ao: Any,
        idea: str,
    ) -> tuple[list[GeneratedFile], int]:
        """Generate Next.js 14 frontend files."""
        raw_template = self.prompts.get("coder/generate_frontend")
        rendered = Template(raw_template).render(
            idea=idea,
            domain=ao.stack.get("frontend", "Next.js 14"),
            features=ao.feature_list.features,
            openapi_spec=ao.openapi_3_1,
            stack=ao.stack,
        )
        raw = await self._call_llm(
            task_class="coder_generation", prompt=rendered, json_mode=True
        )
        files = self._parse_files(raw, "generate_frontend")
        return files, self._count_tokens(rendered, raw)

    async def _generate_config(
        self,
        ao: Any,
        idea: str,
    ) -> tuple[list[GeneratedFile], int]:
        """Generate Dockerfile, docker-compose, CI/CD, README."""
        raw_template = self.prompts.get("coder/generate_config")
        rendered = Template(raw_template).render(
            idea=idea,
            domain=ao.stack.get("backend", "FastAPI"),
            stack=ao.stack,
            features=ao.feature_list.features,
        )
        raw = await self._call_llm(
            task_class="coder_generation", prompt=rendered, json_mode=True
        )
        files = self._parse_files(raw, "generate_config")
        return files, self._count_tokens(rendered, raw)

    async def _generate_tests(
        self,
        ao: Any,
        backend_files_summary: str,
    ) -> tuple[list[GeneratedFile], int]:
        """Generate pytest unit tests (backend) + Jest tests (frontend)."""
        raw_template = self.prompts.get("coder/generate_tests")
        rendered = Template(raw_template).render(
            features=ao.feature_list.features,
            requirements=ao.requirements,
            backend_files_summary=backend_files_summary,
        )
        raw = await self._call_llm(
            task_class="coder_generation", prompt=rendered, json_mode=True
        )
        files = self._parse_files(raw, "generate_tests")
        return files, self._count_tokens(rendered, raw)

    # ------------------------------------------------------------------
    # Private: helpers
    # ------------------------------------------------------------------

    def _cache_key(self, input: CoderInput) -> str:
        digest = hashlib.sha256(str(input.run_id).encode()).hexdigest()[:16]
        return f"{_CACHE_PREFIX}:{digest}"

    def _parse_json(self, raw: str, stage: str) -> Any:
        """Strip markdown fences and parse JSON."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            lines = lines[1:] if lines[0].startswith("```") else lines
            lines = lines[:-1] if lines and lines[-1].startswith("```") else lines
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except Exception as exc:
            logger.error(
                "JSON parse failed at stage '%s': %s — raw: %.200s", stage, exc, raw
            )
            return {}

    def _parse_files(self, raw: str, stage: str) -> list[GeneratedFile]:
        """Parse LLM response into a list of GeneratedFile objects."""
        data = self._parse_json(raw, stage)
        if not isinstance(data, dict):
            logger.warning(
                "Coder stage '%s': expected dict with 'files' key, got %s",
                stage,
                type(data).__name__,
            )
            return []

        raw_files = data.get("files", [])
        if not isinstance(raw_files, list):
            return []

        result: list[GeneratedFile] = []
        for item in raw_files:
            try:
                result.append(GeneratedFile(**item))
            except Exception as exc:
                logger.warning(
                    "Coder stage '%s': skipping malformed file entry: %s", stage, exc
                )
        return result

    def _summarise_files(self, files: list[GeneratedFile]) -> str:
        """Build a compact summary of backend file paths for test generation context."""
        if not files:
            return "(no backend files generated)"
        lines = [f"- {f.path} ({f.language})" for f in files[:30]]
        if len(files) > 30:
            lines.append(f"... and {len(files) - 30} more files")
        return "\n".join(lines)

    @staticmethod
    def _count_tokens(prompt: str, response: str) -> int:
        """Rough token estimate (4 chars/token) for LLMOps telemetry."""
        return (len(prompt) + len(response)) // 4
