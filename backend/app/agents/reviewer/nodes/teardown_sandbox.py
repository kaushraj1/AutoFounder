"""Node 12 — teardown_sandbox: remove the ephemeral container/image (plan §3.4)."""

from __future__ import annotations

import logging
from typing import Any

from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.schema import ReviewerState
from app.agents.reviewer.tools import sandbox as sandbox_tool

logger = logging.getLogger("app.agents.reviewer.nodes.teardown_sandbox")


async def teardown_sandbox(state: ReviewerState, agent: Any) -> dict[str, Any]:
    await sandbox_tool.teardown(to_sandbox(state))
    logger.info("Sandbox torn down for run %s", state.run_id)
    return {"sandbox_container_id": None, "sandbox_image_tag": None}
