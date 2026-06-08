"""T9 — groundedness scorer and confidence banding."""

from app.agents.research.groundedness import (
    GROUNDEDNESS_THRESHOLD,
    confidence_band,
    score_groundedness,
)
from app.agents.research.schema import Citation, ResearchFinding


def _sources(n: int) -> list[Citation]:
    return [Citation(source="tavily", snippet=f"source {i}") for i in range(n)]


def test_all_findings_cited() -> None:
    sources = _sources(3)
    findings = [
        ResearchFinding(claim="A", citations=[0]),
        ResearchFinding(claim="B", citations=[1, 2]),
    ]
    score = score_groundedness(findings, sources)
    assert score == 1.0


def test_no_findings_cited() -> None:
    sources = _sources(3)
    findings = [
        ResearchFinding(claim="A", citations=[]),
        ResearchFinding(claim="B", citations=[]),
    ]
    score = score_groundedness(findings, sources)
    assert score == 0.0


def test_partial_cited() -> None:
    sources = _sources(3)
    findings = [
        ResearchFinding(claim="A", citations=[0]),
        ResearchFinding(claim="B", citations=[]),
        ResearchFinding(claim="C", citations=[]),
        ResearchFinding(claim="D", citations=[2]),
    ]
    score = score_groundedness(findings, sources)
    assert score == 0.5


def test_out_of_range_citation_not_counted() -> None:
    sources = _sources(2)
    findings = [ResearchFinding(claim="A", citations=[99])]
    score = score_groundedness(findings, sources)
    assert score == 0.0


def test_empty_findings_returns_zero() -> None:
    assert score_groundedness([], _sources(3)) == 0.0


def test_confidence_high() -> None:
    assert confidence_band(0.9) == "high"
    assert confidence_band(0.85) == "high"


def test_confidence_medium() -> None:
    assert confidence_band(0.75) == "medium"
    assert confidence_band(GROUNDEDNESS_THRESHOLD) == "medium"


def test_confidence_low() -> None:
    assert confidence_band(0.5) == "low"
    assert confidence_band(0.0) == "low"
