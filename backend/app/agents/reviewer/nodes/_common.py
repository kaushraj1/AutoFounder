"""Shared helpers for Reviewer nodes."""

from __future__ import annotations

from app.agents.reviewer.schema import ReviewerState
from app.agents.reviewer.tools.sandbox import Sandbox


def to_sandbox(state: ReviewerState) -> Sandbox:
    """Reconstruct the ``Sandbox`` handle from primitive state fields."""
    return Sandbox(
        workdir=state.workdir or "",
        container_id=state.sandbox_container_id,
        image_tag=state.sandbox_image_tag,
        spinup_seconds=state.sandbox_spinup_seconds or 0.0,
    )
