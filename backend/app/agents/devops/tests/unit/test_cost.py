from app.agents.devops.schema import ServiceManifest
from app.agents.devops.utils.cost import estimate_monthly_cost_usd


def test_estimate_monthly_cost_positive() -> None:
    services = [
        ServiceManifest(name="api", image_uri="img", port=8000, replicas_baseline=2),
        ServiceManifest(name="web", image_uri="img", port=3000, replicas_baseline=1),
    ]
    assert estimate_monthly_cost_usd(services) > 0


def test_more_replicas_increases_cost() -> None:
    low = estimate_monthly_cost_usd(
        [ServiceManifest(name="api", image_uri="img", port=8000, replicas_baseline=1)]
    )
    high = estimate_monthly_cost_usd(
        [ServiceManifest(name="api", image_uri="img", port=8000, replicas_baseline=4)]
    )
    assert high > low
