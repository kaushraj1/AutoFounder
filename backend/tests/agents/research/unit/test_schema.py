"""T1 — schema bounds and validation."""
import pytest
from pydantic import ValidationError

from app.agents.research.schema import (
    Citation,
    ResearchFinding,
    ResearchInput,
    ResearchOutput,
    SourceResult,
)


def test_research_output_groundedness_bounds_valid() -> None:
    out = ResearchOutput(
        run_id="r1", organization_id="o1", domain="SaaS",
        findings=[], sources=[],
        groundedness_score=0.75, confidence="medium",
    )
    assert out.groundedness_score == 0.75


def test_research_output_groundedness_below_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        ResearchOutput(
            run_id="r1", organization_id="o1", domain="SaaS",
            findings=[], sources=[],
            groundedness_score=-0.1, confidence="low",
        )


def test_research_output_groundedness_above_one_rejected() -> None:
    with pytest.raises(ValidationError):
        ResearchOutput(
            run_id="r1", organization_id="o1", domain="SaaS",
            findings=[], sources=[],
            groundedness_score=1.1, confidence="high",
        )


def test_research_input_defaults() -> None:
    ri = ResearchInput(
        run_id="r1", organization_id="o1",
        idea_normalised="AI tool", domain="SaaS",
    )
    assert "tavily" in ri.sources
    assert ri.queries == []


def test_source_result_ok_false() -> None:
    sr = SourceResult(source="g2", ok=False, error="timeout")
    assert not sr.ok
    assert sr.items == []


def test_citation_optional_fields() -> None:
    c = Citation(source="tavily", snippet="some text")
    assert c.url is None
    assert c.title is None


def test_research_finding_empty_citations() -> None:
    f = ResearchFinding(claim="Something happened")
    assert f.citations == []
