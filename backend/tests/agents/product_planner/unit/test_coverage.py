"""T7-T9 — traceability/coverage scorer."""

from app.agents.product_planner.coverage import (
    COVERAGE_THRESHOLD,
    confidence_band,
    score_coverage,
)
from app.agents.product_planner.schema import PRD, Requirement, UserStory
from app.agents.strategy.schema import BuyerPersona, LeanCanvas


def _canvas(**overrides: object) -> LeanCanvas:
    defaults = dict(
        problem=["Remote teams waste hours on scheduling"],
        customer_segments=["Engineering managers"],
        unique_value_proposition="Zero-effort scheduling",
        solution=["Smart calendar integration", "Timezone auto-detection"],
        unfair_advantage="Algo",
        early_adopters="Distributed startups",
    )
    return LeanCanvas(**{**defaults, **overrides})  # type: ignore[arg-type]


def _persona(name: str) -> BuyerPersona:
    return BuyerPersona(
        name=name, role="PM", company_size="10-50",
        pain_points=["scheduling pain"], goals=["save time"],
    )


def _prd(*target_users: str) -> PRD:
    return PRD(
        title="T", overview="O", problem_statement="Remote teams waste hours on scheduling",
        goals=["g"], target_users=list(target_users),
        scope_in=["Smart calendar integration"],
    )


def _req(traces_to: str = "Smart calendar integration") -> Requirement:
    return Requirement(
        id="FR-001", kind="functional", statement="Sync calendars.",
        priority="must", traces_to=traces_to,
    )


def _story(persona: str) -> UserStory:
    return UserStory(
        id="US-001", persona=persona, role="PM",
        want="sync calendar", benefit="save time",
        acceptance_criteria=["It works"], priority="must",
    )


def test_full_traceability_high_confidence() -> None:
    canvas = _canvas()
    personas = [_persona("Alex")]
    prd = _prd("Alex")
    # Cover all 3 canvas items: both solution items + the problem item
    reqs = [
        _req("Smart calendar integration"),
        _req("Timezone auto-detection"),
        _req("Remote teams waste hours on scheduling"),
    ]
    stories = [_story("Alex")]
    score = score_coverage(prd, reqs, stories, canvas, personas)
    assert score >= 0.85
    assert confidence_band(score) == "high"


def test_persona_with_no_story_lowers_coverage() -> None:
    canvas = _canvas()
    personas = [_persona("Alex"), _persona("Bob")]  # Bob has no story
    prd = _prd("Alex", "Bob")
    reqs = [_req()]
    stories = [_story("Alex")]  # only Alex
    score = score_coverage(prd, reqs, stories, canvas, personas)
    assert score < 1.0


def test_no_requirements_lowers_solution_coverage() -> None:
    canvas = _canvas()
    personas = [_persona("Alex")]
    prd = _prd("Alex")
    score = score_coverage(prd, [], [], canvas, personas)
    assert score < COVERAGE_THRESHOLD


def test_unanchored_story_lowers_coverage() -> None:
    canvas = _canvas()
    personas = [_persona("Alex")]
    prd = _prd("Alex")
    reqs = [_req()]
    stories = [_story("Unknown Person")]  # persona not in list
    score = score_coverage(prd, reqs, stories, canvas, personas)
    assert score < 1.0


def test_empty_personas_returns_zero_persona_coverage() -> None:
    canvas = _canvas()
    prd = _prd("Alex")
    score = score_coverage(prd, [_req()], [_story("Alex")], canvas, [])
    assert score < 1.0  # persona_coverage=0 pulls mean down


def test_coverage_band_high() -> None:
    assert confidence_band(0.90) == "high"


def test_coverage_band_medium() -> None:
    assert confidence_band(0.75) == "medium"


def test_coverage_band_low() -> None:
    assert confidence_band(0.50) == "low"
