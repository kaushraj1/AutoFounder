# AF-037 — Strategy & Ideation Agent (Pillar 1) — Implementation Plan

> **Task:** Strategy & Ideation Agent (Pillar 1) — TAM/SAM/SOM, competitor discovery, persona gen, Lean Canvas, viability 0–100, bias audit, 3 pivots; **SLA < 30 min**.
> **Owner:** Somesh Chitranshi (Pillar 1)
> **Branch:** `feature/strategy-agent`
> **Depends on:** AF-036 BaseAgent ✅ (done), AF-027 UDAL ✅ (done), AF-048 Prompt Registry 🟡 (not built), AF-049 LLM Router 🟡 (not built)
> **Status:** 🟡 → 🟢 (BaseAgent landed; unblocked to build behind contract-first stand-ins)
> **Dir:** `backend/app/agents/strategy/`
> **Ground truth:** `docs/architecture/Agents-Architecture/strategist-agent.md` (LLD) · `.claude/developer-plans/02-somesh-pillar-1-strategy-research-plan.md` · CLAUDE.md §7.4

---

## 1. Why this task matters

Strategy Agent is the **first agent in the whole pipeline** and the lead of Pillar 1. It turns one raw text idea into a fact-grounded, bias-audited validation package (market sizing, competitor map, personas, Lean Canvas, 0–100 viability, 3 pivots) in **under 30 minutes**. Its output (`lean_canvas`, personas, `viability_band`) is consumed downstream by Kaushlendra (Pillar 2 Architect), Pallavi (Pillar 6 Marketing), and Raunak (Validation Studio AF-055). It blocks AF-039 (Product Planner, `feature/product-planner-agent`) which runs after the HITL approve gate.

This is the **first real subclass of `BaseAgent`** — it proves the AF-036 contract end-to-end (DI, circuit breakers, SLA budget, `run()` template) on a live agent.

---

## 2. Current state (GAP ANALYSIS)

### What exists today ✅
- **AF-036 `BaseAgent`** — `backend/app/agents/base.py`: `BaseAgent(ABC, Generic[TIn, TOut])` with `PILLAR`/`AGENT_ID`/`SLA_SECONDS`, DI `__init__(udal, checkpointer, tool_registry, prompt_registry, llm_router)`, `_call_llm`/`_call_tool` guarded by `CircuitBreaker`, typed error hierarchy, `__init_subclass__` enforcement, and the `run()` understand→plan→execute→verify→learn template with `asyncio.timeout(SLA_SECONDS)`.
- **Contract-first Protocols** — `ToolRegistryProtocol`, `PromptRegistryProtocol`, `LLMRouterProtocol` already defined in `base.py`. AF-037 builds against these; real AF-047/048/049 plug in structurally later.
- **AF-027 UDAL** — `app.db.udal.UDAL` with `.relational / .vector / .graph / .object / .cache`; pgvector `VectorClient` available for `market_intelligence` collection.
- **Orchestrator** — `RunState` TypedDict (`strategy_output: dict | None`), `run_pillar_1` **stub** node in `app/orchestrator/nodes.py` returning a fake `strategy_output`, wired into the StateGraph with `validation_gate` (HITL interrupt) after it.
- **Strategy stub** — `app/agents/strategy/__init__.py` holds a `StrategyAgent(Agent)` (LEGACY ABC) raising `NotImplementedError` on all 5 methods. `research/` and `product_planner/` are the same legacy stubs.
- **Tenant context** — `app.db.context.get_tenant_context()` used by `BaseAgent.run()`.

### What is MISSING vs AF-037 spec ❌

| # | Required | Status |
|---|----------|--------|
| 1 | `StrategyAgent(BaseAgent[StrategistState, StrategistState])` real impl | ❌ stub is legacy `Agent` |
| 2 | `schema.py` — Pydantic V2 `StrategistState` + sub-models (LLD §2) | ❌ absent |
| 3 | LangGraph `build_strategist_graph()` — 11 nodes + barrier + error_handler (LLD §3) | ❌ absent |
| 4 | Node implementations (normalize→fan-out→join→audit→canvas→score→report) | ❌ absent |
| 5 | `routers.py` — `route_after_normalize/join/audit`, `route_terminal` | ❌ absent |
| 6 | Jinja2 prompt templates (`prompts/*.j2`, 10 templates) | ❌ absent |
| 7 | Research tool wrappers / bindings (Tavily, SerpAPI, Crunchbase, G2, trends) | ❌ absent (AF-047/AF-038 territory) |
| 8 | Local stand-in `PromptRegistry` (Jinja2 loader) + `LLMRouter` (Gemini shim) impl satisfying protocols | ❌ absent (AF-048/049 not built) |
| 9 | Viability banding + bias audit logic | ❌ absent |
| 10 | Tests (unit + integration + golden) under `tests/agents/strategy/` | ❌ only `test_base_agent.py` exists |
| 11 | Wire `run_pillar_1` orchestrator node → real `StrategyAgent.run()` | ❌ still a stub |
| 12 | Config env vars (Gemini key, research API keys) + deps (`jinja2`, `respx`) | ❌ absent in `config.py` / `pyproject.toml` |

### Dependency reality check
- **AF-048 Prompt Registry** ❌ not built → use `PromptRegistryProtocol` + a local `JinjaPromptRegistry` that loads `prompts/*.j2`. Swap for the real registry later (no call-site change).
- **AF-049 LLM Router** ❌ not built → use `LLMRouterProtocol` + a thin `GeminiRouter` shim (`google-generativeai`, already an optional dep). Tests inject `FakeLLM`.
- **AF-047 Tool Registry / AF-038 Research tools** ❌ not built. AF-037 hard-depends on AF-048/049 **only** (per task_assigned). Research tool calls route through `_call_tool` / `ToolRegistryProtocol`; provide thin local wrappers as stand-ins, fakes in tests, real tools land with AF-038/AF-047.

> **Consequence:** AF-037 ships **now** behind the three Protocols already baked into `BaseAgent`. Real registries/router/tools replace the stand-ins structurally — zero call-site churn (contract-first, mirrors the AF-036 decision).

---

## 3. Naming reconciliation (must decide once)

Two ground-truth docs diverge:

| Aspect | LLD `strategist-agent.md` | Somesh plan `02-…` | CLAUDE.md §40 repo | **Decision** |
|---|---|---|---|---|
| Dir | `agents/strategist/` | `agents/strategy/` | `agents/strategy/` (exists) | **`agents/strategy/`** (repo-canonical, stub already there) |
| Node names | `normalize_idea`, `size_market`, `discover_competitors`, `mine_keywords`, `generate_personas`, `analyze_trends`, `parallel_join`, `audit_bias`, `synthesize_canvas`, `score_viability`, `render_report`, `error_handler` | `normalise_idea`, `domain_classify`, `market_sizing`, … | — | **LLD names** (richer, includes `error_handler` + `render_report`) |
| Bands | strong/moderate/weak/reject | low/medium/medium-high/high | — | **LLD bands** (`ViabilityBand` enum) |
| Schema | `StrategistState` (Pydantic V2, full) | `StrategyOutput` (flat) | — | **LLD `StrategistState`** internal; map to flat `StrategyOutput` contract for RunState/downstream (§10.7 proto) |

**Net:** LLD is authoritative for schema/graph/nodes/routers; directory stays `agents/strategy/`. Keep `domain` + `geography_focus` from `normalize_idea` (LLD has them). Add a `compose StrategyOutput` adapter so downstream consumers (Pillar 2/6, Validation Studio) get the stable flat contract regardless of internal state shape.

---

## 4. Design decisions

1. **`StrategyAgent(BaseAgent[StrategistState, StrategistState])`** — `PILLAR=1`, `AGENT_ID="strategy"`, `SLA_SECONDS=1800`. Replace the legacy `Agent` stub in `strategy/__init__.py` (no external importer besides itself — verified by grep; orchestrator references `run_pillar_1`, not the class).
2. **Lifecycle maps onto LangGraph**, not hand-rolled:
   - `understand(input)` → normalise idea text + `organization_id`, build initial `StrategistState`.
   - `plan(intent)` → compile `build_strategist_graph(checkpointer)` (returns the DAG plan/handle).
   - `execute(plan)` → `await graph.ainvoke(state)` running all 11 nodes (fan-out parallel branches).
   - `verify(output)` → assert Lean Canvas complete, viability computed, ≥1 source/citation, bias audit ran.
   - `learn(trace)` → emit token counts + node traces + groundedness to LLMOps (LangSmith span); persist via UDAL.
3. **Contract-first stand-ins (no waiting on AF-047/048/049):** `JinjaPromptRegistry` (loads `prompts/*.j2`) satisfies `PromptRegistryProtocol`; `GeminiRouter` satisfies `LLMRouterProtocol`; research tools route through `ToolRegistryProtocol`. All injected via the existing `BaseAgent.__init__` DI.
4. **Circuit breakers come for free** — node LLM/tool calls go through `self._call_llm` / `self._call_tool`, so every model + research call is breaker-guarded and raises typed `LLMError`/`ToolError`/`CircuitOpenError`.
5. **Checkpointer reuse** — the graph compiles with the existing `app.orchestrator.checkpointer.DualCheckpointer` (Postgres + Redis) so a long Strategy run is resumable. Tests use LangGraph `MemorySaver`.
6. **Parallel fan-out** — `size_market ∥ discover_competitors ∥ mine_keywords ∥ generate_personas ∥ analyze_trends` then `parallel_join` barrier (matches LLD §3.2). Independent nodes keep total wall-clock under the 30-min SLA.
7. **Self-healing per node** — `RetryPolicy` (3 retries, `[5,15,45]s` backoff) on tool failures; `error_handler` sink escalates fatal errors. Layered under the BaseAgent breakers (fast-fail) — node retry is the inner loop, breaker is the outer.
8. **Bias audit is a real node**, not a checkbox — `audit_bias` flags Western-centric / recency / survivorship / confirmation bias on the merged research before canvas synthesis.
9. **Pivots only when band is weak/reject** — `score_viability` emits 3 `pivot_suggestions` when `total < 50`; avoids noise on strong ideas (Decision D4).
10. **Research tools deferred but contracted** — define the tool **call signatures** Strategy needs (`tavily_search`, `serpapi_search`, `crunchbase_lookup`, `g2_lookup`, `trends_lookup`); real impls land in AF-038/AF-047. Strategy never calls a tool SDK directly — always `self._call_tool(name, args)`.

---

## 5. File structure (deliverables)

```
backend/app/agents/strategy/
├── __init__.py            # re-export StrategyAgent (replaces legacy stub)
├── agent.py               # StrategyAgent(BaseAgent[StrategistState, StrategistState])
├── schema.py              # StrategistState + sub-models (LLD §2) + StrategyOutput adapter
├── graph.py               # build_strategist_graph(checkpointer)
├── routers.py             # route_after_normalize / route_after_join / route_after_audit / route_terminal
├── nodes/
│   ├── __init__.py
│   ├── normalize_idea.py
│   ├── size_market.py
│   ├── discover_competitors.py
│   ├── mine_keywords.py
│   ├── generate_personas.py
│   ├── analyze_trends.py
│   ├── parallel_join.py
│   ├── audit_bias.py
│   ├── synthesize_canvas.py
│   ├── score_viability.py
│   ├── render_report.py
│   └── error_handler.py
├── tools.py               # research tool call signatures (stand-ins → AF-038/047)
└── prompts/
    ├── normalize_idea.j2
    ├── size_market.j2
    ├── discover_competitors.j2
    ├── mine_keywords.j2
    ├── generate_personas.j2
    ├── analyze_trends.j2
    ├── audit_bias.j2
    ├── synthesize_canvas.j2
    ├── score_viability.j2
    └── render_report.j2

backend/app/agents/_providers/         # contract-first stand-ins (shared, retire when AF-048/049 land)
├── __init__.py
├── jinja_prompt_registry.py           # PromptRegistryProtocol impl
└── gemini_router.py                   # LLMRouterProtocol impl (google-generativeai)

backend/tests/agents/strategy/
├── conftest.py            # FakeLLM, fake tool registry, in-memory UDAL, MemorySaver
├── unit/
│   ├── test_schema_validation.py      # TAM≥SAM≥SOM, viability 0-100, canvas min/max lengths
│   ├── test_viability_banding.py      # derive_band thresholds 75/50/25
│   ├── test_bias_audit.py             # diversification flags
│   └── test_routers.py                # normalize/join/audit/terminal routing
├── integration/
│   ├── test_graph_happy_path.py       # strong idea → render_report, no pivots
│   ├── test_graph_low_viability.py    # weak → 3 pivots
│   ├── test_research_fanout.py        # 5 parallel branches merge with sources
│   └── test_tool_fallback.py          # tavily down → serpapi fallback, run still completes
└── test_strategy_agent_run.py         # StrategyAgent.run() drives 5 phases under SLA
```

---

## 6. Schema (`schema.py`) — authoritative from LLD §2

Port LLD §2 verbatim (Pydantic V2): `NodeStatus`, `ViabilityBand`, `BiasFlag` enums; `MarketSize` (with `TAM≥SAM≥SOM` `model_validator`), `Competitor`, `Keyword`, `BuyerPersona`, `TrendSignal`, `LeanCanvas` (min/max length constraints), `ViabilityScore` (`derive_band` validator), `NodeTrace`, `RetryPolicy`, and root `StrategistState`.

**Add** a flat output adapter (downstream stability + §10.7 proto alignment):

```python
class StrategyOutput(BaseModel):
    run_id: str
    organization_id: str
    idea_normalised: str
    domain: str
    tam_sam_som: dict[str, float]
    competitors: list[Competitor]
    icps: list[BuyerPersona]
    lean_canvas: LeanCanvas
    viability_score: int          # 0-100
    viability_band: str
    bias_flags: list[str]
    pivots: list[str]
    sources: list[str]
    report_markdown: str
    total_llm_tokens_used: int

    @classmethod
    def from_state(cls, s: "StrategistState") -> "StrategyOutput": ...
```

`from_state` is what `run_pillar_1` writes into `RunState["strategy_output"]`.

---

## 7. Node behaviour (contract)

| Node | Reads | Writes | LLM/Tool | SLA |
|---|---|---|---|---|
| `normalize_idea` | `idea_raw` | `idea_normalised`, `domain`, `geography_focus` | LLM (+PII redact) | <30s |
| `size_market` | `idea_normalised`, `domain` | `market_size` | LLM + `tavily_search`/`serpapi_search` | <5min |
| `discover_competitors` | `idea_normalised` | `competitors[]` | LLM + `crunchbase_lookup`/`g2_lookup` | <5min |
| `mine_keywords` | `idea_normalised` | `keywords[]` | LLM + `serpapi_search` | <3min |
| `generate_personas` | `idea_normalised`, `domain` | `personas[]` | LLM | <3min |
| `analyze_trends` | `idea_normalised` | `trend_signals[]` | LLM + `trends_lookup` | <5min |
| `parallel_join` | all 5 above | merged context, `total_tool_calls` | — (barrier) | — |
| `audit_bias` | merged research | `bias_flags[]` | LLM | <2min |
| `synthesize_canvas` | merged research | `lean_canvas` | LLM | <3min |
| `score_viability` | canvas + research | `viability_score` (+pivots if `<50`) | LLM | <2min |
| `render_report` | everything | `report_markdown` (+S3 PDF later) | LLM | <1min |
| `error_handler` | `fatal_error` | escalate / end | — | — |

Every node: append a `NodeTrace`, increment `total_llm_tokens_used`, call models via `self._call_llm(...)` and tools via `self._call_tool(...)` (breaker-guarded). Nodes are written as methods/closures bound to the agent instance (so they have `self._call_llm`), or as functions taking an injected `ctx` carrying the call helpers — **decision: bind via a small `NodeContext` injected at graph-build time** to keep node fns testable in isolation.

---

## 8. Step-by-step build order (TDD where practical)

1. **Deps + config.** Add `jinja2` (runtime) and `respx` (test) to `pyproject.toml`; promote `langgraph` + `google-generativeai` out of the optional `agents` extra into core (agents are now first-class). Add env vars to `config.py`: `gemini_api_key`, `strategy_model` (default `"gemini-2.5-flash"`), `tavily_api_key`, `serpapi_key`, `crunchbase_api_key`, `g2_api_key`, `similarweb_api_key` (all dev-safe `""` defaults). `uv sync`.
2. **`schema.py`** — port LLD §2 + `StrategyOutput.from_state`. Unit-test validators first (`test_schema_validation.py`, `test_viability_banding.py`).
3. **Prompts** — author the 10 `prompts/*.j2` (sizing, competitor, keyword, persona, trends, bias, canvas, viability, report, normalize). Each declares its variables (LLD §5 + plan §10.3).
4. **`_providers/jinja_prompt_registry.py`** — `JinjaPromptRegistry.get(key, version=None) -> str` rendering from `prompts/`. Satisfies `PromptRegistryProtocol`.
5. **`_providers/gemini_router.py`** — `GeminiRouter.complete(*, task_class, prompt, **kw) -> str`. Satisfies `LLMRouterProtocol`. Thin wrapper over `google-generativeai`; structured-JSON mode for canvas/score nodes.
6. **`tools.py`** — define the research tool call signatures + a `LocalToolRegistry` stand-in satisfying `ToolRegistryProtocol` (raises `NotImplementedError`-with-fallback or returns empty + lowers groundedness until AF-038/047 land). Real fan-out is AF-038.
7. **`nodes/`** — implement 12 node fns + `NodeContext` (carries `call_llm`, `call_tool`, `prompts`). Cross-source fallback (Tavily→SerpAPI) lives in `size_market`/`mine_keywords`.
8. **`routers.py`** — port LLD §3 routers.
9. **`graph.py`** — `build_strategist_graph(checkpointer)` per LLD §3.2 (fan-out list, barrier, conditional edges, error_handler→END).
10. **`agent.py`** — `StrategyAgent(BaseAgent[...])`; map `understand/plan/execute/verify/learn` onto the graph (§4.2). `verify` enforces canvas completeness + viability + ≥1 source + bias-audit-ran.
11. **`__init__.py`** — re-export `StrategyAgent` (delete legacy `Agent`-based stub body). Confirm `app/agents/__init__.py` still imports legacy `Agent` + Pydantic models from `base` (untouched) so `research`/`product_planner` stubs stay green.
12. **Wire orchestrator** — `run_pillar_1` instantiates `StrategyAgent` (DI: UDAL from request ctx, `DualCheckpointer`, `LocalToolRegistry`, `JinjaPromptRegistry`, `GeminiRouter`), calls `await agent.run(state_input)`, writes `StrategyOutput.from_state(...)` into `RunState["strategy_output"]`. **Guard:** if `gemini_api_key` empty (dev/CI), fall back to the existing stub dict so `test_graph.py` stays green. Keep `validation_gate` interrupt unchanged.
13. **Tests** — unit (§5) then integration with `FakeLLM` + `respx` HTTP mocks + `MemorySaver`. Golden evals under `tests/golden/strategy/` (Phase 2, Promptfoo) — scaffold only now.
14. **Quality gate** — `make quality` (ruff + mypy + pytest) green. Type hints on all public fns (CLAUDE.md §41).

---

## 9. Tests — key scenarios

| ID | Test | Type | Assert |
|----|------|------|--------|
| T1 | strong-viability idea → approve path | integration | `band==strong`; canvas complete; `len(pivots)==0`; `report_markdown` set |
| T2 | weak idea → 3 pivots | integration | `total<50`; `len(pivot_suggestions)==3` |
| T3 | research fan-out + citations | integration | 5 branches merge; `sources` non-empty; `total_tool_calls>0` |
| T4 | Tavily down → SerpAPI fallback | integration | `size_market` completes; run finishes |
| T5 | empty / <10-char idea | unit | `StrategistState` validation rejects; agent asks for clarification, no fabricated market |
| T6 | bias audit flags Western-centric framing | unit | `bias_flags` contains `western_centric` |
| T7 | viability banding thresholds | unit | 75→strong, 50→moderate, 25→weak, 24→reject |
| T8 | `TAM≥SAM≥SOM` violated | unit | `MarketSize` raises `ValueError` |
| T9 | `StrategyAgent.run()` drives 5 phases under SLA | unit | call order understand→plan→execute→verify→learn; trace emitted |
| T10 | SLA blown → `SLAExceededError` | unit | slow fake node + low `SLA_SECONDS` → typed error |
| T11 | LLM 5× fail → breaker OPEN → `CircuitOpenError` | unit | `_call_llm` opens `strategy.llm` breaker |
| T12 | `route_*` routing | unit | normalize fatal→error_handler; join retries-exhausted→error_handler; terminal missing-report→error_handler |

Fakes only — no live infra/APIs (matches LLD §9 + AF-036 test philosophy). `FakeLLM` returns pre-built canvas/score JSON; `respx` mocks research HTTP; in-memory UDAL; `MemorySaver` checkpointer.

---

## 10. Acceptance criteria (Definition of Done)

- [ ] `StrategyAgent(BaseAgent[StrategistState, StrategistState])` with `PILLAR=1`, `AGENT_ID="strategy"`, `SLA_SECONDS=1800`; 5 lifecycle methods mapped onto the LangGraph run.
- [ ] `schema.py` ports LLD §2 (Pydantic V2) + `StrategyOutput.from_state` adapter.
- [ ] `build_strategist_graph()` — 11 nodes + `error_handler`, parallel fan-out + barrier, conditional routers (LLD §3).
- [ ] 10 Jinja2 prompt templates render via `JinjaPromptRegistry` (`PromptRegistryProtocol`).
- [ ] `GeminiRouter` (`LLMRouterProtocol`) + research tool calls routed through `_call_llm`/`_call_tool` (breaker-guarded).
- [ ] Contract-first: AF-037 builds with **zero** dependency on un-built AF-047/048/049 — stand-ins satisfy the Protocols.
- [ ] Bias audit node emits `bias_flags`; pivots generated only when `total<50` (3 of them).
- [ ] `run_pillar_1` wired to real agent, with dev/CI stub fallback when `gemini_api_key` empty; `test_graph.py` stays green.
- [ ] Legacy `Agent` + `research`/`product_planner` stubs still import & pass.
- [ ] All §9 tests pass; `make quality` green (ruff + mypy + pytest).
- [ ] Branch `feature/strategy-agent`, Conventional Commits, PR to `main` (no direct push).

---

## 11. Downstream unblock (what lands after)

1. AF-037 ✅ → `strategy_output` (canvas + personas + viability) flows through `RunState`.
2. **AF-038 Research Agent** (`feature/research-agent`) — real Tavily/SerpAPI/Crunchbase/G2/SimilarWeb fan-out + citation groundedness; replaces `LocalToolRegistry` stand-ins (needs AF-047 Tool Registry).
3. **AF-039 Product Planner** (`feature/product-planner-agent`) — runs after the validation HITL gate, consumes `StrategyOutput` → PRD + roadmap + user stories.
4. **AF-055 Validation Studio** (Raunak) — consumes canvas + viability gauge + ICP cards + pivot picker (agree the data contract via `StrategyOutput`).
5. **Kaushlendra Pillar 2 / Pallavi Pillar 6** — consume `lean_canvas` + personas; confirm schema now (Coordination Checklist).
6. Real **AF-048 Prompt Registry** + **AF-049 LLM Router** (Purnima) drop in structurally — retire `_providers/` stand-ins.

---

## 12. Risks

| Risk | Mitigation |
|------|------------|
| AF-048/049/047 not built → DI args undefined | Build against the 3 Protocols already in `base.py`; ship `_providers/` stand-ins now (contract-first) |
| Strategy needs research tools but AF-038/047 absent | Route all tool calls via `_call_tool`/`ToolRegistryProtocol`; `LocalToolRegistry` returns partial + lowers groundedness; real fan-out lands with AF-038 |
| `strategist/` vs `strategy/` + node-name divergence | Reconciled in §3 — dir `strategy/`, LLD node names, LLD bands |
| Hallucinated market sizing | Citation groundedness check in `verify`; flag low-confidence; `TAM≥SAM≥SOM` validator |
| Western-centric bias | `audit_bias` node + diversified prompts + downstream human gate |
| 30-min SLA blown on parallel research | `asyncio.timeout(SLA_SECONDS)` in `run()`; parallel fan-out; per-node retry budget; breaker fast-fail |
| 3-agent Pillar-1 load slows the chain (P2→P3 wait) | Risk register B/D — flag to Asit; AF-038 or AF-039 reassignable to a lighter owner |
| Breaking orchestrator `test_graph.py` | `run_pillar_1` keeps stub fallback when `gemini_api_key` empty (CI path) |
| New runtime dep (`jinja2`) | Tiny, ubiquitous; no transitive risk; `google-generativeai`/`langgraph` already declared |

---

*Plan for AF-037 — Strategy & Ideation Agent (Pillar 1). Owner: Somesh Chitranshi. Ground truth: `docs/architecture/Agents-Architecture/strategist-agent.md` + `.claude/developer-plans/02-somesh-pillar-1-strategy-research-plan.md` + CLAUDE.md §7.4. Builds on AF-036 BaseAgent (merged).*
