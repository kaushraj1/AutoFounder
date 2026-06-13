"""SLA timer helpers for the Marketing Agent (AF-044)."""

from __future__ import annotations

import time


class SLATimer:
    """Tracks elapsed time for SLA budget enforcement.

    Usage:
        timer = SLATimer(budget_seconds=2700)
        timer.start()
        # ... do work ...
        timer.assert_within_budget("node_name")  # raises if over budget
    """

    def __init__(self, budget_seconds: int = 2700) -> None:
        self.budget_seconds = budget_seconds
        self._start: float | None = None

    def start(self) -> None:
        self._start = time.monotonic()

    @property
    def elapsed(self) -> float:
        if self._start is None:
            return 0.0
        return time.monotonic() - self._start

    @property
    def remaining(self) -> float:
        return max(0.0, self.budget_seconds - self.elapsed)

    @property
    def over_budget(self) -> bool:
        return self.elapsed > self.budget_seconds

    def assert_within_budget(self, label: str = "") -> None:
        if self.over_budget:
            raise TimeoutError(
                f"SLA exceeded ({self.elapsed:.0f}s > {self.budget_seconds}s)"
                + (f" at {label}" if label else "")
            )
