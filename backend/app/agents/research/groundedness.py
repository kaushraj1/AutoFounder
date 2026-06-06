"""Citation groundedness scorer for Research Agent."""
from __future__ import annotations

from app.agents.research.schema import Citation, ResearchFinding

GROUNDEDNESS_THRESHOLD = 0.70

_BANDS = [
    (0.85, "high"),
    (0.70, "medium"),
    (0.0, "low"),
]


def score_groundedness(findings: list[ResearchFinding], sources: list[Citation]) -> float:
    """Ratio of findings with at least one valid citation index. Returns 0.0–1.0."""
    if not findings:
        return 0.0
    valid_indices = set(range(len(sources)))
    grounded = sum(
        1 for f in findings if any(c in valid_indices for c in f.citations)
    )
    return round(grounded / len(findings), 4)


def confidence_band(score: float) -> str:
    for threshold, band in _BANDS:
        if score >= threshold:
            return band
    return "low"
