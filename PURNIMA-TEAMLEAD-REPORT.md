# Work Report for Team Lead — Purnima

> Prepared by: **Purnima** (sushe9sushe@gmail.com)
> Role: Pillar 7 Owner — LLMOps & Continuous Learning + Shared Infrastructure
> Date: 2026-06-12
> Covers: (A) Guardrails Comprehensive Specification doc, (B) AF-050 Eval Harness scaffold

This note explains, in plain language, **what I changed, why it matters to the
AutoFounder AI product, and what to review** for each piece of work.

---

## A. Guardrails Comprehensive Specification

**File:** [`docs/GUARDRAILS_COMPREHENSIVE_SPECIFICATION.md`](docs/GUARDRAILS_COMPREHENSIVE_SPECIFICATION.md)
**Branch:** `purnima-guardrails-docs` (pushed to GitHub already)
**Related task:** AF-046 (Guardrails Pipeline) — co-owned with Asit (Lead)

### What this document is
A single, complete write-up of AutoFounder AI's **6-stage guardrails pipeline**
— the safety membrane that wraps **every** AI agent call in the platform:

```
Policy → Input → Instruction → [Agent/LLM call] → Execution → Output → Monitoring
```

### My part — Output Layer & Monitoring Layer
I'm the co-owner for the last two stages. The doc specifies:

- **Output Layer** (runs after every LLM response, before it reaches the user):
  - Toxicity / content-safety scoring (TruLens)
  - Citation verification (are the sources real and relevant?)
  - Quality scoring — completeness, coherence, relevance
  - PII leak detection + redaction (also prevents cross-tenant data leaks)
  - Brand-safety and legal/regulatory compliance checks
  - **Design rule**: this layer never blocks a response — it flags, redacts,
    or adds disclaimers, so the user always gets an answer (fail-open)

- **Monitoring Layer** (runs continuously, not per-request):
  - Model drift detection (Evidently AI) — input/output/data/concept drift
  - Performance monitoring — latency, throughput, error rates
  - Anomaly detection — unusual usage, abnormal cost, suspicious tool use
  - Feedback loop — user feedback collection feeding back into AF-045 (LLMOps agent)

### Why this matters for the product
- This is the **only place** in the system where every agent's output is
  checked for safety, quality, and compliance before a customer sees it.
- It gives AutoFounder AI an **enterprise-grade audit trail** (required for
  B2B SaaS customers in regulated industries).
- The Monitoring Layer's drift/anomaly signals are the **input feed for my
  AF-045 LLMOps agent** later (it reads these signals to auto-tune prompts
  and models).

### What to review
- Read sections **"Output Layer Guardrails"** and **"Monitoring Layer
  Guardrails"** in the doc for the full spec (config YAML included).
- This is currently a **specification/design doc** — implementation already
  exists in `backend/app/guardrails/stages/output_guard.py` and
  `monitoring.py`; the doc documents/extends that design for AF-046 sign-off.

---

## B. AF-050 — Eval Harness (Promptfoo + Regression Gate)

**Branch:** `feature/eval-harness` (created from `origin/dev`, **not yet pushed**)
**Commit:** `8210752` — "feat(eval): scaffold AF-050 eval harness with Promptfoo runner + regression gate"
**Task:** AF-050 — "Eval harness — Promptfoo golden sets per agent, LangSmith
batch eval runner, CI gate blocking prompt promotion on score regression > 2%"

### What problem this solves
Every agent in AutoFounder AI (Architect, Strategy, Research, Reviewer,
Product Planner, DevOps, ...) is driven by **prompts**. Prompts get edited
over time to improve results — but a "better" prompt for one case can quietly
make another case worse. **AF-050 is the automated check that catches that
before it ships.**

### What I built today, step by step

1. **`backend/app/eval/schema.py`** — defined the result shape every eval
   produces: `EvalResult(agent, golden_set, score, baseline, regression_pct, passed)`

2. **`backend/app/eval/promptfoo_runner.py`** — runs each agent's "golden set"
   (a fixed set of test prompts + expected-behavior assertions, e.g.
   `backend/tests/golden/architect/promptfoo.yaml`) through the **Promptfoo**
   CLI, and reduces the pass/fail results to a single score from 0 to 1
   (e.g. 0.9 = 90% of test cases passed).

3. **`backend/app/eval/baseline.py`** — stores each agent's last "good" score
   in `backend/tests/golden/<agent>/baseline.json`, so future runs have
   something to compare against.

4. **`backend/app/eval/gate.py`** — the actual gate logic:
   - Runs the golden set → gets a new score
   - Compares it to the stored baseline
   - If the score **drops more than 2%**, raises `RegressionGateError`
   - If it's the first run, or the score holds/improves, saves the new score
     as the baseline

5. **`backend/app/eval/cli.py`** + **`__main__.py`** — lets CI run this with
   one command:
   ```bash
   uv run python -m app.eval architect tests/golden/architect/promptfoo.yaml
   ```
   Exit code `0` = pass, `1` = regression detected (fails the build).

6. **`backend/tests/unit/eval/`** — 20 unit tests covering all of the above
   (pass, fail, regression, first-run, zero-baseline edge cases). All passing.
   `ruff check`, `ruff format --check`, and `mypy app` all clean.

7. **`.github/workflows/eval-gate.yml`** — new GitHub Actions workflow: on any
   PR that touches an agent's prompts or golden set, it runs every agent's
   golden set and **fails the PR** if any agent's quality regresses > 2%.

8. **`Makefile`** — added `make eval-gate` so this can be run locally before
   pushing.

### Why this matters for the product
- **Prevents silent quality regressions.** Without this, a prompt tweak for
  one agent (e.g. Architect) could break another agent's output and nobody
  would notice until a customer hit it.
- **Unblocks every other pillar.** Per our team's plan, AF-050 (along with
  AF-048 Prompt Registry and AF-049 Model Router) is a **shared
  infrastructure dependency** — every pillar agent's prompt changes will run
  through this gate before merging.
- **Foundation for AF-045 (my LLMOps agent)**, which will use this same
  scoring mechanism to automatically test prompt optimizations it proposes.

### Current status / what's left
- ✅ Core harness, CLI, tests, CI workflow — **done and tested**
- 🟡 Only the **Architect agent** has a golden set today
  (`backend/tests/golden/architect/promptfoo.yaml`, pre-existing). The other
  5 agents (Strategy, Research, Product Planner, Reviewer, DevOps) each need
  their own `promptfoo.yaml` golden set — **this needs short input from each
  pillar owner** on what "correct output" looks like for their agent.
- 🟡 LangSmith batch eval runner (mentioned in the task spec) — not yet built;
  next increment.

### What to review
- `backend/app/eval/` — the harness code (5 files, ~290 lines)
- `backend/tests/unit/eval/` — tests (5 files, 20 tests)
- `.github/workflows/eval-gate.yml` + `Makefile` — CI wiring

---

## Overall Task Status Summary

| ID | Task | Status |
|----|------|--------|
| AF-046 (co-owned) | Guardrails pipeline — Output + Monitoring spec | ✅ Spec doc complete, implementation pre-existing |
| **AF-050** | Eval harness | 🟡 Core harness done; per-agent golden sets pending |
| AF-049 | LiteLLM Router + RAG | ❌ Not started |
| AF-048 | Prompt Registry | ❌ Not started |
| AF-045 | LLMOps Agent | ❌ Not started (blocked, runs last) |

---

## How to push / share for review

```bash
# A. Guardrails doc — already pushed to:
#    origin/purnima-guardrails-docs (open PR -> dev if not done yet)

# B. Eval harness — push the new branch:
git checkout feature/eval-harness
git push -u origin feature/eval-harness
# then open a PR: base = dev, compare = feature/eval-harness
```

---

## Cross-reference
- [`PURNIMA-TASKS.md`](PURNIMA-TASKS.md) — full assigned task breakdown
- [`PURNIMA-PROGRESS-NOTES.md`](PURNIMA-PROGRESS-NOTES.md) — AF-050 file-level change notes
- [`PURNIMA_WORK_REPORT.md`](PURNIMA_WORK_REPORT.md) — overall contribution history
- [`docs/GUARDRAILS_COMPREHENSIVE_SPECIFICATION.md`](docs/GUARDRAILS_COMPREHENSIVE_SPECIFICATION.md) — full guardrails spec
