# AF-038 — Research Agent (Pillar 1) — Implementation Plan

> **Task:** Research Agent (Pillar 1) — Tavily + SerpAPI + Crunchbase + G2 + SimilarWeb tool fan-out, multi-source synthesis, citation groundedness check.
> **Owner:** Somesh Chitranshi (Pillar 1)
> **Branch:** `feature/research-agent`
> **Depends on:** AF-036 BaseAgent ✅ (done), AF-027 UDAL ✅ (done)
> **Soft-blocked by:** AF-047 Tool Registry 🟡, AF-048 Prompt Registry 🟡, AF-049 LLM Router 🟡 → satisfied via Protocols (contract-first).
> **Priority:** P0 — reused by Strategy Agent (AF-037) and future pillars.
> **File(s):** `backend/app/agents/research/`
> **Ground truth:** `.claude/developer-plans/02-somesh-pillar-1-strategy-research-plan.md`, `.claude/specs/agents.md` §7.4 + §10.2 (RAG groundedness), `.claude/TASKS.md` AF-038.

---

## 1. Why this task matters

The Research Agent is the **tool-fan-out specialist** of Pillar 1. The Strategy Agent's research nodes (`market_sizing`, `competitor_discovery`, `persona_generation`, `keyword_intent_mine`) all delegate external data gathering to it. It is also reusable by Marketing (Pillar 6) later. Its single job: take a domain + normalised idea, fan out across 5 external sources, synthesise the results into one **grounded, cited** context, and **prove** the synthesis is source-backed (citation groundedness check). Everything downstream (Lean Canvas, viability score) inherits its groundedness — hallucinated market data here poisons the whole validation.

---

## 2. Current state (GAP ANALYSIS)

### What exists today ✅
- `backend/app/agents/base.py` — **AF-036 `BaseAgent[TIn, TOut]`** is complete: DI `__init__(udal, checkpointer, tool_registry, prompt_registry, llm_router)`, circuit breakers (`_call_llm`, `_call_tool`), typed error hierarchy (`AgentError`, `ToolError`, `LLMError`, `CircuitOpenError`, `SLAExceededError`, …), `__init_subclass__` attr guard, `run()` template (understand→plan→execute→verify→learn under SLA).
- `ToolRegistryProtocol`, `PromptRegistryProtocol`, `LLMRouterProtocol` — contract-first stand-ins, already defined in `base.py`.
- `app.db.udal.UDAL` ✅ — read/write artifacts.
- `get_tenant_context()` ✅ — tenant scoping in `run()`.

### What is MISSING vs AF-038 spec ❌
| # | Required | Status |
|---|----------|--------|
| 1 | `ResearchAgent(BaseAgent[...])` on the AF-036 contract | ❌ `research/__init__.py` is a **legacy stub** on the old `Agent` ABC, `raise NotImplementedError` |
| 2 | Pydantic schemas: `ResearchInput`, `Citation`, `SourceResult`, `ResearchFinding`, `ResearchOutput` | ❌ absent |
| 3 | 5 tool wrappers: Tavily, SerpAPI, Crunchbase, G2, SimilarWeb | ❌ no `tools/` dir anywhere in `backend/app` |
| 4 | Parallel fan-out w/ per-tool timeout + cross-source fallback | ❌ absent |
| 5 | LLM synthesis with inline citations | ❌ absent |
| 6 | Citation **groundedness** check (verify phase) | ❌ absent |
| 7 | Redis research cache (`research:cache:{sha256}`) | ❌ absent |
| 8 | Jinja2 synthesis prompt | ❌ absent |
| 9 | Mocked unit + integration tests (`respx`, `FakeLLM`) | ❌ absent |

### Dependency reality check
- **BaseAgent** ✅ — subclass it directly.
- **Tool Registry (AF-047)** ❌ not built → call tools via `ToolRegistryProtocol` (`self._call_tool`). For Phase 1 ship a thin **in-agent tool layer** (`research/tools/*.py`) + a tiny local registry adapter satisfying the protocol, so the agent runs end-to-end before AF-047 lands.
- **Prompt Registry (AF-048)** ❌ not built → `PromptRegistryProtocol`; bundle the synthesis `.j2` locally, load via protocol, swap to AF-048 later.
- **LLM Router (AF-049)** ❌ not built → `LLMRouterProtocol` (`self._call_llm`, `task_class="research_synthesis"`).

> **Consequence:** AF-038 lands NOW on protocols + a local tool adapter; AF-047/048/049 plug in later structurally. Same contract-first principle AF-036 used.

---

## 3. Design decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| D1 | Base class | `ResearchAgent(BaseAgent[ResearchInput, ResearchOutput])` | Use the AF-036 contract; get breakers + SLA + trace free |
| D2 | Replace legacy stub | Delete old `Agent`-based stub in `research/__init__.py`; re-export new `ResearchAgent` | Old `Agent` ABC is Phase-1 legacy; nothing imports the stub's logic |
| D3 | Tools | Thin async wrappers in `research/tools/`, called through `self._call_tool` via a local `ToolRegistryProtocol` adapter | Runs before AF-047; breaker-guarded; swappable |
| D4 | Fan-out | `asyncio.gather(..., return_exceptions=True)` with per-tool `asyncio.timeout` | Parallel; one slow/dead source never blocks the join |
| D5 | Fallback | Tavily⇄SerpAPI cross-fallback; Crunchbase/G2/SimilarWeb failures degrade gracefully (partial data + lower confidence) | Matches plan §2.3 fallback matrix |
| D6 | Synthesis | Single LLM call (`task_class="research_synthesis"`, Gemini 3.5 Flash) producing findings + **inline citation markers** | Groundedness over single-source |
| D7 | Groundedness | `verify()` computes source-backed-claim ratio; `< threshold` → one retrieval retry, else flag `confidence="low"` (non-fatal) | Spec §10.2 citation/groundedness check |
| D8 | Caching | Redis `research:cache:{sha256(domain+idea+sources)}` TTL ~24h | Cut cost + rate-limit pressure |
| D9 | SLA | `SLA_SECONDS = 600` (10 min) | Sub-budget of Strategy's 30 min end-to-end |
| D10 | No new heavy deps | `httpx` (already present) for tool HTTP; `respx` (test-only) for mocks | Keep `uv` lockfile lean |

---

## 4. Implementation

### 4.1 File structure
```
backend/app/agents/research/
├── __init__.py        # re-export ResearchAgent (replaces legacy stub)
├── agent.py           # ResearchAgent(BaseAgent[ResearchInput, ResearchOutput])
├── schema.py          # ResearchInput, Citation, SourceResult, ResearchFinding, ResearchOutput
├── fanout.py          # parallel tool fan-out + timeout + fallback orchestration
├── groundedness.py    # citation groundedness scorer
├── registry.py        # local ToolRegistryProtocol adapter (maps tool_name -> tools/*.py)
├── tools/
│   ├── __init__.py
│   ├── tavily.py      similarweb.py
│   ├── serpapi.py     crunchbase.py
│   └── g2.py
└── prompts/
    └── synthesis.j2
backend/tests/agents/research/   # unit + integration tests
```

### 4.2 Schemas — `schema.py`
```python
class ResearchInput(BaseModel):
    run_id: str; organization_id: str
    idea_normalised: str; domain: str
    queries: list[str] = []          # optional pre-built sub-queries from Strategy
    sources: list[str] = ["tavily", "serpapi", "crunchbase", "g2", "similarweb"]

class Citation(BaseModel):
    source: str; url: str | None = None; title: str | None = None; snippet: str

class SourceResult(BaseModel):
    source: str; ok: bool
    items: list[Citation] = []
    error: str | None = None         # populated when a source failed / was skipped

class ResearchFinding(BaseModel):
    claim: str; citations: list[int] = []   # indices into ResearchOutput.sources

class ResearchOutput(BaseModel):
    run_id: str; organization_id: str; domain: str
    findings: list[ResearchFinding]
    sources: list[Citation]                  # flat citation list, deduped
    groundedness_score: float = Field(..., ge=0.0, le=1.0)
    confidence: str                          # high | medium | low
    partial_sources: list[str] = []          # sources that failed/were skipped
    total_llm_tokens_used: int = 0
```

### 4.3 Tool wrappers — `tools/*.py`
- Each: `async def search(client: httpx.AsyncClient, query: str, *, limit: int) -> list[Citation]`.
- Read API key from settings (`TAVILY_API_KEY`, `SERPAPI_KEY`, `CRUNCHBASE_API_KEY`, `G2_API_KEY`, `SIMILARWEB_API_KEY`).
- **No key set → raise `ToolError` (skipped, not fabricated)**; fan-out records it as `partial`.
- Pure functions over an injected `httpx.AsyncClient` so `respx` can mock with zero live calls.

### 4.4 Fan-out — `fanout.py`
```python
async def fan_out(call_tool, sources, query, *, per_tool_timeout=20.0) -> list[SourceResult]:
    """Parallel tool fan-out via BaseAgent._call_tool (breaker-guarded).
    asyncio.gather(return_exceptions=True); per-tool asyncio.timeout.
    Tavily<->SerpAPI cross-fallback; other failures -> SourceResult(ok=False)."""
```
- Routes every call through `self._call_tool(tool_name, args)` → circuit-breaker + `ToolError` mapping inherited from BaseAgent.

### 4.5 `ResearchAgent` — `agent.py`
```python
class ResearchAgent(BaseAgent[ResearchInput, ResearchOutput]):
    PILLAR = 1
    AGENT_ID = "research"
    SLA_SECONDS = 600   # 10 min

    async def understand(self, input):   # build/expand sub-queries from idea+domain; cache key
    async def plan(self, intent):        # pick sources, fallback order, retrieval budget
    async def execute(self, plan):       # fan_out -> dedupe sources -> LLM synthesis (inline cites) -> ResearchOutput
    async def verify(self, output):      # groundedness ratio; retry retrieval once if low; set confidence
    async def learn(self, trace):        # emit sources + token counts + groundedness to LLMOps
```
- `understand` checks Redis cache first; hit → short-circuit `execute`.
- `execute` synthesis call: `await self._call_llm(task_class="research_synthesis", prompt=rendered)`.

### 4.6 Groundedness — `groundedness.py`
```python
GROUNDEDNESS_THRESHOLD = 0.7
def score_groundedness(findings, sources) -> float:
    """Ratio of findings whose citations[] resolve to >=1 real source. 0.0-1.0."""
```
- `verify()` maps band: `>=0.85 high`, `>=0.7 medium`, `<0.7 low` (and triggers one retrieval retry before settling on `low`).

---

## 5. Step-by-step build order (TDD)

1. `schema.py` — Pydantic models + bounds (`groundedness_score` 0–1, `viability`-style validation). Unit-test first.
2. `tools/*.py` — 5 wrappers over injected `httpx.AsyncClient`. Test each with `respx` (success + failure + no-key).
3. `registry.py` — local adapter satisfying `ToolRegistryProtocol.call(tool_name, args)`.
4. `fanout.py` — parallel gather + timeout + Tavily⇄SerpAPI fallback. Test with fake `call_tool`.
5. `groundedness.py` — scorer + threshold banding. Unit-test.
6. `prompts/synthesis.j2` — multi-source synthesis with inline citation markers.
7. `agent.py` — `ResearchAgent` 5 lifecycle methods + Redis cache in `understand`.
8. `__init__.py` — replace legacy stub; re-export `ResearchAgent`.
9. Tests (§6).
10. `make quality` — ruff + mypy + pytest green (type hints on all public funcs, CLAUDE.md §41).

---

## 6. Tests — `backend/tests/agents/research/`

| ID | Test | Type | Assert |
|----|------|------|--------|
| T1 | schema bounds | unit | `groundedness_score` ∈[0,1]; bad value rejected |
| T2 | each tool wrapper parses results | unit (`respx`) | returns `list[Citation]` |
| T3 | tool no API key | unit | raises `ToolError`, not fabricated data |
| T4 | fan-out parallel happy path | unit | 5 `SourceResult`, all `ok` |
| T5 | Tavily down → SerpAPI fallback | unit | fan-out still returns market signals |
| T6 | Crunchbase/G2/SimilarWeb down | unit | `partial_sources` populated; no crash |
| T7 | one tool times out | unit | that source `ok=False`; others succeed |
| T8 | synthesis produces cited findings | integration (`FakeLLM`) | `findings` non-empty, each has `citations[]` |
| T9 | groundedness ≥ threshold → confidence high/medium | unit | banding correct |
| T10 | low groundedness → retry then `confidence="low"` | integration | one retrieval retry, flagged low |
| T11 | Redis cache hit short-circuits execute | unit (fake redis) | tools NOT called on 2nd run |
| T12 | breaker opens after repeated tool failure | unit | `CircuitOpenError` surfaced (inherited AF-036) |
| T13 | happy-path `run()` calls 5 phases in order | unit | fake records order |

Fakes only — `FakeLLMRouter`, `respx` HTTP mocks, in-memory UDAL, fake Redis, `MemorySaver`. No live infra (matches plan §9.1).

---

## 7. Acceptance criteria (Definition of Done)

- [ ] `ResearchAgent(BaseAgent[ResearchInput, ResearchOutput])`, `PILLAR=1`, `AGENT_ID="research"`, `SLA_SECONDS=600`.
- [ ] 5 tool wrappers (Tavily, SerpAPI, Crunchbase, G2, SimilarWeb) called via `self._call_tool` (breaker-guarded).
- [ ] Parallel fan-out with per-tool timeout + Tavily⇄SerpAPI fallback + graceful partial-source degradation.
- [ ] LLM synthesis with inline citations via `self._call_llm(task_class="research_synthesis")`.
- [ ] Citation groundedness check in `verify()`; low → one retry then `confidence="low"` (non-fatal).
- [ ] Redis cache short-circuit on repeat queries.
- [ ] Legacy `Agent`-based stub replaced; `app.agents.research` imports green.
- [ ] All §6 tests pass; `make quality` green (ruff + mypy + pytest).
- [ ] `.env.example` updated with the 5 keys (+ `PRODUCTHUNT_TOKEN`).
- [ ] Branch `feature/research-agent`, Conventional Commits, PR to `main` (no direct push).

---

## 8. Fallback matrix (from plan §2.3)

| Failure | Strategy |
|---------|----------|
| idea text empty/too short | Ask for clarification; do NOT fabricate a market |
| Tavily / SerpAPI rate-limited | Cross-fallback to the other; reduce result count; lower confidence |
| Crunchbase/G2/SimilarWeb down | Skip source; mark `partial`; lower groundedness |
| Groundedness < threshold | Re-run retrieval once; still low → flag `confidence="low"` |

---

## 9. Downstream unblock

1. AF-038 ✅ → Strategy Agent (AF-037) research nodes delegate to `ResearchAgent`.
2. AF-047 Tool Registry lands → swap local `registry.py` adapter for the real registry (protocol unchanged).
3. AF-048/049 land → real prompt loading + model routing (protocols unchanged).
4. Pallavi (Pillar 6) reuses `ResearchAgent` for competitor/positioning research.
5. Purnima (Pillar 7) consumes groundedness + token traces via `learn()`.

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| AF-047/048/049 not built → DI args undefined | Protocols + local tool/registry adapter; ship now (contract-first, same as AF-036) |
| Hallucinated market sizing | Groundedness check; flag low-confidence reports for human review |
| Research API rate limits / cost | Redis cache + cross-source fallback + breaker fail-fast |
| Prompt injection via idea text | Input redaction/injection check upstream (Guardrails AF-046); treat tool results as untrusted in synthesis prompt |
| 3-agent load on Somesh (plan Appendix B) | Research is self-contained — can be delegated to an early-finishing owner |
