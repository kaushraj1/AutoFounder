"""Tenant-scoped pgvector client.

Wraps the same AsyncSession used by RelationalClient (search_path already
set by RelationalClient.__aenter__) so vector queries run in the correct
tenant schema without a second round-trip.

The migration provisions memory_episodes with an IVFFlat index
(vector_cosine_ops, 100 lists).  The <=> operator performs cosine distance.

Usage:
    async with udal.relational() as db:
        vec = udal.vector()          # shares the same session
        results = await vec.search(
            collection="memory_episodes",
            query_vector=embedding,
            k=10,
            filters={"run_id": str(run_id)},
        )
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class VectorClient:
    """pgvector search and upsert over the tenant's schema."""

    def __init__(self, org_id: str, session: AsyncSession) -> None:
        self._org_id = org_id
        self._session = session

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        k: int = 10,
        filters: dict[str, str] | None = None,
    ) -> list[dict]:
        """Return up to k rows closest to query_vector (cosine distance).

        search_path is assumed to already be set by RelationalClient.__aenter__.
        filters are simple col=val equality checks added to WHERE.
        """
        vec_literal = "[" + ",".join(str(v) for v in query_vector) + "]"
        where_clauses = [f"embedding <=> '{vec_literal}'::vector IS NOT NULL"]
        params: dict[str, str] = {}
        if filters:
            for i, (col, val) in enumerate(filters.items()):
                placeholder = f"f{i}"
                where_clauses.append(f"{col} = :{placeholder}::uuid")
                params[placeholder] = val

        where_sql = " AND ".join(where_clauses)
        sql = text(f"""
            SELECT *, (embedding <=> '{vec_literal}'::vector) AS distance
            FROM {collection}
            WHERE {where_sql}
            ORDER BY distance
            LIMIT :k
        """)
        result = await self._session.execute(sql, {"k": k, **params})
        return [dict(row._mapping) for row in result]

    async def upsert(
        self,
        collection: str,
        embedding: list[float],
        payload: dict,
        id: str | None = None,
    ) -> str:
        """Insert (or replace by id) a vector row.  Returns the row's UUID."""
        vec_literal = "[" + ",".join(str(v) for v in embedding) + "]"
        col_names = ", ".join(payload.keys())
        placeholders = ", ".join(f":{k}" for k in payload.keys())

        if id:
            sql = text(f"""
                INSERT INTO {collection} (id, embedding, {col_names})
                VALUES (:_id::uuid, '{vec_literal}'::vector, {placeholders})
                ON CONFLICT (id) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        {", ".join(f"{k} = EXCLUDED.{k}" for k in payload.keys())}
                RETURNING id::text
            """)
            row = await self._session.execute(sql, {"_id": id, **payload})
        else:
            sql = text(f"""
                INSERT INTO {collection} (embedding, {col_names})
                VALUES ('{vec_literal}'::vector, {placeholders})
                RETURNING id::text
            """)
            row = await self._session.execute(sql, payload)

        return row.scalar_one()
