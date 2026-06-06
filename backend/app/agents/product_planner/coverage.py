"""Traceability / coverage scorer for Product Planner Agent.

Three sub-ratios are averaged into a single coverage score:
  persona_coverage  — personas with >=1 user story / total personas
  solution_coverage — canvas solution+problem items mapped to >=1 requirement
  story_anchoring   — user stories whose .persona resolves to a real persona name
"""

from __future__ import annotations

from app.agents.product_planner.schema import (
    PRD,
    Requirement,
    UserStory,
)
from app.agents.strategy.schema import BuyerPersona, LeanCanvas

COVERAGE_THRESHOLD = 0.70

_BANDS = [
    (0.85, "high"),
    (0.70, "medium"),
    (0.0, "low"),
]


def score_coverage(
    prd: PRD,
    requirements: list[Requirement],
    user_stories: list[UserStory],
    canvas: LeanCanvas,
    personas: list[BuyerPersona],
) -> float:
    """Return mean of three traceability sub-ratios. 0.0–1.0."""
    persona_names = {p.name.strip().lower() for p in personas}

    # 1. persona_coverage: fraction of personas that have at least one story
    story_persona_names = {s.persona.strip().lower() for s in user_stories}
    if persona_names:
        persona_cov = len(persona_names & story_persona_names) / len(persona_names)
    else:
        persona_cov = 0.0

    # 2. solution_coverage: canvas solution+problem items that appear in >=1 requirement
    canvas_items = [i.strip().lower() for i in (canvas.solution + canvas.problem)]
    if canvas_items and requirements:
        req_text = " ".join((r.statement + " " + (r.traces_to or "")).lower() for r in requirements)
        matched = sum(1 for item in canvas_items if item and item in req_text)
        solution_cov = matched / len(canvas_items)
    elif not canvas_items:
        solution_cov = 1.0  # nothing to trace — vacuously satisfied
    else:
        solution_cov = 0.0

    # 3. story_anchoring: stories whose .persona resolves to a real persona
    if user_stories:
        anchored = sum(1 for s in user_stories if s.persona.strip().lower() in persona_names)
        story_anchor = anchored / len(user_stories)
    else:
        story_anchor = 0.0

    total = (persona_cov + solution_cov + story_anchor) / 3
    return round(total, 4)


def confidence_band(score: float) -> str:
    for threshold, band in _BANDS:
        if score >= threshold:
            return band
    return "low"
