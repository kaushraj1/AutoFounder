# Purnima — Progress Notes (AF-050 Eval Harness)

> Prepared for: Team Lead review
> Date: 2026-06-12
> Branch with this work: ` AF-050 -- feature/eval-harness` (created from `origin/dev`)
> Commit: `8210752` — "feat(eval): scaffold AF-050 eval harness with Promptfoo runner + regression gate"

---

## 1. What I built this session (AF-050 — Eval Harness)

AF-050 = "Eval harness — Promptfoo golden sets per agent, LangSmith batch eval
runner, CI gate blocking prompt promotion on score regression > 2%"

**Core module: `backend/app/eval/`**

| File | What it does |
|---|---|
| `schema.py` | `EvalResult` model — `agent`, `golden_set`, `score`, `baseline`, `regression_pct`, `passed` |
| `promptfoo_runner.py` | Runs `npx promptfoo eval --config <path> --output <json>`, parses the JSON results into a 0–1 pass-rate `score` |
| `baseline.py` | Reads/writes `tests/golden/<agent>/baseline.json` — the "last known good" score per agent |
| `gate.py` | `run_gate()` — runs the golden set, compares score vs. baseline, raises `RegressionGateError` if the score drops more than **2%**; auto-saves the first score as the baseline |
| `cli.py` / `__main__.py` | Command-line entrypoint for CI: `uv run python -m app.eval <agent> <config.yaml>` |

**Tests: `backend/tests/unit/eval/`**
- 20 unit tests covering the runner, baseline store, gate logic (pass/fail/regression/zero-baseline), and CLI exit codes
- All passing; `ruff check`, `ruff format --check`, and `mypy app` are all clean

**CI / tooling**
- `.github/workflows/eval-gate.yml` — new workflow that runs every agent's golden set (`backend/tests/golden/*/promptfoo.yaml`) on PRs touching prompts or golden sets, and fails the PR if any agent regresses > 2%
- `Makefile` — added `make eval-gate` to run the same check locally

---

## 2. My assigned tasks — completion status

| ID | Task | Branch | Status |
|----|------|--------|--------|
| **AF-050** | Eval harness — Promptfoo + regression gate | `feature/eval-harness` | 🟡 **Core harness built & tested.** Still needed: golden sets (`promptfoo.yaml`) for the other 5 agents (architect's already existed) + LangSmith batch-eval runner — needs coordination with pillar owners |
| AF-049 | LiteLLM Model Router + RAG | `feature/model-router-rag` | ❌ Not started |
| AF-048 | Prompt Registry (versioned Jinja2 + canary) | `feature/prompt-registry` | ❌ Not started |
| AF-045 | LLMOps Agent (Pillar 7) | `feature/llmops-agent` | ❌ Not started — blocked, runs last |

**Score: 0/4 fully complete, 1/4 (AF-050) in progress with working code merged-ready.**

Build order (per plan): **AF-050 → AF-049 → AF-048 → AF-045**. AF-050's
infrastructure is done; next up is AF-049.

---

## 3. Files changed / added (this commit)

```
.github/workflows/eval-gate.yml          (new)
Makefile                                  (added `eval-gate` target)
backend/app/eval/__init__.py              (new)
backend/app/eval/__main__.py              (new)
backend/app/eval/baseline.py              (new)
backend/app/eval/cli.py                   (new)
backend/app/eval/gate.py                  (new)
backend/app/eval/promptfoo_runner.py      (new)
backend/app/eval/schema.py                (new)
backend/tests/unit/eval/__init__.py       (new)
backend/tests/unit/eval/test_baseline.py  (new)
backend/tests/unit/eval/test_cli.py       (new)
backend/tests/unit/eval/test_gate.py      (new)
backend/tests/unit/eval/test_promptfoo_runner.py (new)
backend/tests/unit/eval/test_schema.py    (new)
```

17 files changed, 896 insertions(+).

---

## 4. Step-by-step — push this branch so your team lead can see it

You're currently on branch **`feature/eval-harness`**, which already has this
work committed locally. To share it:

1. **Push the branch to GitHub:**
   ```bash
   git push -u origin feature/eval-harness
   ```

2. **Open a Pull Request** (GitHub will print a link after the push, or go to
   the repo on GitHub and click "Compare & pull request"):
   - Base branch: `dev`
   - Compare branch: `feature/eval-harness`
   - Title suggestion: `feat(eval): AF-050 eval harness — Promptfoo runner + regression gate`

3. **In the PR description**, you can paste the summary from Section 1 above
   so your team lead can review what's done vs. what's still pending.

4. **Share the PR link** with your team lead for review.

---

## 5. Cross-reference

- Full task breakdown: [`PURNIMA-TASKS.md`](PURNIMA-TASKS.md)
- Detailed work history/report: [`PURNIMA_WORK_REPORT.md`](PURNIMA_WORK_REPORT.md)
- Eval harness code: [`backend/app/eval/`](backend/app/eval/)
- Eval harness tests: [`backend/tests/unit/eval/`](backend/tests/unit/eval/)
