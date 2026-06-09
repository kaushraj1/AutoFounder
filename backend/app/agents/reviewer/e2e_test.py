"""Local e2e harness for the Reviewer agent (plan §9.4).

Run the full graph against a local repo without the platform:

    uv run python -m app.agents.reviewer.e2e_test --repo <path> --mock-llm

With ``--mock-llm`` a deterministic fake router drives judge/triage/heal/report
so the run is reproducible offline; without it, the real Gemini router is used
(requires GEMINI_API_KEY).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.agents._providers import JinjaPromptRegistry
from app.agents._providers.gemini_router import GeminiRouter
from app.agents.reviewer.agent import ReviewerAgent
from app.agents.reviewer.registry import ReviewerToolRegistry
from app.agents.reviewer.schema import ReviewerInput, ReviewerOutput
from app.core.config import get_settings

logger = logging.getLogger("app.agents.reviewer.e2e_test")


class _MockLLMRouter:
    """Deterministic offline router: approves clean code, no heal needed."""

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        if task_class == "reviewer_judge":
            return json.dumps(
                {
                    "readability": 85,
                    "maintainability": 82,
                    "security_posture": 80,
                    "overall": 83,
                    "approved": True,
                    "rationale": "Clean, well-structured code.",
                }
            )
        if task_class == "reviewer_triage":
            return json.dumps({"decision": "approved", "reason": "all green", "failures": []})
        if task_class == "reviewer_heal":
            return json.dumps({"patches": []})
        return "# Code Review Report\n\nApproved."


class _StubObjectStore:
    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        return f"memory://{path}"


class _StubUDAL:
    def object(self) -> _StubObjectStore:
        return _StubObjectStore()


async def _run(repo: str, mock_llm: bool) -> ReviewerOutput:
    settings = get_settings()
    router: Any = _MockLLMRouter() if mock_llm else GeminiRouter(settings.gemini_api_key)
    agent = ReviewerAgent(
        udal=_StubUDAL(),
        checkpointer=MemorySaver(),
        tool_registry=ReviewerToolRegistry(),
        prompt_registry=JinjaPromptRegistry(),
        llm_router=router,
    )
    state = await agent.run(
        ReviewerInput(organization_id="cli-org", repo_url="local", local_path=repo)
    )
    import time

    return ReviewerOutput.from_state(state, completed_at_unix_ms=int(time.time() * 1000))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Reviewer agent local e2e harness")
    parser.add_argument("--repo", required=True, help="Path to a local repo to review")
    parser.add_argument("--mock-llm", action="store_true", help="Use the deterministic fake LLM")
    args = parser.parse_args()

    output = asyncio.run(_run(args.repo, args.mock_llm))
    print(json.dumps(output.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
