"""Unit tests — AWSPricingTool cost estimation math (AF-040).

Tests: static fallback, per-service estimators, PricingResult shape.
No LLM, no real AWS API calls.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.agents.architect.tools.aws_pricing import AWSPricingTool


@pytest.fixture()
def tool() -> AWSPricingTool:
    return AWSPricingTool()


class TestAWSPricingStaticFallback:
    def test_get_prices_returns_all_default_services(self, tool):
        with patch("httpx.Client") as mock_client:
            mock_client.side_effect = Exception("network unavailable")
            result = tool.get_prices()

        assert result.source == "static_fallback"
        assert "ecs_fargate" in result.data
        assert "s3" in result.data
        assert "elasticache_redis" in result.data
        assert result.error is not None

    def test_get_prices_filters_to_requested_services(self, tool):
        with patch("httpx.Client") as mock_client:
            mock_client.side_effect = Exception("offline")
            result = tool.get_prices(["ecs_fargate", "s3"])

        assert set(result.data.keys()) == {"ecs_fargate", "s3"}

    def test_unknown_service_returns_empty_dict(self, tool):
        with patch("httpx.Client") as mock_client:
            mock_client.side_effect = Exception("offline")
            result = tool.get_prices(["nonexistent_service"])

        assert result.data["nonexistent_service"] == {}


class TestECSCostEstimation:
    def test_ecs_cost_is_positive(self, tool):
        cost = tool.estimate_ecs_monthly(vcpus=0.25, memory_gb=0.5)
        assert cost > 0

    def test_ecs_cost_scales_with_vcpus(self, tool):
        cost_small = tool.estimate_ecs_monthly(vcpus=0.25, memory_gb=0.5)
        cost_large = tool.estimate_ecs_monthly(vcpus=2.0, memory_gb=4.0)
        assert cost_large > cost_small

    def test_ecs_cost_for_one_task_month(self, tool):
        # 0.25 vCPU, 0.5 GB, 730 hrs/month
        # = (0.25 * 0.04048 + 0.5 * 0.004445) * 730 = ~9.01
        cost = tool.estimate_ecs_monthly(vcpus=0.25, memory_gb=0.5, hours_per_month=730)
        assert 8.0 < cost < 12.0


class TestS3CostEstimation:
    def test_s3_cost_is_positive(self, tool):
        cost = tool.estimate_s3_monthly(storage_gb=10)
        assert cost > 0

    def test_s3_cost_scales_with_storage(self, tool):
        cost_small = tool.estimate_s3_monthly(storage_gb=1)
        cost_large = tool.estimate_s3_monthly(storage_gb=1000)
        assert cost_large > cost_small

    def test_s3_100gb_is_reasonable(self, tool):
        # 100 GB * $0.023 = $2.30 storage + minimal request costs
        cost = tool.estimate_s3_monthly(storage_gb=100, puts=10_000, gets=100_000)
        assert 2.0 < cost < 5.0


class TestRedisCostEstimation:
    def test_redis_micro_cost(self, tool):
        cost = tool.estimate_redis_monthly("cache.t3.micro")
        assert cost > 0

    def test_redis_large_costs_more(self, tool):
        micro = tool.estimate_redis_monthly("cache.t3.micro")
        large = tool.estimate_redis_monthly("cache.r6g.large")
        assert large > micro

    def test_redis_micro_monthly_is_reasonable(self, tool):
        # $0.017/hr * 730 hrs = ~$12.41
        cost = tool.estimate_redis_monthly("cache.t3.micro", hours_per_month=730)
        assert 10.0 < cost < 15.0
