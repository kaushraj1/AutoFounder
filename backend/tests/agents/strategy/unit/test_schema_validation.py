import pytest
from pydantic import ValidationError

from app.agents.strategy.schema import LeanCanvas, MarketSize


def test_market_size_valid():
    m = MarketSize(
        tam_usd_bn=10.0, sam_usd_bn=5.0, som_usd_bn=1.0, cagr_pct=5.5, sources=["https://url.com"]
    )
    assert m.tam_usd_bn == 10.0
    assert m.sam_usd_bn == 5.0
    assert m.som_usd_bn == 1.0


def test_market_size_negative_invalid():
    with pytest.raises(ValidationError):
        MarketSize(tam_usd_bn=-1.0, sam_usd_bn=5.0, som_usd_bn=1.0, cagr_pct=5.5)


def test_market_size_hierarchy_violation():
    with pytest.raises(ValidationError, match="TAM >= SAM >= SOM constraint violated"):
        # TAM < SAM
        MarketSize(tam_usd_bn=5.0, sam_usd_bn=10.0, som_usd_bn=1.0, cagr_pct=5.5)


def test_lean_canvas_constraints():
    # Valid Lean Canvas
    valid_canvas = LeanCanvas(
        problem=["Problem 1"],
        customer_segments=["Segment X"],
        unique_value_proposition="Best AI builder",
        solution=["Solution A"],
        unfair_advantage="Secret Sauce",
        early_adopters="Early fans",
    )
    assert valid_canvas.unique_value_proposition == "Best AI builder"

    # Too many problems constraint (>3)
    with pytest.raises(ValidationError):
        LeanCanvas(
            problem=["P1", "P2", "P3", "P4"],
            customer_segments=["Segment X"],
            unique_value_proposition="Best AI builder",
            solution=["Solution A"],
            unfair_advantage="Secret Sauce",
            early_adopters="Early fans",
        )

    # Empty problems constraint (<1)
    with pytest.raises(ValidationError):
        LeanCanvas(
            problem=[],
            customer_segments=["Segment X"],
            unique_value_proposition="Best AI builder",
            solution=["Solution A"],
            unfair_advantage="Secret Sauce",
            early_adopters="Early fans",
        )
