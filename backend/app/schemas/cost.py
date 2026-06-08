"""Cost schemas for FinOps cost telemetry."""

from pydantic import BaseModel


class CostRead(BaseModel):
    total_cost_usd: float
