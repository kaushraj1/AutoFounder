# AutoFounder AI — Current Status of Development

> **Snapshot date:** 2026-06-06 · **Author:** Vishal (via Claude) · **Method:** verified against real code (5-agent fan-out, 66 backend tests run), **not** copied from the task doc.
> **Companion to** [`.claude/task_assigned.md`](task_assigned.md) (the plan/ownership SSoT). This file = *what is actually built right now*, claim-vs-reality.

---

## 0. TL;DR

- **Backend foundation (Phase 3a) is genuinely real and tested** — migrations, UDAL, FastAPI bootstrap, auth are done and 66 tests pass. **Two claimed-done tasks are overstated:** `AF-030` REST endpoints are **partial** (real schema/ORM mismatch — see §4 P0) and `AF-031` realtime is **scaffold-only**.
- **PR #12 (Somesh) is solid work** implementing the orchestrator (`AF-032→AF-035`). **Verdict: APPROVE_WITH_NITS.** It is mergeable after resolving **one docs conflict** (`.claude/TASKS.md`); all code merges clean. A few non-blocking prod-path nits to fix as follow-ups. → §3.
- **Phase 2 infra (`AF-012→AF-024`) — Vishal's next pickup — is ~greenfield.** 0 Terraform files. The only real shipped work is CI (`backend-ci.yml` + `lint.yml`, done) and structlog JSON logging. CD workflows exist but are **inert** (target AWS resources that don't exist). → §5.
- **Everything else (agents AF-036–050, frontend AF-051–062, mobile AF-063–071, vscode AF-072–078) is honest Phase-1 scaffold** — `NotImplementedError` stubs / `placeholder.ts`. The task doc marks these ❌ and reality agrees. → §6.

---

## 1. Branch & repo reality (verified)

| Item | Reality |
|---|---|
| Your branch | `vishal-feature-branch` == `dev` == `origin/dev` == **`88ff6fb`** (identical SHAs) — clean base to work from |
| PR #12 | author `someshnaman`, branch **`somesh-feature`** @ `3957b5f` → base `dev`. Reviewer = you (`Vishal-ml-ds`) |
| PR #12 merge-base | **`ec1fd2e`** (NOT dev HEAD). Branch diverged from an old base; `dev` is ~30 commits ahead. **Not a fast-forward.** |
| Merge result | 3-way merge = **1 conflict: `.claude/TASKS.md`** (docs). All code auto-merges clean. No committed conflict markers anywhere. |
| ⚠️ Decoy branch | `origin/somesh-feature-branch` @ `0244739` "test_again" (note the `-branch` suffix) is **stale / NOT the PR**. Do not merge it. |
| ⚠️ Decoy dir | root-level `website/` is a **real Vite+React landing site** (what `deploy-frontend.yml` ships) — it is **NOT** the Next.js 14 Founder Portal of `AF-051..062`. Don't mistake it for frontend progress. |

---

## 2. Verified status by phase (claim → actual)

Legend: ✅ done · 🟫 partial · 🟪 scaffold-only (stub, compiles, no logic) · ❌ not-started

| Phase | Tasks | Doc claim | **Verified reality** |
|---|---|---|---|
| **1 — Monorepo** | AF-001..011 | ✅ 11/11 | ✅ workspace scaffolds confirmed present |
| **2 — Infra & Cloud** | AF-012..024 | ❌ ~all | **0 done.** AF-012–021,014,024 ❌ · AF-022 🟫 (CI done, CD inert) · AF-023 🟫 (JSON logs done, OTel unused) |
| **3a — Core API/Data** | AF-025..032 | ✅ 7 / ❌ 1 | AF-025/026/027/028/029 ✅ · **AF-030 🟫 (overstated)** · **AF-031 🟪 (overstated)** · AF-032 ⏳ in PR #12 |
| **3b — Orchestrator** | AF-033..035 | ❌ | ⏳ **delivered by PR #12** (in `dev`, engine.py is still a stub) |
| **3c — Agents** | AF-036..045 | ❌ | AF-036 🟫 (contract only, no error-hierarchy/circuit-breakers) · AF-037/038/039 🟪 · AF-040..045 ❌ |
| **3d — Guardrails/Reg/Router/Eval** | AF-046..050 | ❌ | AF-046 🟫 (1/6 stages, `run()` raises) · AF-047/048/049/050 ❌ (DB tables only) |
| **4 — Frontend** | AF-051..062 | ❌ | 🟪 scaffold-only (`placeholder.ts`, no Next/React/Tailwind) |
| **5 — Mobile** | AF-063..071 | ❌ | 🟪 scaffold-only (no Expo deps) |
| **6 — VS Code Ext** | AF-072..078 | ❌ | 🟪 scaffold-only (no `main`/`activationEvents`/`contributes`) |

**Honest tally (in `dev`, excluding PR #12):** ✅ ~16 (11 monorepo + 5 foundation) · 🟫 ~4 (AF-022, AF-023, AF-030, AF-036, AF-046 partials) · 🟪 ~6 stubs · ❌ remainder. PR #12 adds 4 more (AF-032–035) once merged.

---

## 3. PR #12 — Review verdict (you are the reviewer)

**Scope (verified, +4376/−232, 61 files): `AF-032` Redis · `AF-033` LangGraph StateGraph · `AF-034` HITL gate manager · `AF-035` SQS worker.** All four **fully implemented**, not stubs.

### Verdict: ✅ **APPROVE_WITH_NITS** — safe to merge to `dev` after the 1 doc conflict; fix nits as follow-ups.

**Strengths**
- `DualCheckpointer` (Postgres authoritative + Redis 24h hot cache), fully parameterized SQL, `ON CONFLICT` upsert, graceful Redis degradation.
- Strong tenant isolation: cache keys always `org:{org_id}:…`, explicit cross-tenant isolation tests (`test_cache`).
- Production-grade SQS worker: blocking boto3 correctly offloaded via `asyncio.to_thread`, exponential backoff + jitter (cap 900s), DLQ escalation, clean shutdown.
- Authentic protoc 5.29.0 gRPC `pb2` files (not hand-edited). ~59 real test functions across 8 files (backoff, DLQ, gate routing, checkpoint persistence).
- New gate columns + `orchestrator.checkpoints` / `step_events` already provisioned by the existing tenant-schema migration — **no missing migration**.

**Nits to fix (none are merge-blockers — prod paths are not active yet)**
| # | Sev | File | Issue |
|---|---|---|---|
| 1 | med | `orchestrator/events/consumer.py` | Blocking `boto3.receive_message`/`delete_message` called **directly in the async loop** (not wrapped in `asyncio.to_thread`). With a real SQS queue + long-poll, stalls the whole event loop up to 20s. (worker.py does this right; consumer doesn't.) |
| 2 | med | `backend/pyproject.toml` | `grpcio` is **not a runtime dep** (only `grpcio-tools`, dev group). Prod `import grpc` in `worker._grpc_dispatch` would `ImportError`. Add `grpcio` (+ likely `langgraph`) to the prod/optional group. |
| 3 | med | CI | `test_graph`/`test_engine`/`test_engine_persistence` use `pytest.importorskip('langgraph')` and are **silently skipped** — PR doesn't make CI run `uv sync --group agents`. High-value tests aren't actually executing in CI. |
| 4 | low | `proto/agent_worker.proto` | No documented proto-regen step; `pb2` pins protobuf 5.29.0. Add a `make regen-proto` + pin runtime. |
| 5 | low | `orchestrator/worker.py` | `engine.resume(gate_decision='approved')` after every successful step conflates "step ok" with "HITL approved" — harmless while nodes are stubs, wrong once real gates land (revisit at AF-036+). Internal gRPC channel is `insecure_channel` (no mTLS) — document as VPC-internal hardening follow-up. |

### Recommended merge path (clean — drops the stale-base diff noise)
> Do **not** be alarmed by GitHub's "Files changed" showing deleted deploy workflows / resurrected `website/dist` — that's the stale branch point, not the merge outcome.

```bash
# Cleanest: rebase the PR branch onto current dev, then merge.
git fetch origin
git checkout somesh-feature && git rebase origin/dev      # resolve the 1 TASKS.md conflict here
# (or ask Somesh to rebase — it's his branch; coordinate before force-pushing)

# Alternative (local merge into dev, simplest to "push to dev"):
git checkout dev && git pull
git merge origin/somesh-feature                            # ONE conflict: .claude/TASKS.md
#   -> keep the union of both task-status updates, then:
cd backend && uv run pytest                                # confirm green before pushing
git push origin dev
```
**Tell me "merge PR #12" and I'll walk you through it / do the local merge + conflict resolution + test run.** (I won't touch it until you say so.)

---

## 4. Real gaps that matter (not just "not built yet")

These are **genuine issues in claimed-done code**, surfaced honestly. Two are owned by Somesh/Asit — flag to them, don't silently fix.

- **P0 — `AF-030` schema/ORM mismatch (real correctness bug, hidden by mocks).** REST endpoints use the legacy *flat* SQLAlchemy models (`models/run.py` → `public.runs`), but at runtime `search_path` points at `org_*.runs` (the canonical tenant tables from the `AF-026` migration) whose columns differ entirely (`organization_id`, `idea_text`, `cost_usd`, `current_pillar` …). Against a **real provisioned tenant DB these queries fail or mismap.** `submit_idea` (`ideas.py:33-44`) **never persists `idea.text`** — the submitted idea is silently dropped. Every endpoint test mocks the `AsyncSession`, so this is **never exercised** → green tests give false confidence. *Owner: Somesh (AF-030). Needs a migration/testcontainers integration test + model alignment.*
- **P1 — Dev-only auth bypass (by design, security-relevant).** Prod auth IS enforced (verified by `test_auth.py` prod cases). But in non-prod: no token → falls back to `DEV_PRINCIPAL` (`deps.py:45-46`); OPA returns `allow` on offline/non-200 (`opa.py:56-64`); `config.py` ships `supabase_jwt_secret='change-me-in-dev'`. Matches the prior 2026-06-04 audit's "open auth" finding — acceptable for dev, must never reach prod config. *Owner: Asit/Somesh.*
- **AF-031 realtime is scaffold-only:** only the `pg_notify` trigger exists (migration); **no backend consumer/LISTEN/WebSocket/SSE**. The ✅ in the doc overstates it (🟡 in the plan column is accurate).
- **AF-022 CD is inert:** `deploy-prod.yml`/`deploy-staging.yml` are real workflows but target ECR/`autofounderai-cluster`/ECS services that **have no Terraform backing** (0 `.tf`). "Canary" = `sleep 120` + `force-new-deployment`, **not** CodeDeploy blue/green. → fixing this is literally your Phase-2 work below.
- **AF-036 BaseAgent** is a real `Agent` ABC contract but **missing 2 of 3 spec deliverables**: no typed error hierarchy, no circuit breakers. Blocks all pillar agents (incl. your AF-042).

---

## 5. What Vishal picks up next — `AF-012 → AF-024` (Phase 2 Infra)

Reassigned to you from Asit (per Somesh, 2026-06-06). **Status: ~greenfield Terraform.** `infra/terraform/` + `infra/codedeploy/` = `.gitkeep` only.

| ID | Module | State | Note |
|---|---|---|---|
| AF-012 | networking (VPC, subnets, NAT, endpoints) | ❌ | **Start here** — everything depends on it |
| AF-013 | ecs (Fargate cluster, tasks, autoscale) | ❌ | cluster name CD expects: `autofounderai-cluster`; services `autofounderai-backend-{prod,uat}`; task def `autofounderai-backend` |
| AF-014 | Supabase project (link, RLS, pgvector) | ❌ | RLS/pgvector/tenant schemas already exist via Alembic — this is the *hosted project link*, not the schema |
| AF-015 | elasticache (Redis 7) | ❌ | PR #12's Redis client expects this in prod |
| AF-016 | s3 (artifacts, RLHF lake, Object Lock) | ❌ | |
| AF-017 | messaging (Kafka/EventBridge/SQS/SNS) | ❌ | PR #12 worker/HITL emit to EventBridge + SQS — they need these |
| AF-018 | alb (ALB/HTTPS/CloudFront/WAF) | ❌ | depends on AF-013 |
| AF-019 | iam (least-priv roles) | ❌ | no wildcard `*:*` |
| AF-020 | secrets (Secrets Mgr/SSM/KMS) | ❌ | replaces the `change-me-in-dev` defaults for prod |
| AF-021 | ecr (repos, scan, lifecycle) | ❌ | CD pushes to `${ECR_REGISTRY}/autofounderai/backend` — repo doesn't exist yet |
| AF-022 | CI/CD | 🟫 | **CI done.** Wire CD to real infra; replace sleep-canary with CodeDeploy blue/green (`infra/codedeploy/` empty) |
| AF-023 | OTel baseline | 🟫 | **JSON logs done.** Add OTel SDK + FastAPIInstrumentor + the mandatory `trace_id·org_id·run_id·agent_id·model·env` fields + Fluent Bit |
| AF-024 | Prometheus + Grafana | ❌ | deps declared-but-unused; add `/metrics`, dashboards, LangSmith wiring |

> **Sequencing:** `AF-012 → AF-019/020/021 (parallel) → AF-013 → AF-015/016/017 → AF-018`, then close the CD loop (AF-022) and observability (AF-023/024). Coordinate with **Prasenjit (AF-043 DevOps agent)** — his product-Terraform mirrors your platform-Terraform; share modules.

**Your own assignment, `AF-042` (Reviewer/Self-Healer agent), is ❌ not-started and blocked on `AF-036` (BaseAgent) + `AF-041` (Coder agent).** You can still build its offline pieces now (sandbox runner, Trivy/Semgrep/Snyk wrappers, self-heal state machine) per the task doc.

---

## 6. Scaffold-only surfaces (honest, intentional — owned by others)

`frontend/`, `mobile-app/`, `vscode-extension/`, and the Pillar agents are all byte-identical Phase-1 scaffolds (`package.json` + `README.md` + `tsconfig.json` + `src/placeholder.ts`) or `NotImplementedError` stubs with clear "lands in Sprint 1" messages. **This is not broken — it's planned, unstarted work owned by Raunak / Yogesh / Asit / pillar leads.** Don't conflate not-built-yet with defective.

---

## 7. Immediate next actions

1. **Review & merge PR #12** → say the word; resolve the 1 `TASKS.md` conflict, run tests, push `dev`.
2. **File the 3 medium PR nits** (boto3 `to_thread`, `grpcio` runtime dep, CI `--group agents`) as follow-up issues for Somesh — non-blocking.
3. **Flag the AF-030 schema mismatch + dropped `idea_text`** to Somesh (real bug, owner = him).
4. **Start `AF-012` Terraform networking** on a fresh `feat/infra/terraform-networking` branch.

---

## 8. Update — 2026-06-06 (Phase 2 progress)

Since the snapshot above was written:

- **PR #12 merged** into `dev` (merge commit `3d3266d`) — orchestrator AF-032–035 is now in `dev`.
- **Phase 2 infra started by Vishal** on branch `feat/infra/terraform-networking` (each batch validated with real `terraform validate`; pending PR → `dev`):
  - ✅ **10/13** — `AF-012` networking · `AF-013` ecs · `AF-014` supabase-config · `AF-015` elasticache · `AF-016` s3 · `AF-017` messaging (AWS-native; Confluent deferred) · `AF-018` alb (ALB+WAFv2; CloudFront/Shield deferred) · `AF-019` iam · `AF-020` secrets · `AF-021` ecr (account-global stack `infra/terraform/global/`).
  - **Remaining Phase 2:** `AF-022` CI/CD (CI done, CD pending), `AF-023` OTel (JSON logs done), `AF-024` Prometheus/Grafana.
  - ⚠️ Fixed a `.gitignore` trap: the broad `env/` (venv) rule had excluded `infra/terraform/env/` from every prior infra commit — backfilled the staging/production tfvars + backend configs (commit `ee7a980`).
- Trackers synced: [`.claude/TASKS.md`](TASKS.md), [`.claude/task_assigned.md`](task_assigned.md).

§0–§7 above reflect the pre-infra state and are kept for reference.
