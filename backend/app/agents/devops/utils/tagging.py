"""Build the mandatory resource tag set. Tag key 'Tenant' is preserved (Option B)."""
from __future__ import annotations

from uuid import UUID


def build_tags(organization_id: str, run_id: UUID | str, env: str = "staging") -> dict[str, str]:
    return {
        "Tenant": organization_id,
        "RunId": str(run_id),
        "Pillar": "5",
        "Env": env,
        "ManagedBy": "DevOpsAgent",
    }