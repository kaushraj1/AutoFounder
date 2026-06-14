"""Architect tool registry (AF-040 / AF-047 catalog + BaseAgent DI slot).

The Architect's tools are strongly-typed functions invoked directly by nodes
(``tools/*.py``), so dynamic ``call()`` dispatch is intentionally unsupported —
this registry exists to (a) satisfy ``BaseAgent``'s ``tool_registry`` dependency
and (b) declare the tool catalog the platform Tool Registry (AF-047) registers.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import ToolRegistryProtocol

# AF-047 tool catalog: name → scope/auth/cost/rate-limit metadata.
ARCHITECT_TOOLS: dict[str, dict[str, str]] = {
    "mermaid_validate": {
        "scope": "architect",
        "auth": "none",
        "cost": "free",
        "description": "Validate Mermaid erDiagram syntax and extract entity metadata",
    },
    "openapi_validate": {
        "scope": "architect",
        "auth": "none",
        "cost": "free",
        "description": "Validate OpenAPI 3.x specifications against the JSON schema",
    },
    "aws_pricing": {
        "scope": "architect",
        "auth": "none",
        "cost": "free",
        "description": "Fetch live AWS pricing data; falls back to static table on API error",
    },
}


class ArchitectToolRegistry(ToolRegistryProtocol):
    """Catalog registry for the Architect agent (typed tools are called directly).

    Architect tools (mermaid_validate, openapi_validate, aws_pricing) are
    invoked as typed Python objects by the graph nodes — not via the generic
    ``call()`` interface. This class satisfies the BaseAgent DI requirement
    and exposes the AF-047 catalog for platform registration.
    """

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Raise NotImplementedError — Architect tools are invoked directly by nodes.

        See app/agents/architect/tools/ for the typed tool implementations.
        """
        raise NotImplementedError(
            f"Architect tools are typed and invoked directly by nodes, not via "
            f"dynamic call() (attempted: '{tool_name}'). "
            f"See app/agents/architect/tools/."
        )

    @staticmethod
    def registered_tools() -> dict[str, dict[str, str]]:
        """Return the AF-047 tool catalog for platform registration."""
        return dict(ARCHITECT_TOOLS)
