# Purnima — My Tasks (AutoFounder AI)

> Personal task sheet, built from `.claude/task_assigned.md`, `.claude/PLAN.md`, `.claude/TASKS.md`,
> and `.claude/developer-plans/08-purnima-pillar-7-llmops-plan.md` (origin/dev).
> Read this before starting implementation — it's the "what do I actually need to build, in what order" view.

---

## 1. What I own

| ID | Task | Branch | Depends on | Status |
|----|------|--------|------------|--------|
| AF-048 | Prompt Registry — versioned Jinja2 templates in `prompt_registry` table + S3; `get()` resolves active/canary; deterministic canary split; strict variable validation | `feature/prompt-registry` | AF-025 ✅ | ❌ Not built |
| AF-049 | LiteLLM Model Router + RAG — task-class → model routing (Gemini 3.5 Flash; gemini-embedding-2 768-dim); hybrid BM25 + ANN on Supabase pgvector; Cohere reranking; context compression; citation check | `feature/model-router-rag` | AF-027 ✅, AF-014 ✅ | ❌ Not built |
| AF-050 | Eval harness — Promptfoo golden sets per agent, LangSmith batch eval runner, CI gate blocking prompt promotion on score regression > 2% | `feature/eval-harness` | AF-048 | ❌ Not built |
| AF-045 | LLMOps Agent (Pillar 7) — trace analysis, DSPy prompt optimisation, Promptfoo regression, LiteLLM routing updates, TruLens drift monitoring, A/B experiments, FinOps report; weekly Step Functions cycle | `feature/llmops-agent` | AF-036 ✅, **all 9 agents running** (🟡 4/9 live) | ❌ Not built — runs LAST |

**Build order:** AF-050 → AF-049 → AF-048 → AF-045 (registry/router/eval ship first — they unblock every other pillar's agent; the LLMOps agent ships last because it needs live traces).

---

## 2. Current reality (per origin/dev plan, 2026-06-04)

- Foundation is delivered: AF-036 BaseAgent ✅, AF-027 UDAL ✅, AF-025 migrations ✅, AF-014 Supabase pgvector ✅.
- **AF-048 / AF-049 / AF-050 are now the team's top blocker** — every pillar agent's prompts and model routing wait on these.
- AF-045 (LLMOps agent) is blocked: 4/9 agents live (Pillar 1 agents AF-037/038/039 + Reviewer AF-042); AF-040/041/043/044 still pending.

---

## 3. Immediate action items (start now)

| # | Task | Priority | Est. | Output |
|---|------|:--------:|------|--------|
| 1 | AF-050 Eval harness + Promptfoo golden-set runner scaffold | P0 | 5 hrs | `backend/app/eval/` |
| 2 | AF-049 LiteLLM Router rules (task-class → Gemini 3.5 Flash) | P0 | 5 hrs | `backend/app/llm/router.py` |
| 3 | AF-049 RAG pipeline (hybrid BM25+ANN, rerank, citation) | P0 | 6 hrs | `backend/app/rag/` |
| 4 | AF-048 Prompt Registry loader + versioning + canary split | P0 | 5 hrs | `backend/app/prompts/registry.py` |
| 5 | Drift monitoring (TruLens/Evidently) + FinOps report logic | P1 | 4 hrs | `backend/app/llmops/drift.py`, `finops.py` |
| 6 | Coordinate golden sets + prompts with every pillar owner | P0 | 2 hrs | per-agent contributions |

~27 hrs of offline/foundational work before AF-045 can start.

---

## 4. File structure to produce

```
backend/app/
├── prompts/registry.py               # AF-048
├── llm/router.py                     # AF-049
├── rag/                               # AF-049 (query rewrite, hybrid retrieve, rerank, compress, citation)
├── eval/                               # AF-050 (Promptfoo runner + CI gate)
└── agents/llmops/
    ├── agent.py  graph.py  schema.py  # AF-045
    ├── nodes/ (trace_analysis, prompt_optimise, model_route_update,
    │           drift_monitor, ab_experiment, finops_report)
    └── prompts/ (*.j2)
```

---

## 5. Shared APIs I provide to other pillars

```python
prompt_registry.get(name, tenant) -> resolves active/canary
llm_router.complete(task_class, messages) -> routes to model + applies RAG
eval_harness.run(agent, golden_set) -> score, gate on >2% regression
```

---

## 6. Testing checklist (from the dev plan §9)

- Mock UDAL + `FakeLLM` + recorded trace fixtures for tests (no live LangSmith needed).
- `tests/unit/`: prompt registry resolution, router rules, RAG pipeline, eval gate (>2% blocks).
- `tests/integration/`: full weekly cycle (analyse → optimise → gate → canary), drift → rollback.
- `tests/golden/`: per-agent Promptfoo golden sets.

```bash
cd backend && uv run pytest tests/unit/ -v
cd backend && uv run pytest tests/integration/ -v
cd backend && npx promptfoo eval --config tests/golden/promptfoo.yaml
```

---

## 7. Cross-reference

- Full technical plan: `.claude/developer-plans/08-purnima-pillar-7-llmops-plan.md` (on `origin/dev`)
- Ownership table: `.claude/task_assigned.md` § Team Roster, § Part B.8
- Master plan: `.claude/PLAN.md`
- Task tracker: `.claude/TASKS.md`
