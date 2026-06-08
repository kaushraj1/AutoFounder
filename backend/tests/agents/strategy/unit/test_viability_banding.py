from app.agents.strategy.schema import ViabilityBand, ViabilityScore


def test_viability_banding():
    breakdown = {
        "market_size": 10,
        "competition": 10,
        "trend": 10,
        "monetisation": 10,
        "feasibility": 10,
    }

    # Total >= 75 -> STRONG
    s1 = ViabilityScore(total=85, breakdown=breakdown)
    assert s1.band == ViabilityBand.STRONG

    s2 = ViabilityScore(total=75, breakdown=breakdown)
    assert s2.band == ViabilityBand.STRONG

    # Total >= 50 and < 75 -> MODERATE
    s3 = ViabilityScore(total=74, breakdown=breakdown)
    assert s3.band == ViabilityBand.MODERATE

    s4 = ViabilityScore(total=50, breakdown=breakdown)
    assert s4.band == ViabilityBand.MODERATE

    # Total >= 25 and < 50 -> WEAK
    s5 = ViabilityScore(total=49, breakdown=breakdown)
    assert s5.band == ViabilityBand.WEAK

    s6 = ViabilityScore(total=25, breakdown=breakdown)
    assert s6.band == ViabilityBand.WEAK

    # Total < 25 -> REJECT
    s7 = ViabilityScore(total=24, breakdown=breakdown)
    assert s7.band == ViabilityBand.REJECT

    s8 = ViabilityScore(total=0, breakdown=breakdown)
    assert s8.band == ViabilityBand.REJECT
