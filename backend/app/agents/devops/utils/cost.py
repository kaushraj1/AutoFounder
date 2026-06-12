"""Estimate monthly AWS cost for a DevOpsState. Rough; refresh from AWS Pricing API later."""

from __future__ import annotations

from ..schema import ServiceManifest

# ap-south-1 USD as of 2026; revisit when AWS Pricing API integration lands.
_FARGATE_PER_VCPU_HOUR = 0.04048
_FARGATE_PER_GB_HOUR = 0.004445
_HOURS_PER_MONTH = 730

_NAT_GATEWAY_MONTH = 32.40
_ALB_MONTH = 22.50
_RDS_T4G_MICRO_MONTH = 15.00
_REDIS_T3_MICRO_MONTH = 13.00
_S3_BASELINE_MONTH = 1.00

# Baseline Fargate reservation per task: 0.5 vCPU / 1 GB.
_VCPU_PER_TASK = 0.5
_GB_PER_TASK = 1.0


def estimate_monthly_cost_usd(services: list[ServiceManifest]) -> float:
    per_task = _HOURS_PER_MONTH * (
        _VCPU_PER_TASK * _FARGATE_PER_VCPU_HOUR + _GB_PER_TASK * _FARGATE_PER_GB_HOUR
    )
    def _replicas(s: object) -> int:
        if isinstance(s, dict):
            return int(s.get("replicas_baseline", 0))
        return int(getattr(s, "replicas_baseline", 0))

    fargate = sum(_replicas(s) for s in services) * per_task
    return round(
        fargate
        + _NAT_GATEWAY_MONTH
        + _ALB_MONTH
        + _RDS_T4G_MICRO_MONTH
        + _REDIS_T3_MICRO_MONTH
        + _S3_BASELINE_MONTH,
        2,
    )
