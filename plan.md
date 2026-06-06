# AF-039 — Product Planner Agent (Pillar 1.5) — Implementation Plan

> **Task:** Product Planner Agent (Pillar 1.5) — PRD generation, roadmap, user stories, requirements extraction from Strategy output.
> **Owner:** Somesh Chitranshi (Pillar 1) — heaviest single load: 3 agents (AF-037 / AF-038 / AF-039).
> **Branch:** `feature/product-planner-agent`
> **Depends on:** AF-036 BaseAgent ✅, AF-027 UDAL ✅, AF-037 Strategy Agent ✅ (produces `StrategyOutput`), AF-038 Research Agent ✅.
> **Soft-blocked by:** AF-048 Prompt Registry 🟡, AF-049 LLM Router 🟡 → satisfied via Protocols + local providers (`JinjaPromptRegistry`, `GeminiRouter`), same contract-first pattern as AF-037/038.
> **Downstream consumer:** AF-040 Architect Agent (Pillar 2, Kaushlendra) — **the PRD + requirements are its primary input.**
> **Priority:** P0 — gates the entire build pipeline (Pillar 2→7 wait on the PRD).
> **File(s):** `backend/app/agents/product_planner/`
> **Ground truth:** `.claude/developer-plans/02-somesh-pillar-1-strategy-research-plan.md` (§4.2, §4.3, §5.1, §10.3), `.claude/developer-plans/03-kaushlendra-pillar-2-architecture-plan.md` (PRD consumer contract), `.claude/specs/agents.md` §7.4, `.claude/TASKS.md` AF-039.

---

## 1. Why this task matters

The Product Planner is the **bridge from validation to construction**. It runs **after** the founder approves the Strategy Agent's Lean Canvas at the validation HITL gate, and turns the validated strategy (canvas + personas + viability) into a structured, buildable specification: a **PRD**, **functional + non-functional requirements**, **INVEST user stories**, and a **phased roadmap**.

Everything downstream inherits this artifact:

- **Pillar 2 (Architect, AF-040)** extracts FRs/NFRs/use-cases *directly from the PRD* to design the ERD, OpenAPI contract, and stack. A weak or hallucinated PRD poisons the whole technical blueprint.
- **Pillar 3 (Coder)** builds against the user stories + acceptance criteria.
- **Pillar 4 (Reviewer)** asserts coverage against the same acceptance criteria.

Its single job: **faithfully decompose validated strategy into requirements that trace back to the canvas/personas — no invented features.** Feature-list hallucination here is the #1 risk (a feature with no canvas/persona backing becomes wasted build cost across 5 downstream pillars).

---

## 2. Current state (GAP ANALYSIS)

### What exists today ✅
- `backend/app/agents/base.py` — **AF-036 `BaseAgent[TIn, TOut]`** complete: DI `__init__(udal, checkpointer, tool_registry, prompt_registry, llm_router)`, breakers (`_call_llm`, `_call_tool`), typed errors, `__init_subclass__` attr guard (`PILLAR:int`, `AGENT_ID:str`, `SLA_SECONDS:int`), `run()` template (understand→plan→execute→verify→learn under SLA).
- `backend/app/agents/strategy/schema.py` — **`StrategyOutput`** ✅ (the PP input contract): `idea_normalised`, `domain`, `tam_sam_som`, `competitors: list[Competitor]`, `icps: list[BuyerPersona]`, `lean_canvas: LeanCanvas`, `viability_score:int`, `viability_band`, `pivots`, `sources`, `report_markdown`. Reusable models: `LeanCanvas`, `BuyerPersona`, `Competitor`.
- `backend/app/agents/_providers/` — shared **`JinjaPromptRegistry`** (maps `pillar/template` → `backend/app/agents/{pillar}/prompts/{template}.j2`) and **`GeminiRouter`** (`LLMRouterProtocol`, `json_mode=True` supported). Reuse both — no new providers.
- `app.db.udal.UDAL` ✅ + `udal.cache` (Redis `get_session`/`set_session`) ✅ — artifact read/write + cache.
- Research Agent (AF-038) ✅ — reference implementation for: lifecycle methods, `verify()` groundedness/coverage scorer + banding pattern, Redis cache short-circuit, JSON-mode synthesis + fenced-code cleanup, `learn()` telemetry. **Mirror its conventions.**

### What is MISSING vs AF-039 spec ❌
| # | Required | Status |
|---|----------|--------|
| 1 | `ProductPlannerAgent(BaseAgent[ProductPlannerInput, ProductPlannerOutput])` on AF-036 contract | ❌ `product_planner/__init__.py` is a **legacy stub** on the old `Agent` ABC, `raise NotImplementedError` |
| 2 | Pydantic schemas: `ProductPlannerInput`, `PRD`, `Requirement`, `UserStory`, `Milestone`, `ProductPlannerOutput` | ❌ absent |
| 3 | LLM synthesis: PRD → requirements → user stories → roadmap | ❌ absent |
| 4 | **Traceability / coverage check** (verify phase) — every requirement/story traces to canvas or persona | ❌ absent |
| 5 | PRD markdown render + artifact persistence (`prd_s3_uri`) via UDAL | ❌ absent |
| 6 | Redis cache (`product_planner:cache:{sha256}`) | ❌ absent |
| 7 | Jinja2 prompts (`generate_prd`, `extract_requirements`, `generate_user_stories`, `build_roadmap`) | ❌ absent |
| 8 | Unit + integration tests (`FakeLLM`, fake UDAL, `MemorySaver`) | ❌ absent |

### Dependency reality check
- **BaseAgent** ✅ — subclass directly.
- **Strategy Agent (AF-037)** ✅ — `StrategyOutput` is done and importable; PP takes it as input. **No protocol stand-in needed.**
- **Prompt Registry (AF-048)** ❌ → use shared `JinjaPromptRegistry` (already used by AF-037/038); bundle `.j2` locally; swap to AF-048 later (protocol unchanged).
- **LLM Router (AF-049)** ❌ → use shared `GeminiRouter` via `LLMRouterProtocol` (`self._call_llm`, `task_class="product_planner_*"`).
- **Tool Registry (AF-047)** — **not needed.** PP is LLM-only; it makes **zero external tool calls** (all market data already lives in `StrategyOutput`, gathered by Research). BaseAgent DI still requires a `tool_registry` arg → inject a tiny **`NoToolRegistry`** that raises on `.call()` (PP never calls `_call_tool`; the breaker stays cold).

> **Consequence:** AF-039 lands NOW with **no new external dependencies** — it is the cleanest of the three Pillar-1 agents (no tool fan-out, no API keys). Pure structured-generation + traceability verification.

---

## 3. Design decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| D1 | Base class | `ProductPlannerAgent(BaseAgent[ProductPlannerInput, ProductPlannerOutput])` | AF-036 contract → breakers + SLA + trace free |
| D2 | Pillar attr | `PILLAR = 1` (conceptual stage **1.5**, documented in docstring) | `__init_subclass__` requires `int`; 1.5 is a sub-stage of Pillar 1, not a new pillar |
| D3 | Replace legacy stub | Delete old `Agent`-based stub in `__init__.py`; re-export new `ProductPlannerAgent` | Old `Agent` ABC is Phase-1 legacy; nothing imports the stub's logic |
| D4 | **No tools** | LLM-only; inject `NoToolRegistry` (raises if called) | All inputs already in `StrategyOutput`; PP synthesizes, it does not gather |
| D5 | Input contract | `ProductPlannerInput` wraps the real `StrategyOutput` (import from `app.agents.strategy.schema`) | Single source of truth; no drift between Strategy out and PP in |
| D6 | Generation shape | **Staged LLM calls** inside `execute()`: (1) `generate_prd` → (2) `extract_requirements` → (3) `generate_user_stories` → (4) `build_roadmap` | Decomposition keeps each call grounded + smaller-context; cheaper retries; each stage's output feeds the next |
| D7 | Model | `task_class="product_planner_generation"`, Gemini 3.5 Flash, `json_mode=True` | Matches plan §10.3 registry entry; structured JSON out |
| D8 | **Traceability** | `verify()` computes a coverage score: (a) every persona has ≥1 user story, (b) every canvas `solution`/`problem` item maps to ≥1 requirement, (c) every requirement/story cites a canvas/persona source | Anti-hallucination — the feature-list cross-ref guard the dev-plan calls out |
| D9 | Low coverage → retry | `< THRESHOLD` → one regeneration retry with stricter "trace-or-drop" instruction; still low → `confidence="low"` (non-fatal, flagged for human review) | Mirror AF-038 groundedness retry; never hard-fail the run |
| D10 | Persistence | Render `prd_markdown`; persist PRD artifact via UDAL → `prd_s3_uri` (StrategyOutput protobuf field 11) | Architect (AF-040) reads the PRD artifact by URI |
| D11 | Caching | Redis `product_planner:cache:{sha256(strategy_output)}` TTL ~24h | Re-runs on same approved strategy are free |
| D12 | SLA | `SLA_SECONDS = 600` (10 min) | Post-gate, not latency-critical; 4 sequential LLM calls + retry fit comfortably |
| D13 | No new deps | `jinja2` (present), reuse `_providers` | Keep `uv` lockfile lean |

---

## 4. Implementation

### 4.1 File structure
```
backend/app/agents/product_planner/
├── __init__.py            # re-export ProductPlannerAgent (replaces legacy stub)
├── agent.py               # ProductPlannerAgent(BaseAgent[ProductPlannerInput, ProductPlannerOutput])
├── schema.py              # ProductPlannerInput, PRD, Requirement, UserStory, Milestone, ProductPlannerOutput
├── coverage.py            # traceability/coverage scorer + confidence banding (mirror groundedness.py)
├── registry.py            # NoToolRegistry (ToolRegistryProtocol; raises on call — PP has no tools)
├── persistence.py         # render_prd_markdown() + persist_prd() -> prd_s3_uri via UDAL
└── prompts/
    ├── generate_prd.j2
    ├── extract_requirements.j2
    ├── generate_user_stories.j2
    └── build_roadmap.j2
backend/tests/agents/product_planner/
├── conftest.py            # FakeProductPlannerLLMRouter, NoToolRegistry, fake UDAL, sample StrategyOutput
├── unit/
│   ├── test_schema.py
│   ├── test_coverage.py
│   └── test_persistence.py
└── integration/
    └── test_product_planner_agent.py
```

### 4.2 Schemas — `schema.py`
```python
from app.agents.strategy.schema import StrategyOutput, BuyerPersona, LeanCanvas  # reuse

class ProductPlannerInput(BaseModel):
    run_id: str
    organization_id: str
    strategy: StrategyOutput            # the approved validation output (canvas + personas + viability)

class Requirement(BaseModel):
    id: str                             # "FR-001" | "NFR-001"
    kind: str                           # "functional" | "non_functional"
    statement: str
    priority: str                       # MoSCoW: "must" | "should" | "could" | "wont"
    rationale: str | None = None
    traces_to: str                      # canvas/persona ref it derives from (anti-hallucination anchor)

class UserStory(BaseModel):
    id: str                             # "US-001"
    persona: str                        # name of a BuyerPersona from strategy.icps
    role: str
    want: str                           # "I want to ..."
    benefit: str                        # "so that ..."
    acceptance_criteria: list[str] = Field(..., min_length=1)
    priority: str                       # MoSCoW
    epic: str | None = None

class Milestone(BaseModel):
    phase: str                          # "MVP" | "v1" | "v2"
    title: str
    objective: str
    epics: list[str] = Field(default_factory=list)
    user_story_ids: list[str] = Field(default_factory=list)
    target_weeks: int | None = None

class PRD(BaseModel):
    title: str
    overview: str
    problem_statement: str
    goals: list[str] = Field(..., min_length=1)
    non_goals: list[str] = Field(default_factory=list)
    target_users: list[str] = Field(..., min_length=1)   # persona names
    success_metrics: list[str] = Field(default_factory=list)
    scope_in: list[str] = Field(default_factory=list)
    scope_out: list[str] = Field(default_factory=list)

class ProductPlannerOutput(BaseModel):
    run_id: str; organization_id: str; domain: str
    prd: PRD
    requirements: list[Requirement]
    user_stories: list[UserStory]
    roadmap: list[Milestone]
    prd_markdown: str
    prd_s3_uri: str | None = None
    coverage_score: float = Field(..., ge=0.0, le=1.0)
    confidence: str                     # high | medium | low
    total_llm_tokens_used: int = 0
```

### 4.3 `NoToolRegistry` — `registry.py`
```python
class NoToolRegistry(ToolRegistryProtocol):
    """Product Planner makes no external tool calls. Present only to satisfy
    BaseAgent DI; raising here makes an accidental _call_tool loud, not silent."""
    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("ProductPlannerAgent does not use external tools")
```

### 4.4 `ProductPlannerAgent` — `agent.py`
```python
class ProductPlannerAgent(BaseAgent[ProductPlannerInput, ProductPlannerOutput]):
    PILLAR = 1            # conceptual stage 1.5 (post-validation-gate sub-stage of Pillar 1)
    AGENT_ID = "product_planner"
    SLA_SECONDS = 600     # 10 min

    async def understand(self, input):   # validate strategy present + approved-band; build cache key
    async def plan(self, intent):        # Redis cache check → short-circuit on hit; else staged-gen plan
    async def execute(self, plan):       # generate_prd → extract_requirements → generate_user_stories
                                         #   → build_roadmap → render markdown → persist (prd_s3_uri) → cache
    async def verify(self, output):      # coverage/traceability score; retry once if low; set confidence
    async def learn(self, trace):        # emit #reqs / #stories / coverage / tokens to LLMOps
```
- `understand` rejects empty canvas; warns (non-fatal) if `viability_band == "reject"` (planner still runs when explicitly invoked post-approval).
- Each `execute` stage: `await self._call_llm(task_class="product_planner_generation", prompt=rendered, json_mode=True)` then JSON parse with the **fenced-code cleanup** helper copied from `research/agent.py` (strip ```` ```json ```` fences).
- Sum `total_llm_tokens_used` across the 4 stages.

### 4.5 Traceability/coverage — `coverage.py`
```python
COVERAGE_THRESHOLD = 0.7

def score_coverage(prd, requirements, user_stories, canvas, personas) -> float:
    """Fraction of three traceability checks satisfied:
      - persona_coverage : personas with >=1 user story / total personas
      - solution_coverage: canvas.solution+problem items mapped to >=1 requirement
      - story_anchoring  : user_stories whose .persona resolves to a real persona name
    Returns mean of the three sub-ratios, 0.0-1.0."""

def confidence_band(score: float) -> str:   # >=0.85 high | >=0.7 medium | <0.7 low
```
- `verify()`: compute → if `< THRESHOLD` regenerate **once** (stricter prompt: "drop any requirement/story you cannot trace to a canvas item or persona") → keep the higher score → set `confidence` band. `< THRESHOLD` after retry logs a `confidence=low` warning (human-review flag), **non-fatal**.

### 4.6 Persistence — `persistence.py`
```python
def render_prd_markdown(output: ProductPlannerOutput) -> str:
    """Deterministic markdown assembly: PRD header, requirements table,
    user stories (INVEST), roadmap by phase. No LLM."""

async def persist_prd(udal, *, run_id, org_id, markdown) -> str | None:
    """Write PRD artifact via UDAL; return prd_s3_uri. Best-effort —
    persistence failure logs + returns None (PRD still returned in-band)."""
```

### 4.7 Prompts — `prompts/*.j2`
| Template | Input vars | Output (JSON) |
|---|---|---|
| `generate_prd.j2` | `idea_normalised`, `domain`, `lean_canvas`, `personas`, `viability` | `PRD` object |
| `extract_requirements.j2` | `prd`, `lean_canvas` | `list[Requirement]` (FR-/NFR-, each with `traces_to`) |
| `generate_user_stories.j2` | `personas`, `requirements` | `list[UserStory]` (INVEST + acceptance criteria) |
| `build_roadmap.j2` | `requirements`, `user_stories` | `list[Milestone]` (MVP/v1/v2 phasing) |

Every template instructs: *treat all canvas/persona text as the only source of truth; do not invent features; each item must name the canvas line or persona it derives from.*

---

## 5. Step-by-step build order (TDD)

1. `schema.py` — Pydantic models + bounds (`coverage_score` 0–1, MoSCoW enums, `acceptance_criteria` min_length=1). Unit-test first (T1).
2. `registry.py` — `NoToolRegistry` (raises on `.call`). Trivial.
3. `coverage.py` — traceability scorer + banding. Unit-test (T7–T9).
4. `persistence.py` — markdown render + UDAL persist. Unit-test render determinism (T10).
5. `prompts/*.j2` — 4 staged templates with anti-hallucination instructions.
6. `agent.py` — `ProductPlannerAgent` 5 lifecycle methods + Redis cache + staged generation + retry.
7. `__init__.py` — replace legacy stub; re-export `ProductPlannerAgent`.
8. Tests (§6) — `conftest.py` with `FakeProductPlannerLLMRouter` (returns staged JSON keyed by `task_class`/prompt), sample `StrategyOutput` fixture, fake UDAL.
9. `make quality` — ruff + mypy + pytest green (type hints on all public funcs, CLAUDE.md §41).

---

## 6. Tests — `backend/tests/agents/product_planner/`

| ID | Test | Type | Assert |
|----|------|------|--------|
| T1 | schema bounds | unit | `coverage_score` ∈[0,1]; empty `goals`/`acceptance_criteria` rejected |
| T2 | `understand` rejects empty canvas | unit | raises `ValueError` |
| T3 | `understand` warns but proceeds on `reject` band | unit | no raise; intent built |
| T4 | full `execute` produces PRD+reqs+stories+roadmap | integration (`FakeLLM`) | all 4 non-empty; tokens summed |
| T5 | staged calls invoked in order | integration | fake records 4 `task_class` calls in PRD→req→story→roadmap order |
| T6 | `NoToolRegistry.call` raises | unit | `_call_tool` would surface `NotImplementedError` |
| T7 | full traceability → confidence high | unit | coverage ≥0.85; band `high` |
| T8 | persona with no story lowers coverage | unit | `persona_coverage` < 1; band drops |
| T9 | low coverage → one regen retry → `confidence="low"` | integration | one extra LLM call; flagged low, non-fatal |
| T10 | markdown render is deterministic + complete | unit | contains every requirement id + story id + phase |
| T11 | Redis cache hit short-circuits execute | unit (fake redis) | LLM NOT called on 2nd run |
| T12 | PRD persisted → `prd_s3_uri` set | integration (fake UDAL) | uri non-null; markdown written |
| T13 | persistence failure degrades gracefully | unit | `prd_s3_uri is None`; output still returned |
| T14 | happy-path `run()` calls 5 phases in order | unit | fake records order |

Fakes only — `FakeProductPlannerLLMRouter`, `NoToolRegistry`, in-memory UDAL+cache, `MemorySaver`. No live infra.

---

## 7. Acceptance criteria (Definition of Done)

- [ ] `ProductPlannerAgent(BaseAgent[ProductPlannerInput, ProductPlannerOutput])`, `PILLAR=1`, `AGENT_ID="product_planner"`, `SLA_SECONDS=600`.
- [ ] Input wraps the real `StrategyOutput` (imported from `app.agents.strategy.schema`); no schema drift.
- [ ] Staged LLM generation: PRD → requirements (FR/NFR + `traces_to`) → INVEST user stories → phased roadmap, via `self._call_llm(task_class="product_planner_generation", json_mode=True)`.
- [ ] **No external tools** — `NoToolRegistry` injected; `_call_tool` never invoked.
- [ ] Traceability/coverage check in `verify()`; low → one regen retry then `confidence="low"` (non-fatal, human-review flag).
- [ ] `prd_markdown` rendered; PRD persisted via UDAL → `prd_s3_uri` (best-effort).
- [ ] Redis cache short-circuit on repeat (same approved strategy).
- [ ] Legacy `Agent`-based stub replaced; `app.agents.product_planner` imports green.
- [ ] All §6 tests pass; `make quality` green (ruff + mypy + pytest).
- [ ] Branch `feature/product-planner-agent`, Conventional Commits, PR to `main` (no direct push).

---

## 8. Fallback matrix

| Failure | Strategy |
|---------|----------|
| `strategy.lean_canvas` empty/missing | Raise `ValueError` in `understand`; do NOT fabricate a PRD |
| `viability_band == "reject"` | Warn (non-fatal); planner runs only when explicitly invoked post-approval |
| LLM returns unparseable JSON for a stage | Fenced-code cleanup → retry that stage once → empty list/partial for that section, lower coverage |
| Coverage < threshold | Regenerate once with strict "trace-or-drop" prompt; still low → `confidence="low"` |
| PRD persistence (S3/UDAL) fails | Log + `prd_s3_uri=None`; PRD still returned in-band so Architect can read from RunState |

---

## 9. Downstream unblock

1. AF-039 ✅ → **AF-040 Architect (Pillar 2)** extracts FRs/NFRs/use-cases from the PRD (its `understand` parses `prd` → requirements).
2. AF-048/049 land → swap `JinjaPromptRegistry`/`GeminiRouter` for real registry + router (protocols unchanged).
3. Pillar 3 (Coder) builds against `user_stories` + `acceptance_criteria`.
4. Pillar 4 (Reviewer) asserts coverage against the same acceptance criteria.
5. Pillar 7 (LLMOps) consumes coverage + token traces via `learn()`.

> **Cross-team contract (act now):** the `PRD` + `Requirement` shapes in §4.2 are the agreement with Kaushlendra (Pillar 2). His `architect/extract_requirements` node consumes them — lock the field names before he starts AF-040 (dev-plan §"Coordination", both plans flag this as ⬜ Pending).

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| **Feature-list hallucination** (PRD invents features absent from canvas/personas) | `traces_to` field is mandatory per requirement; coverage scorer in `verify()`; strict trace-or-drop retry; low-confidence flag for human review |
| PRD schema drift vs Architect's expectation | Agree `PRD`/`Requirement` shape with Kaushlendra **now**; single shared contract (§9) |
| AF-048/049 not built → DI args undefined | Reuse shared `JinjaPromptRegistry` + `GeminiRouter` (already powering AF-037/038); contract-first |
| 4 sequential LLM calls blow latency | SLA 600s is post-gate, generous; cache short-circuit on re-runs |
| Strategy output incomplete (missing personas) | `understand` validates; degrade gracefully (fewer stories, lower coverage) rather than crash |
| 3-agent load on Somesh (dev-plan Appendix B) | PP is the lightest of the three (no tools, no API keys) — can be delegated to an early-finishing owner if the chain stalls |
