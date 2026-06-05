"""Graph database client — stub pending architecture decision.

Per stack.md § Open Decisions:
  "Graph DB | Neo4j AuraDB vs Amazon Neptune | Benchmark on competitor ↔
   market ↔ persona queries"

This module will be replaced when the decision resolves.  Until then every
call raises NotImplementedError so callers know the surface exists but is
not yet implemented, rather than silently failing.
"""

from __future__ import annotations


class GraphClient:
    """Placeholder for future graph DB access (Neo4j AuraDB or Amazon Neptune)."""

    def query(self, cypher: str, **params: object) -> list[dict]:
        raise NotImplementedError(
            "Graph DB not yet provisioned.  "
            "Open decision: Neo4j AuraDB vs Amazon Neptune.  "
            "See .claude/specs/stack.md § Open Decisions."
        )

    def upsert_node(self, label: str, properties: dict) -> str:
        raise NotImplementedError(
            "Graph DB not yet provisioned.  See stack.md § Open Decisions."
        )

    def upsert_edge(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict | None = None,
    ) -> None:
        raise NotImplementedError(
            "Graph DB not yet provisioned.  See stack.md § Open Decisions."
        )
