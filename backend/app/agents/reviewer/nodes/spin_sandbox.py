"""Node 2 — spin_sandbox: build + prepare the ephemeral execution env (plan §3.4).

Runs once per cycle (the heal loop re-enters here after applying patches). Before
rebuilding it tears down the previous cycle's sandbox so a self-heal run does not
leak one Docker image per cycle. A ``SandboxError`` (e.g. Dockerfile build
failure) is FATAL → error_handler.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.reviewer import metrics
from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.schema import SANDBOX_SPINUP_SLA_SECONDS, ReviewerState
from app.agents.reviewer.tools import sandbox as sandbox_tool

logger = logging.getLogger("app.agents.reviewer.nodes.spin_sandbox")


async def spin_sandbox(state: ReviewerState, agent: Any) -> dict[str, Any]:
    if not state.workdir:
        return {"fatal_error": "spin_sandbox: no workdir from ingest"}

    # Heal-loop re-entry: clean up the prior cycle's container/image first.
    if state.sandbox_image_tag or state.sandbox_container_id:
        await sandbox_tool.teardown(to_sandbox(state))

    try:
        sandbox = await sandbox_tool.spin_up(
            state.workdir, run_id=str(state.run_id), cycle=state.heal_cycle
        )
    except sandbox_tool.SandboxError as exc:
        logger.error("Sandbox spin-up failed: %s", exc)
        return {"fatal_error": f"Sandbox build failed: {exc}"}

    if sandbox.spinup_seconds > SANDBOX_SPINUP_SLA_SECONDS:
        metrics.SLA_BREACHES.labels(node="spin_sandbox").inc()
        logger.warning(
            "Sandbox spin-up %.1fs exceeded %.0fs SLA",
            sandbox.spinup_seconds,
            SANDBOX_SPINUP_SLA_SECONDS,
        )

    return {
        "sandbox_container_id": sandbox.container_id,
        "sandbox_image_tag": sandbox.image_tag,
        "sandbox_spinup_seconds": sandbox.spinup_seconds,
    }
