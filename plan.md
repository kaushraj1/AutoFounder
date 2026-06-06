# AF-036 — `BaseAgent` ABC — Implementation Plan

> **Task:** ⭐ `BaseAgent` ABC — `understand()`, `plan()`, `execute()`, `verify()`, `learn()`; typed error hierarchy; circuit breakers on LLM + tool calls. **Blocks ALL agents.**
> **Owner:** Asit Piri (Platform Lead) · shared
> **Branch:** `feature/base-agent`
> **Depends on:** AF-027 UDAL ✅ (done)
> **Priority:** P0 — critical path. Flips 7 pillar owners from 🟡 → 🟢.
> **Est:** ~4 hrs (per `01-asit-platform-foundation-plan.md` §10.8)
> **File:** `backend/app/agents/base.py`

---

## 1. Why this task matters

AF-036 is the **agent contract** every one of the 9 specialised agents subclasses. Until it lands, all pillar owners (Somesh AF-037/038/039, Kaushlendra AF-040, Kartik AF-041, Vishal AF-042, Prasenjit AF-043, Pallavi AF-044, Purnima AF-045) are 🔴 **blocked** on wiring a *running* agent — they can only build prompts/schemas/tools offline.

Source of truth:
- `.claude/developer-plans/01-asit-platform-foundation-plan.md` §3.2 (ABC sketch), §10.7 (output contract), §10.8 (action items)
- `.claude/specs/agents.md` §7.2 (capabilities), §7.3 (contract)
- `.claude/task_assigned.md` rows AF-036
- `.claude/TASKS.md` / `.claude/PLAN.md` critical path

---

## 2. Current state (GAP ANALYSIS)

`backend/app/agents/base.py` **already exists** but is a **Phase-1 stub**. It is NOT the spec'd `BaseAgent`.

### What exists today ✅
- A plain `Agent(ABC)` with the 5 abstract lifecycle methods.
- Pydantic I/O models: `AgentInput`, `Intent`, `Step`, `Plan`, `StepEvent`, `AgentOutput`, `VerifyResult`, `ExecutionTrace`.
- `StrategyAgent` / `ResearchAgent` / `ProductPlannerAgent` subclass `Agent` and `raise NotImplementedError` (offline placeholders).

### What is MISSING vs AF-036 spec ❌
| # | Required (spec §3.2) | Status |
|---|----------------------|--------|
| 1 | Class named `BaseAgent`, `Generic[TIn, TOut]` | ❌ currently `Agent`, non-generic |
| 2 | Class attrs `PILLAR: int`, `AGENT_ID: str`, `SLA_SECONDS: int` | ❌ only `id` + `capabilities` |
| 3 | DI `__init__(udal, checkpointer, tool_registry, prompt_registry, llm_router)` | ❌ no `__init__` |
| 4 | **Typed error hierarchy** | ❌ absent entirely |
| 5 | **Circuit breakers on LLM + tool calls** | ❌ absent entirely |
| 6 | `learn()` emits trace to LLMOps | ⚠️ method exists, no emit wiring |

### Dependency reality check
- **UDAL** ✅ — `app.db.udal.UDAL(principal, session, redis)`
- **Checkpointer** ✅ — `app.orchestrator.checkpointer.DualCheckpointer(session_factory, redis)`
- **Tool Registry (AF-047)** ❌ NOT built — `backend/app/tools/` does not exist
- **Prompt Registry (AF-048)** ❌ NOT built — only an alembic `prompt_registry` table migration exists
- **LLM Router (AF-049)** ❌ NOT built

> **Consequence:** `__init__` injects `tool_registry`, `prompt_registry`, `llm_router` that don't exist yet. Solution → type them as `Protocol`s / `Any` so `BaseAgent` lands NOW without waiting on AF-047/048/049. Pillar owners get the contract; the real impls plug in later (contract-first principle, §3.1).

---

## 3. Design decisions

1. **Keep backward compat.** Existing `Agent` + Pydantic models stay (3 agents import them). Add `BaseAgent` alongside; optionally alias `Agent = BaseAgent` later. Do NOT break `strategy/research/product_planner` imports.
2. **Contract-first DI via Protocols.** Define `ToolRegistryProtocol`, `PromptRegistryProtocol`, `LLMRouterProtocol` so AF-036 ships before AF-047/048/049. Real classes satisfy the protocol structurally.
3. **Circuit breakers in-process, zero new deps.** Hand-rolled async `CircuitBreaker` (CLOSED → OPEN → HALF_OPEN) wrapping LLM + tool calls. Avoids adding `pybreaker`/`tenacity` to keep `uv` lockfile lean. Configurable `failure_threshold`, `reset_timeout`.
4. **Typed error hierarchy** rooted at `AgentError`, carrying `agent_id`, `run_id` context for observability/EventBridge `agent.failed` emit (§10.6).
5. **Generic[TIn, TOut]** for type-safe pillar I/O while staying Pydantic-friendly.

---

## 4. Implementation — `backend/app/agents/base.py`

### 4.1 Typed error hierarchy
```python
class AgentError(Exception):
    """Root of all agent failures. Carries observability context."""
    def __init__(self, message: str, *, agent_id: str | None = None,
                 run_id: str | None = None, cause: Exception | None = None):
        ...

class UnderstandError(AgentError): ...   # input parse / intent failure
class PlanError(AgentError): ...         # decomposition failure
class ExecuteError(AgentError): ...      # step execution failure
class VerifyError(AgentError): ...       # self-critique hard failure
class LearnError(AgentError): ...        # trace emit failure (non-fatal upstream)

class ToolError(AgentError): ...         # tool call failed
class LLMError(AgentError): ...          # model call failed
class CircuitOpenError(AgentError): ...  # breaker rejected call (fail-fast)
class SLAExceededError(AgentError): ...  # SLA_SECONDS budget blown
```

### 4.2 Circuit breaker
```python
class CircuitState(str, Enum):
    CLOSED = "closed"; OPEN = "open"; HALF_OPEN = "half_open"

class CircuitBreaker:
    """Async circuit breaker for LLM + tool calls.
    failure_threshold consecutive failures -> OPEN; after reset_timeout -> HALF_OPEN;
    one success in HALF_OPEN -> CLOSED. OPEN rejects with CircuitOpenError (fail-fast)."""
    def __init__(self, *, failure_threshold: int = 5, reset_timeout: float = 30.0,
                 name: str = "breaker"): ...
    async def call(self, fn: Callable[..., Awaitable[T]], *a, **kw) -> T: ...
```
- Two breakers per agent instance: `self._llm_breaker`, `self._tool_breaker`.
- Helper wrappers: `async def _call_llm(...)` and `async def _call_tool(...)` route through the breakers so subclasses never call `self.llm` / `self.tools` raw.

### 4.3 Protocols (contract-first stand-ins for AF-047/048/049)
```python
class ToolRegistryProtocol(Protocol):
    async def call(self, tool_name: str, args: dict) -> dict: ...
class PromptRegistryProtocol(Protocol):
    def get(self, key: str, version: str | None = None) -> str: ...
class LLMRouterProtocol(Protocol):
    async def complete(self, *, task_class: str, prompt: str, **kw) -> str: ...
```

### 4.4 `BaseAgent`
```python
TIn = TypeVar("TIn"); TOut = TypeVar("TOut")

class BaseAgent(ABC, Generic[TIn, TOut]):
    PILLAR: int
    AGENT_ID: str
    SLA_SECONDS: int = 1800   # default 30 min

    def __init__(self, udal, checkpointer, tool_registry,
                 prompt_registry, llm_router, *,
                 breaker_failure_threshold: int = 5,
                 breaker_reset_timeout: float = 30.0):
        self.udal = udal
        self.checkpointer = checkpointer
        self.tools = tool_registry
        self.prompts = prompt_registry
        self.llm = llm_router
        self._llm_breaker = CircuitBreaker(name=f"{self.AGENT_ID}.llm", ...)
        self._tool_breaker = CircuitBreaker(name=f"{self.AGENT_ID}.tool", ...)

    # --- guarded helpers subclasses use ---
    async def _call_llm(self, *, task_class, prompt, **kw): ...   # via _llm_breaker -> LLMError/CircuitOpenError
    async def _call_tool(self, tool_name, args): ...             # via _tool_breaker -> ToolError/CircuitOpenError

    # --- lifecycle (5 abstract methods) ---
    @abstractmethod
    async def understand(self, input: TIn) -> dict: ...
    @abstractmethod
    async def plan(self, intent: dict) -> dict: ...
    @abstractmethod
    async def execute(self, plan: dict) -> TOut: ...
    @abstractmethod
    async def verify(self, output: TOut) -> dict: ...
    @abstractmethod
    async def learn(self, trace: dict) -> None: ...

    # --- optional orchestration template (non-abstract) ---
    async def run(self, input: TIn) -> TOut:
        """understand->plan->execute->verify->learn under SLA budget + breakers.
        Wraps each phase, maps raw exceptions into the typed hierarchy,
        enforces SLA_SECONDS via asyncio timeout, emits trace in finally."""
```

> **Subclass-contract enforcement (test T8, §9.5):** missing `PILLAR`/`AGENT_ID`/`SLA_SECONDS` or any abstract method must fail fast (at instantiation). Use `__init_subclass__` to assert the required class attrs are set.

---

## 5. Backward-compatibility shim

The existing `Agent` + Pydantic models are imported by 3 agents. Keep them. Recommended:
- Retain `Agent` (Phase-1 simple ABC) **and** add `BaseAgent` (AF-036 contract) in the same module, OR
- Migrate the 3 agents to `BaseAgent` in a follow-up (AF-037+ owner work), not in AF-036.

**Decision:** AF-036 = land `BaseAgent` + errors + breaker + protocols only. Do NOT rewrite the 3 placeholder agents here (that is each pillar owner's job). Just ensure imports stay green.

---

## 6. Step-by-step build order

1. Add `CircuitState`, `CircuitBreaker` (async, unit-test in isolation first — TDD).
2. Add typed error hierarchy (`AgentError` + 8 subclasses).
3. Add the 3 `Protocol`s.
4. Add `BaseAgent(ABC, Generic[TIn, TOut])` with DI `__init__`, class attrs, `__init_subclass__` guard, guarded `_call_llm` / `_call_tool`, 5 abstract methods, optional `run()` template.
5. Export new symbols from `app.agents.base` (and re-export via `app/agents/__init__.py` if pattern used).
6. Keep `Agent` + Pydantic models untouched.
7. Write tests (§7).
8. `make quality` — ruff + mypy clean (type hints on all public funcs per CLAUDE.md §41).

---

## 7. Tests — `backend/tests/agents/`

| ID | Test | Type | Assert |
|----|------|------|--------|
| T-CB1 | breaker opens after N failures | unit | state → OPEN, next call → `CircuitOpenError` |
| T-CB2 | breaker half-open after reset_timeout | unit | one success → CLOSED |
| T-CB3 | breaker passes through on success | unit | returns value, stays CLOSED |
| T-ERR | error hierarchy carries agent_id/run_id | unit | all subclass `AgentError` |
| T8 | subclass missing abstract method | unit | instantiation/`__init_subclass__` fails |
| T-ATTR | subclass missing `PILLAR`/`AGENT_ID` | unit | fails fast |
| T-LLM | `_call_llm` routes through breaker, maps to `LLMError` | unit | fake router raises → `LLMError` |
| T-TOOL | `_call_tool` routes through breaker, maps to `ToolError` | unit | fake registry raises → `ToolError` |
| T-SLA | `run()` exceeds `SLA_SECONDS` | unit | `SLAExceededError` |
| T-RUN | happy-path `run()` calls 5 phases in order | unit | fake agent records call order |

Use fakes (fake LLM router, fake tool registry, fake UDAL) — no live infra (matches §9 test philosophy, mocked unit tests).

---

## 8. Acceptance criteria (Definition of Done)

- [ ] `BaseAgent(ABC, Generic[TIn, TOut])` with `PILLAR`, `AGENT_ID`, `SLA_SECONDS` + DI `__init__` matching spec §3.2.
- [ ] Typed error hierarchy rooted at `AgentError`.
- [ ] `CircuitBreaker` wraps LLM + tool calls; OPEN fails fast with `CircuitOpenError`.
- [ ] `__init_subclass__` enforces required attrs; missing abstract method fails at import/instantiation (T8).
- [ ] Contract-first `Protocol`s let AF-036 land before AF-047/048/049.
- [ ] Existing `Agent` + 3 placeholder agents still import & pass.
- [ ] `make quality` green (ruff + mypy + pytest).
- [ ] New tests under `backend/tests/agents/` pass.
- [ ] Branch `feature/base-agent`, Conventional Commit, PR to `main` (no direct push).

---

## 9. Downstream unblock (what lands next)

Once merged, the wiring order (`01-asit` §10 / `task_assigned.md` "wiring order"):
1. AF-036 ✅ → flips 7 owners 🟡 → 🟢.
2. Purnima lands AF-048 Prompt Registry + AF-049 LLM Router (real impls replace protocols).
3. Asit lands AF-047 Tool Registry shell.
4. Each pillar owner subclasses `BaseAgent`, registers tools, reads/writes via UDAL.
5. Orchestrator (AF-033 ✅) calls Pillar 1→2→3… passing `RunState`.

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| AF-047/048/049 not built → DI args undefined | Use `Protocol`/`Any`; ship contract now (contract-first) |
| Breaking 3 existing agents' imports | Keep `Agent` + Pydantic models; add `BaseAgent` alongside |
| Runaway LLM cost (§ risk register) | Circuit breakers + (later) per-tenant cost caps |
| Bus-factor 1 (Asit gates 9) | Self-contained, no infra deps → can be delegated to early-finishing owner |
