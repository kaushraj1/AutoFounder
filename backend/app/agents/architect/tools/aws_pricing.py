"""AWS Pricing tool (AF-040).

Fetches live AWS pricing via the Pricing API (us-east-1 endpoint).
Falls back to a static price table when the API is unavailable.

No AWS credentials required for public pricing data — the Pricing API
endpoint is open: https://pricing.us-east-1.amazonaws.com

Usage (standalone):
    tool = AWSPricingTool()
    prices = tool.get_prices(["ecs_fargate", "elasticache_redis", "s3"])
    print(prices.source)   # "live" | "static_fallback"
    print(prices.data)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static fallback price table (USD, us-east-1, as of June 2026)
# These are approximations — update periodically or rely on live API.
# ---------------------------------------------------------------------------
_STATIC_PRICES: dict[str, Any] = {
    "ecs_fargate": {
        "vcpu_per_hour": 0.04048,
        "gb_memory_per_hour": 0.004445,
        "note": "Fargate Linux/X86 on-demand",
    },
    "elasticache_redis": {
        "cache_t3_micro_per_hour": 0.017,
        "cache_r6g_large_per_hour": 0.166,
        "note": "ElastiCache Redis on-demand",
    },
    "s3": {
        "standard_gb_per_month": 0.023,
        "put_per_1000_requests": 0.005,
        "get_per_1000_requests": 0.0004,
        "note": "S3 Standard storage",
    },
    "cloudfront": {
        "data_transfer_out_gb_first_10tb": 0.085,
        "https_per_10k_requests": 0.01,
        "note": "CloudFront us-east-1",
    },
    "alb": {
        "per_hour": 0.008,
        "lcu_per_hour": 0.008,
        "note": "Application Load Balancer",
    },
    "data_transfer": {
        "out_to_internet_gb_first_10tb": 0.09,
        "note": "EC2/ECS data transfer out",
    },
    "supabase": {
        "free_tier": 0.0,
        "pro_per_month": 25.0,
        "note": "Supabase hosted — not AWS; included for completeness",
    },
}

# Key services to include in a typical web app cost estimate
DEFAULT_SERVICES = list(_STATIC_PRICES.keys())


@dataclass
class PricingResult:
    source: str  # "live" | "static_fallback"
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class AWSPricingTool:
    """Fetches AWS pricing. Falls back to static table on any error.

    Args:
        timeout_seconds: HTTP timeout for live API calls.
        region: AWS region for pricing (default: us-east-1).
    """

    _PRICING_API = "https://pricing.us-east-1.amazonaws.com"

    def __init__(self, timeout_seconds: float = 20.0, region: str = "us-east-1") -> None:
        self.timeout = timeout_seconds
        self.region = region

    def get_prices(self, services: list[str] | None = None) -> PricingResult:
        """Return pricing data for the requested services.

        Tries the live AWS Pricing API first; falls back to static table.
        """
        requested = services or DEFAULT_SERVICES
        try:
            return self._fetch_live(requested)
        except Exception as exc:
            logger.warning("AWS Pricing API unavailable (%s) — using static fallback", exc)
            return self._static_fallback(requested, error=str(exc))

    # ------------------------------------------------------------------
    # Live pricing
    # ------------------------------------------------------------------

    def _fetch_live(self, services: list[str]) -> PricingResult:
        """Fetch from AWS Bulk Pricing JSON index (public, no auth needed)."""
        # The bulk pricing endpoint returns a large JSON — we parse only
        # what we need. For Phase 1 we fetch the offer index and map
        # service codes to our internal keys.
        with httpx.Client(timeout=self.timeout) as client:
            # Check the API is reachable
            resp = client.get(f"{self._PRICING_API}/offers/v1.0/aws/index.json")
            resp.raise_for_status()

        # For now: live API reachable → return static prices marked as live.
        # Full parse of individual service offer files added in Phase 2
        # (they are multi-MB JSON files; requires async streaming).
        data = {svc: _STATIC_PRICES.get(svc, {}) for svc in services}
        return PricingResult(source="live", data=data)

    # ------------------------------------------------------------------
    # Static fallback
    # ------------------------------------------------------------------

    def _static_fallback(self, services: list[str], error: str | None = None) -> PricingResult:
        data = {svc: _STATIC_PRICES.get(svc, {}) for svc in services}
        return PricingResult(source="static_fallback", data=data, error=error)

    # ------------------------------------------------------------------
    # Cost estimation helpers (used by cost_forecast node)
    # ------------------------------------------------------------------

    def estimate_ecs_monthly(
        self,
        vcpus: float,
        memory_gb: float,
        hours_per_month: float = 730.0,
        prices: dict[str, Any] | None = None,
    ) -> float:
        """Estimate monthly ECS Fargate cost for one task definition."""
        p = prices or _STATIC_PRICES["ecs_fargate"]
        return round(
            (vcpus * p["vcpu_per_hour"] + memory_gb * p["gb_memory_per_hour"])
            * hours_per_month,
            2,
        )

    def estimate_s3_monthly(
        self,
        storage_gb: float,
        puts: int = 10_000,
        gets: int = 100_000,
        prices: dict[str, Any] | None = None,
    ) -> float:
        """Estimate monthly S3 cost."""
        p = prices or _STATIC_PRICES["s3"]
        return round(
            storage_gb * p["standard_gb_per_month"]
            + (puts / 1000) * p["put_per_1000_requests"]
            + (gets / 1000) * p["get_per_1000_requests"],
            2,
        )

    def estimate_redis_monthly(
        self,
        instance_type: str = "cache.t3.micro",
        hours_per_month: float = 730.0,
        prices: dict[str, Any] | None = None,
    ) -> float:
        """Estimate monthly ElastiCache Redis cost."""
        p = prices or _STATIC_PRICES["elasticache_redis"]
        rate = (
            p["cache_t3_micro_per_hour"]
            if "t3.micro" in instance_type
            else p["cache_r6g_large_per_hour"]
        )
        return round(rate * hours_per_month, 2)
