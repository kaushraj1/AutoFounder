"""AF-049: Hybrid BM25 + ANN RAG pipeline.

Retrieval pipeline used by agents that need to ground LLM calls in
organisation-scoped knowledge. Executes five stages:

1. **Query rewrite** — LLM expands the raw query for better recall.
2. **Hybrid retrieve** — BM25 full-text (Supabase ``ts_rank``) + pgvector ANN
   search run in parallel; results are merged.
3. **Rerank** — Reciprocal Rank Fusion (RRF) merges BM25 and ANN rankings.
4. **Context compression** — Trim chunks to a configurable token budget
   (rough estimate: 4 characters per token).
5. **Citation check** — Populate ``citations`` list from retrieved chunk IDs.

Usage::

    rag = RAGPipeline(udal=udal, llm_router=llm_router)
    result = await rag.retrieve("What is the target market?", org_id="org-abc")
    print(result.context_str)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("app.rag.pipeline")

_CHARS_PER_TOKEN = 4  # rough approximation used for budget trimming


@dataclass
class RAGResult:
    """Output of a full RAG pipeline run."""

    chunks: list[dict[str, Any]]
    """All retrieved chunks (BM25 + ANN, before reranking)."""

    reranked: list[dict[str, Any]]
    """Chunks ordered by RRF fusion score (highest first)."""

    context_str: str
    """Concatenated, compressed context ready to inject into a prompt."""

    citations: list[str]
    """Chunk IDs referenced in ``context_str``."""

    token_count: int
    """Estimated token count of ``context_str``."""


class RAGPipeline:
    """Hybrid retrieval + reranking + compression pipeline.

    Combines BM25 keyword search (Supabase full-text) with pgvector ANN search,
    then applies Reciprocal Rank Fusion to produce a single ranked list.

    Args:
        udal: Universal Data Access Layer instance. Must expose
            ``udal.db`` for raw SQL (BM25) and ``udal.vector`` for ANN search.
            Pass ``None`` in tests — only ``_rewrite_query`` will work.
        llm_router: LLMRouterProtocol-compatible object used for query rewriting.
    """

    def __init__(self, udal: Any, llm_router: Any) -> None:
        self.udal = udal
        self.llm = llm_router

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 10,
        org_id: str,
        max_tokens: int = 4000,
    ) -> RAGResult:
        """Run the full RAG pipeline and return a structured result.

        Stages: rewrite → (BM25 + ANN in parallel) → rerank → compress → cite.

        Args:
            query: Raw user/agent query string.
            top_k: Number of results to fetch from each retrieval method.
            org_id: Organisation ID used to scope all knowledge base queries.
            max_tokens: Maximum token budget for ``context_str``.

        Returns:
            :class:`RAGResult` with ranked chunks, compressed context, and citations.
        """
        # Stage 1: query rewrite
        expanded_query = await self._rewrite_query(query)

        # Stage 2: hybrid retrieval (concurrent)
        bm25_results, ann_results = await asyncio.gather(
            self._bm25_search(expanded_query, org_id=org_id, k=top_k),
            self._ann_search(expanded_query, org_id=org_id, k=top_k),
        )

        all_chunks = bm25_results + ann_results

        # Stage 3: rerank via RRF
        reranked = await self._rerank(expanded_query, all_chunks)

        # Stage 4: compress to token budget
        context_str = self._compress(reranked, max_tokens=max_tokens)

        # Stage 5: citations — collect chunk IDs present in context_str
        citations = self._extract_citations(reranked, context_str)

        token_count = len(context_str) // _CHARS_PER_TOKEN

        logger.debug(
            "RAGPipeline: org=%s query_len=%d chunks=%d reranked=%d tokens=%d citations=%d",
            org_id,
            len(query),
            len(all_chunks),
            len(reranked),
            token_count,
            len(citations),
        )

        return RAGResult(
            chunks=all_chunks,
            reranked=reranked,
            context_str=context_str,
            citations=citations,
            token_count=token_count,
        )

    async def _rewrite_query(self, query: str) -> str:
        """LLM-based query expansion for better recall.

        Asks the LLM to generate a semantically enriched version of the query
        that includes synonyms and related terms. Falls back to the original
        query on any error.

        Args:
            query: Original query string.

        Returns:
            Expanded query string.
        """
        prompt = (
            "You are a query expansion assistant. Rewrite the following search query "
            "to improve recall by adding related terms, synonyms, and contextual keywords. "
            "Return ONLY the expanded query string — no explanation.\n\n"
            f"Original query: {query}"
        )
        try:
            expanded = await self.llm.complete(task_class="rag_rewrite", prompt=prompt)
            expanded = expanded.strip()
            return expanded if expanded else query
        except Exception as exc:
            logger.warning("RAGPipeline: query rewrite failed (%s) — using original", exc)
            return query

    async def _bm25_search(
        self, query: str, *, org_id: str, k: int
    ) -> list[dict[str, Any]]:
        """Keyword search via Supabase full-text search (``ts_rank``).

        Executes a ``to_tsquery`` / ``ts_rank`` query against the
        ``knowledge_chunks`` table, scoped to ``org_id``.

        Args:
            query: Search query (may be expanded).
            org_id: Organisation scope.
            k: Maximum number of results to return.

        Returns:
            List of chunk dicts with keys ``id``, ``content``, ``bm25_score``.
        """
        if self.udal is None:
            logger.debug("RAGPipeline/_bm25_search: udal=None, returning empty results")
            return []

        try:
            sql = (
                "SELECT id, content, "
                "ts_rank(to_tsvector('english', content), "
                "plainto_tsquery('english', $1)) AS bm25_score "
                "FROM knowledge_chunks "
                "WHERE organization_id = $2 "
                "AND to_tsvector('english', content) @@ plainto_tsquery('english', $1) "
                "ORDER BY bm25_score DESC LIMIT $3"
            )
            rows = await self.udal.db.fetch(sql, query, org_id, k)
            return [
                {
                    "id": row["id"],
                    "content": row["content"],
                    "bm25_score": float(row["bm25_score"]),
                    "ann_score": 0.0,
                    "source": "bm25",
                }
                for row in rows
            ]
        except Exception as exc:
            logger.warning("RAGPipeline/_bm25_search: failed (%s)", exc)
            return []

    async def _ann_search(
        self, query: str, *, org_id: str, k: int
    ) -> list[dict[str, Any]]:
        """pgvector ANN search via UDAL vector client.

        Embeds the query and performs a cosine-distance nearest-neighbour
        search against ``knowledge_chunks.embedding``.

        Args:
            query: Search query (may be expanded).
            org_id: Organisation scope.
            k: Maximum number of results to return.

        Returns:
            List of chunk dicts with keys ``id``, ``content``, ``ann_score``.
        """
        if self.udal is None:
            logger.debug("RAGPipeline/_ann_search: udal=None, returning empty results")
            return []

        try:
            results = await self.udal.vector.search(
                query=query, org_id=org_id, top_k=k
            )
            return [
                {
                    "id": r.get("id"),
                    "content": r.get("content", ""),
                    "ann_score": float(r.get("score", 0.0)),
                    "bm25_score": 0.0,
                    "source": "ann",
                }
                for r in results
            ]
        except Exception as exc:
            logger.warning("RAGPipeline/_ann_search: failed (%s)", exc)
            return []

    async def _rerank(
        self, query: str, chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Score fusion via Reciprocal Rank Fusion (RRF) of BM25 + ANN scores.

        RRF formula: ``score(d) = Σ 1 / (k + rank(d))`` where ``k=60`` is the
        smoothing constant. Deduplicates chunks by ``id`` before scoring.

        Args:
            query: Expanded query (kept for interface consistency; not used by RRF).
            chunks: Combined BM25 + ANN results.

        Returns:
            Deduplicated and sorted chunk list (highest RRF score first), each
            chunk augmented with ``rrf_score``.
        """
        k = 60  # RRF smoothing constant

        # Deduplicate by chunk id (ANN result takes precedence for content)
        seen: dict[str, dict[str, Any]] = {}
        for chunk in chunks:
            chunk_id = chunk.get("id") or chunk.get("content", "")[:32]
            if chunk_id not in seen:
                seen[chunk_id] = {**chunk, "rrf_score": 0.0}
            else:
                # Merge scores from different sources
                existing = seen[chunk_id]
                existing["bm25_score"] = max(
                    existing.get("bm25_score", 0.0), chunk.get("bm25_score", 0.0)
                )
                existing["ann_score"] = max(
                    existing.get("ann_score", 0.0), chunk.get("ann_score", 0.0)
                )

        unique = list(seen.values())

        # Rank by BM25 score
        bm25_ranked = sorted(unique, key=lambda c: c.get("bm25_score", 0.0), reverse=True)
        # Rank by ANN score
        ann_ranked = sorted(unique, key=lambda c: c.get("ann_score", 0.0), reverse=True)

        # Compute RRF scores
        rrf: dict[str, float] = {}
        for rank, chunk in enumerate(bm25_ranked, start=1):
            cid = chunk.get("id") or chunk.get("content", "")[:32]
            rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (k + rank)
        for rank, chunk in enumerate(ann_ranked, start=1):
            cid = chunk.get("id") or chunk.get("content", "")[:32]
            rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (k + rank)

        for chunk in unique:
            cid = chunk.get("id") or chunk.get("content", "")[:32]
            chunk["rrf_score"] = rrf.get(cid, 0.0)

        return sorted(unique, key=lambda c: c.get("rrf_score", 0.0), reverse=True)

    def _compress(
        self, chunks: list[dict[str, Any]], *, max_tokens: int = 4000
    ) -> str:
        """Trim chunks to fit within the token budget.

        Concatenates chunk content (highest RRF score first) until the
        estimated token count exceeds ``max_tokens``.

        Args:
            chunks: Reranked chunk list.
            max_tokens: Maximum number of tokens in the output string.

        Returns:
            Concatenated context string ready for prompt injection.
        """
        parts: list[str] = []
        char_budget = max_tokens * _CHARS_PER_TOKEN
        used = 0

        for chunk in chunks:
            content = chunk.get("content", "")
            if not content:
                continue
            chunk_chars = len(content)
            if used + chunk_chars > char_budget:
                # Include partial content to fill the budget
                remaining = char_budget - used
                if remaining > 0:
                    parts.append(content[:remaining])
                break
            parts.append(content)
            used += chunk_chars

        return "\n\n---\n\n".join(parts)

    def _extract_citations(
        self, reranked: list[dict[str, Any]], context_str: str
    ) -> list[str]:
        """Return the IDs of chunks whose content appears in ``context_str``.

        Args:
            reranked: Reranked chunk list (used to map content → ID).
            context_str: Compressed context string.

        Returns:
            List of chunk IDs referenced in the context.
        """
        citations: list[str] = []
        for chunk in reranked:
            content = chunk.get("content", "")
            chunk_id = chunk.get("id")
            if content and chunk_id and content[:50] in context_str:
                citations.append(str(chunk_id))
        return citations
