"""Per-agent baseline score storage.

Each golden set's last-known-good score is persisted as
``backend/tests/golden/<agent>/baseline.json`` next to its Promptfoo config,
so the regression gate (see ``app.eval.gate``) has something to compare
against without needing a database or external service.
"""

from __future__ import annotations

import json
from pathlib import Path

_BASELINE_FILENAME = "baseline.json"


def baseline_path(golden_set_dir: Path) -> Path:
    """Return the baseline file path for a golden set directory."""
    return golden_set_dir / _BASELINE_FILENAME


def load_baseline(golden_set_dir: Path) -> float | None:
    """Return the stored baseline score, or ``None`` if none has been recorded yet."""
    path = baseline_path(golden_set_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return float(data["score"])


def save_baseline(golden_set_dir: Path, score: float) -> None:
    """Persist ``score`` as the new baseline for a golden set directory."""
    path = baseline_path(golden_set_dir)
    path.write_text(json.dumps({"score": score}, indent=2) + "\n", encoding="utf-8")
