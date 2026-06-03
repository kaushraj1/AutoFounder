"""LangGraph orchestration engine (stub).

Sprint 1 builds a stateful ``StateGraph``: one node per pillar, Postgres + Redis
checkpointing, and HITL interrupt gates. LangGraph is an optional dependency
(``uv sync --group agents``) and is imported lazily inside methods, so importing this
module never requires it to be installed.
"""


class OrchestratorEngine:
    """Drives a run through the pillar graph."""

    async def create_run(self, organization_id: str, idea_text: str) -> str:
        """Start a new run and return its id."""
        raise NotImplementedError("LangGraph engine lands in Phase 1 Sprint 1")

    async def resume(self, run_id: str) -> None:
        """Resume a run paused at a human-in-the-loop gate."""
        raise NotImplementedError("LangGraph engine lands in Phase 1 Sprint 1")
