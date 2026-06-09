"""Node 11 — auto_heal: generate + apply minimal source patches (plan §3.4, D5).

Patches to test files are rejected (patching tests hides bugs). After applying,
the graph loops back to ``spin_sandbox`` to re-run the full suite.
"""

from __future__ import annotations

import logging
from typing import Any

from jinja2 import Template

from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.schema import HealCycle, ReviewerState
from app.agents.reviewer.tools import github
from app.agents.reviewer.utils.llm_parse import loads_lenient

logger = logging.getLogger("app.agents.reviewer.nodes.auto_heal")

_TEST_DIR_MARKERS = ("/tests/", "/__tests__/", "tests/", "__tests__/")


def is_test_file(path: str) -> bool:
    """True if a path looks like a test file (must never be auto-patched)."""
    p = path.replace("\\", "/").lower()
    name = p.rsplit("/", 1)[-1]
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    if ".test." in name or ".spec." in name:
        return True
    return any(marker in p for marker in _TEST_DIR_MARKERS)


async def auto_heal(state: ReviewerState, agent: Any) -> dict[str, Any]:
    cycle = state.heal_cycle + 1
    heal = HealCycle(cycle=cycle, issues_targeted=list(state.current_failures))
    tokens = 0
    patches: dict[str, str] = {}

    try:
        rendered = Template(agent.prompts.get("reviewer/auto_heal")).render(
            heal_cycle=cycle,
            current_failures=state.current_failures,
            heal_history=state.heal_history,
        )
        raw = await agent._call_llm(task_class="reviewer_heal", prompt=rendered, json_mode=True)
        tokens = (len(rendered) + len(raw)) // 4
        data = loads_lenient(raw)
        rationales: list[str] = []
        if isinstance(data, dict):
            for patch in data.get("patches", []):
                file_path = patch.get("file_path")
                content = patch.get("new_content")
                if not file_path or content is None:
                    continue
                if is_test_file(file_path):
                    logger.warning("Rejecting heal patch to test file: %s", file_path)
                    continue
                patches[file_path] = content
                rationales.append(patch.get("rationale", file_path))
        heal.patches_applied = rationales
    except Exception as exc:  # noqa: BLE001 - heal failure is recorded, loop continues
        logger.warning("auto_heal generation failed on cycle %d: %s", cycle, exc)
        heal.outcome = "failed"

    if patches:
        written = await github.apply_patches(
            to_sandbox(state),
            patches,
            commit_message=f"fix: reviewer self-heal cycle {cycle}",
        )
        heal.files_patched = written
        heal.outcome = "improved" if written else "no_change"
    elif heal.outcome != "failed":
        heal.outcome = "no_change"

    logger.info("Heal cycle %d outcome=%s files=%s", cycle, heal.outcome, heal.files_patched)
    return {
        "heal_cycle": cycle,
        "heal_history": [*state.heal_history, heal],
        "current_failures": [],
        "total_llm_tokens_used": state.total_llm_tokens_used + tokens,
    }
