"""T1 — schema bounds and validation."""
import pytest
from pydantic import ValidationError

from app.agents.product_planner.schema import (
    PRD,
    Milestone,
    ProductPlannerOutput,
    Requirement,
    UserStory,
)


def test_output_coverage_bounds_valid() -> None:
    out = ProductPlannerOutput(
        run_id="r1", organization_id="o1", domain="SaaS",
        prd=PRD(
            title="T", overview="O", problem_statement="P",
            goals=["g"], target_users=["u"],
        ),
        requirements=[], user_stories=[], roadmap=[],
        prd_markdown="", coverage_score=0.8, confidence="high",
    )
    assert out.coverage_score == 0.8


def test_output_coverage_below_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        ProductPlannerOutput(
            run_id="r1", organization_id="o1", domain="SaaS",
            prd=PRD(
                title="T", overview="O", problem_statement="P",
                goals=["g"], target_users=["u"],
            ),
            requirements=[], user_stories=[], roadmap=[],
            prd_markdown="", coverage_score=-0.1, confidence="low",
        )


def test_output_coverage_above_one_rejected() -> None:
    with pytest.raises(ValidationError):
        ProductPlannerOutput(
            run_id="r1", organization_id="o1", domain="SaaS",
            prd=PRD(
                title="T", overview="O", problem_statement="P",
                goals=["g"], target_users=["u"],
            ),
            requirements=[], user_stories=[], roadmap=[],
            prd_markdown="", coverage_score=1.1, confidence="high",
        )


def test_prd_empty_goals_rejected() -> None:
    with pytest.raises(ValidationError):
        PRD(title="T", overview="O", problem_statement="P", goals=[], target_users=["u"])


def test_prd_empty_target_users_rejected() -> None:
    with pytest.raises(ValidationError):
        PRD(title="T", overview="O", problem_statement="P", goals=["g"], target_users=[])


def test_user_story_empty_acceptance_criteria_rejected() -> None:
    with pytest.raises(ValidationError):
        UserStory(
            id="US-001", persona="Alice", role="PM",
            want="do something", benefit="to achieve x",
            acceptance_criteria=[], priority="must",
        )


def test_requirement_defaults() -> None:
    r = Requirement(
        id="FR-001", kind="functional",
        statement="System shall do X.", priority="must",
        traces_to="canvas item",
    )
    assert r.rationale is None
    assert r.traces_to == "canvas item"


def test_milestone_optional_weeks() -> None:
    m = Milestone(phase="MVP", title="Launch", objective="Ship it.")
    assert m.target_weeks is None
    assert m.epics == []
