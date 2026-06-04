# Pillar 5 — DevOps Agent · Detailed Plan & Review Spec

> **Owner**: Prasenjit Roy
> **Task ID**: AF-043 · **Branch**: `feature/devops-agent`
> **Pillar**: 5 — Deployment & Infrastructure
> **Phase**: 2 — MVP Builder (active design) / Phase 4 — Enterprise Scale (hardening)
> **SLA**: < 10 minutes end-to-end (excluding async HITL spend gate)
> **Status today**: Blocked on platform foundation (AF-036 `BaseAgent`, AF-027 UDAL, AF-048 Prompt Registry, AF-049 Model Router) → Start-readiness: 🟡 **Partly now** (build everything offline against the dummy CoderOutput)

---

## 1. Project context (you only need to read this once)

AutoFounder AI is a multi-tenant SaaS that turns one text idea into a live, marketed product in ~7 days. Work flows through **7 sequential pillars**, each owned by a specialist agent, all orchestrated by **LangGraph** and gated by **6 layers of guardrails**. Pillar 5 is the moment the generated, tested code stops being a repo and becomes a live URL.

### 1.1 The 9 agents (and where Pillar 5 sits)

| # | Agent | Pillar | Owner | What it produces | Hands to |
|---|---|---|---|---|---|
| 1 | Strategy & Ideation | 1 | Somesh | Lean Canvas, viability 0–100, ICPs | Product Planner |
| 2 | Research | 1 | Somesh | Market signals, competitors, citations | Strategy |
| 3 | Product Planner | 1.5 | Somesh | PRD, roadmap, user stories | Architect |
| 4 | Architect | 2 | Kaushlendra | ERD, OpenAPI, stack, cost forecast | Coder |
| 5 | Coder | 3 | Kartik | Repo (Next.js + FastAPI) + PR | Reviewer |
| 6 | Reviewer / Self-Healer | 4 | Vishal | Tested repo, ≥80% coverage, scans clean | **DevOps** |
| 7 | **DevOps (Pillar 5 — YOU)** | 5 | **Prasenjit** | **Live URL, infra, monitoring, CI/CD** | Marketer |
| 8 | Marketing | 6 | Pallavi | Brand kit, landing page, SEO, social | (LLMOps) |
| 9 | LLMOps | 7 | Purnima | Trace analysis, drift, prompt opt, FinOps | (feedback to all) |

> See `task_assigned.md` for the full 78-task plan and ownership matrix. Pillar 5 is **AF-043** only — a single agent task, but a heavy one.

### 1.2 End-to-end flow (where your output unblocks Marketing)

```
Idea → Strategy → Product Planner → Architect → Coder → Reviewer
                                                            │
                                                            ▼
                                                       ┌──────────┐
                                                       │ DevOps   │  ← Pillar 5
                                                       │ (you)    │
                                                       └────┬─────┘
                                                            ▼
                                                       Marketing → Launch
                                                            │
                                                            ▼
                                                       LLMOps (continuous)
```

### 1.3 Authoritative reads (do not skip)

| Document | Why it matters for Pillar 5 |
|---|---|
| `.claude/CLAUDE.md` | Canonical architecture (10 layers, security, multi-tenancy, ECS-on-Fargate decision). |
| `task_assigned.md` | Who owns what, what unblocks you, what your output unblocks. |
| `PLAN.md` | Sprint plan and the locked directory layout. Note: Phase 1 only ships Strategy + Research + Product Planner — Pillar 5 ships in Phase 2. |
| `docs/architecture/Agents-Architecture/devops-agent.md` | **Your LLD.** State schema, node graph, prompts, tools, error handling, output contract. Read end-to-end. |
| `docs/architecture/Agents-Architecture/coder-agent.md` (§ Output Contract, line ~2095) | The exact `CoderOutput` proto you receive. |
| `docs/architecture/Agents-Architecture/reviewer-agent.md` | What the Reviewer guarantees before your run starts. |
| `docs/architecture/HLD.md`, `LLD.md`, `architecture.md` | System-wide guardrails, observability, multi-tenant rules. |
| `.claude/specs/deployment.md`, `database.md`, `api-design.md`, `integrations.md` | Cross-cutting platform contracts. |

---

## 2. Pillar 5 expectations (the contract you must satisfy)

### 2.1 What you receive (from Reviewer / Coder)

A validated `CoderOutput` (proto in `docs/architecture/Agents-Architecture/coder-agent.md` ~L2095) describing a **tested, lint-clean, security-scanned** repo that:
- has ≥ 80% coverage,
- passes Trivy / Semgrep / Snyk,
- exposes its services + images via ECR URIs,
- carries `organization_id`, `parent_run_id`, `grandparent_run_id` (Architect), and `idea_normalised`/`domain`.

For local development you will use `.claude/specs/pillar5-dummy-input.json` (created alongside this plan).

### 2.2 What you must produce (to Marketing)

A `DevOpsOutput` (proto in `docs/architecture/Agents-Architecture/devops-agent.md` § 8) carrying:
- `live_url` (HTTPS, TLS issued),
- infrastructure inventory (ECS cluster / RDS PostgreSQL / ElastiCache / S3 bucket, region),
- CI/CD workflow path + repo URL,
- smoke-test summary (all green, P99 latency),
- monitoring handles (CloudWatch log group, Grafana URL, alarm count),
- a Markdown deploy report at `s3://autofounder-artefacts/{organization_id}/{run_id}/deploy-report.md`.

### 2.3 Sub-tasks (canonical node list — match these names)

| Node | Target SLA | Notes |
|---|---|---|
| `ingest_input` | < 15 s | Validate CoderOutput, normalise, compute cost estimate. |
| `hitl_spend_gate` | async (15 min timeout) | LangGraph `interrupt_before`; founder approves AWS spend. |
| `provision_networking` | < 3 min | Terraform: VPC, subnets, NAT, IGW, SGs. |
| `provision_compute` | < 4 min | Terraform: **ECS Fargate** cluster + services (see §3). |
| `provision_data_layer` | < 3 min | Terraform: **Amazon RDS for PostgreSQL** (private subnets, ECS-only SG, creds in Secrets Manager) + ElastiCache + S3 (see §3). |
| `provision_secrets` | < 30 s | boto3 → AWS Secrets Manager, per-tenant prefixed names. |
| `build_helm_charts` *(rename: `build_task_defs`)* | < 2 min | Generate ECS task definitions + service manifests (see §3). |
| `configure_argocd` *(rename: `configure_codedeploy`)* | < 1 min | Generate CodeDeploy appspec + deployment groups (see §3). |
| `deploy_application` | < 3 min | CodeDeploy blue/green to ECS. |
| `configure_dns_ssl` | < 1 min | Route 53 alias → ALB, ACM cert. |
| `configure_monitoring` | < 1 min | CloudWatch alarms + Prometheus scrape + Grafana. |
| `configure_cicd` | < 1 min | GitHub Actions workflow committed to tenant repo. |
| `smoke_test` | < 30 s | HTTP health checks via ALB. |
| `render_deploy_report` | < 1 min | Final Markdown → S3, build `DevOpsOutput`. |
| `error_handler` | — | Terraform destroy of partial resources, Slack alert. |

### 2.4 Non-negotiables

- **Canonical identifier (MANDATORY)**: use `organization_id` everywhere as the tenant identifier — in schemas, paths, variables, prompts, examples, log fields, JWT claims, RLS policies, proto field names. **Do NOT use `tenant_id` anywhere.** The AWS resource **tag key** stays `Tenant=` (preserved for FinOps/observability filters) but its value source is `{{ organization_id }}`. The concept words "tenant", "multi-tenant", "per-tenant" remain in prose. See `docs/learning-log.md` (2026-06-04, Option B).
- **Coding conventions (MANDATORY)**:
  - Use the latest stable library versions and idiomatic patterns of the day. Don't pin old majors out of caution.
  - Simplicity first. No over-engineering, no speculative defensive code, no extra features beyond what the task requires. Validate only at system boundaries (HTTP, queue, external API); trust internal call sites.
  - READMEs and docstrings stay minimal — one line unless a non-obvious *why* justifies more.
  - **No emojis** anywhere: code, comments, READMEs, commit messages, PR descriptions, Slack/email templates, log lines.
- **Tenant isolation**: every resource tagged `Tenant={organization_id}` `RunId={run_id}`; S3 paths and Secret names prefixed `{organization_id}/{run_id}/...`; per-tenant Terraform state in S3 with DynamoDB lock.
- **No agent touches AWS or DB directly** — all state writes go through UDAL (`packages/db`); all infra calls go through the registered tools in `packages/agents/engineering/devops/tools.py`.
- **Guardrails wrap every call**: input (validate CoderOutput), execution (tool allow-list + cost cap), output (no leaked secrets in report).
- **HITL spend gate is mandatory** — never `terraform apply` before approval.
- **Idempotency**: each node must be safe to re-run from a LangGraph checkpoint (no double-create on retry).
- **Observability tags on every signal**: `organization_id · pillar=5 · agent_id=devops · model · run_id · env`.
- **Zero-downtime**: production deploys are blue/green via CodeDeploy; rollback < 60 s.

### 2.5 Definition of done

- [ ] LangGraph subgraph compiles against the platform `RunState` (AF-033).
- [ ] `python -m autofounder_ai.agents.devops.run_local --input .claude/specs/pillar5-dummy-input.json` produces a `DevOpsOutput` JSON locally (mocked AWS).
- [ ] All 14 nodes wrapped with `with_retry` + per-node SLA timeout.
- [ ] `error_handler` calls best-effort `terraform destroy` on partial infra.
- [ ] Golden eval suite (Promptfoo) covers: HCL syntax-clean output, ECS task def schema-valid, CodeDeploy appspec schema-valid, GitHub Actions YAML lints clean.
- [ ] Unit tests ≥ 80% coverage on `nodes/`, `routers.py`, `tools.py`.
- [ ] Integration test against LocalStack (ECS, IAM, S3, Secrets Manager, Route53) passes end-to-end in CI.
- [ ] Cost-cap guard fires when `estimated_monthly_cost_usd > tenant_cap`.
- [ ] Multi-tenant isolation test: two runs cannot read each other's secrets, state, or S3 objects.
- [ ] `DevOpsOutput` proto round-trips successfully into a mocked Marketer Agent ingest.

---

## 3. Architecture reconciliation (read before writing any HCL)

The agent LLD (`devops-agent.md`) is the authoritative source. Earlier drafts of this plan listed Supabase as the tenant-MVP datastore — that has been corrected: **Supabase is reserved for the internal AutoFounder control-plane only** and is never provisioned by `provision_data_layer`. Tenant MVPs always use **Amazon RDS for PostgreSQL** (`DataLayerSpec.kind = "rds"`).

The LLD was originally written against EKS + Helm + ArgoCD; `.claude/CLAUDE.md` (§17, §48) and `task_assigned.md` (AF-013, AF-022) make the runtime authoritative as ECS-on-Fargate with CodeDeploy blue/green. Treat the LLD's *structure* (state schema, node graph, prompts, error handling, sequence diagrams) as canonical — they have already been updated to match. The substitution table below is kept for historical context:

| Earlier draft said | Authoritative today | Reason |
|---|---|---|
| EKS cluster + node groups | **ECS Fargate cluster + services + task definitions** | CLAUDE.md §17.1 |
| Helm charts (`build_helm_charts`) | **ECS task definitions + service JSON** (`build_task_defs`) | CLAUDE.md §27, §48 |
| ArgoCD Application (`configure_argocd`) | **CodeDeploy appspec.yaml + deployment group** (`configure_codedeploy`) | CLAUDE.md §17.4 |
| Supabase Postgres for tenant MVPs | **Amazon RDS for PostgreSQL** (`db.t4g.micro`, private subnets, SG=ecs_tasks only, creds in Secrets Manager) | scope rule: Supabase is control-plane-only |
| `kubectl`, `helm` tools | **`aws ecs`, `aws codedeploy`** boto3 wrappers | follows runtime |
| GitOps via ArgoCD sync | **GitHub Actions → ECR push → CodeDeploy** (AF-022) | platform CI/CD |

The cluster topology (VPC, subnets, NAT, SGs, ALB, Route53, ACM, CloudWatch, Secrets Manager, S3) is unchanged. Keep ElastiCache Redis.

> The LLD is now in sync with this plan. If a future drift appears, the LLD wins.

---

## 4. Module layout (under `packages/agents/engineering/devops/`)

```
packages/agents/engineering/devops/
├── __init__.py
├── agent.py                  # DevOpsAgent(BaseAgent) — wires LangGraph subgraph
├── schema.py                 # DevOpsState + sub-models (Pydantic v2 — copy from LLD §2,
│                             # then swap EKSCluster → ECSCluster, HelmChart → ECSTaskDef,
│                             # ArgoCDApp → CodeDeployApp; RDSInstance is the data-layer model)
├── graph.py                  # StateGraph factory + interrupt_before=["hitl_spend_gate"]
├── routers.py                # All route_after_* functions (copy from LLD §3.2)
├── nodes/
│   ├── __init__.py
│   ├── ingest_input.py
│   ├── hitl_spend_gate.py    # Redis poll (60 s interval), 15 min timeout (LLD §7.4)
│   ├── provision_networking.py
│   ├── provision_compute.py        # ECS Fargate cluster
│   ├── provision_data_layer.py     # RDS PostgreSQL + ElastiCache + S3
│   ├── provision_secrets.py
│   ├── build_task_defs.py          # was build_helm_charts
│   ├── configure_codedeploy.py     # was configure_argocd
│   ├── deploy_application.py
│   ├── configure_dns_ssl.py
│   ├── configure_monitoring.py
│   ├── configure_cicd.py
│   ├── smoke_test.py
│   ├── render_deploy_report.py
│   └── error_handler.py
├── tools.py                  # StructuredTool wrappers — terraform_run, aws_ecs_*,
│                             # aws_codedeploy_*, route53_upsert, acm_request,
│                             # secrets_manager_create, http_health_check, github_upsert_file
├── prompts/                  # Jinja2 templates — register via AF-048 Prompt Registry
│   ├── provision_networking.j2
│   ├── provision_compute.j2          # ECS Fargate variant
│   ├── provision_data_layer.j2       # RDS + ElastiCache + S3 (Terraform HCL)
│   ├── build_task_defs.j2            # ECS task definition JSON
│   ├── configure_codedeploy.j2       # appspec.yaml + deployment group
│   ├── configure_monitoring.j2
│   ├── configure_cicd.j2             # GitHub Actions workflow YAML
│   └── render_deploy_report.j2
├── utils/
│   ├── retry.py              # with_retry decorator (LLD §7.3)
│   ├── sla.py                # enforce_node_sla (LLD §7.5)
│   ├── cost.py               # estimated_monthly_cost_usd calculator
│   └── tagging.py            # mandatory resource tags
├── terraform_templates/      # Reusable HCL modules (mirror infra/terraform/)
│   ├── networking/
│   ├── ecs/
│   ├── data-layer/
│   ├── alb/
│   └── _shared/backend.tf    # S3 + DynamoDB locking (LLD §7.6)
├── run_local.py              # CLI: load dummy input → run subgraph → print DevOpsOutput
└── tests/
    ├── unit/
    │   ├── test_schema.py
    │   ├── test_routers.py
    │   ├── test_cost.py
    │   ├── test_tagging.py
    │   └── test_retry.py
    ├── integration/
    │   ├── test_localstack_e2e.py
    │   └── test_isolation.py
    ├── golden/                  # Promptfoo + LangSmith golden sets
    │   ├── provision_networking.yaml
    │   ├── build_task_defs.yaml
    │   ├── configure_codedeploy.yaml
    │   └── configure_cicd.yaml
    └── fixtures/
        └── coder_output_dummy.json  # symlink/copy of the dummy below
```

---

## 5. Independent build plan (start TODAY — no platform needed)

You are 🟡 blocked on AF-036 `BaseAgent`, AF-027 UDAL, AF-048 Prompt Registry, AF-049 Model Router. Do this in order; each item is offline-runnable against the dummy input.

### Week 1 — Schema, prompts, scaffold

1. Copy `DevOpsState` + sub-models from `docs/architecture/Agents-Architecture/devops-agent.md` §2 into `schema.py`. Apply the §3 substitutions (ECS, CodeDeploy, RDS).
2. Write all 8 Jinja2 prompt templates under `prompts/`. Validate variable shape against `DevOpsState` with strict Jinja2 (no undefined).
3. Build `utils/cost.py` — given the `services[]` list, return an `EstimatedCost` (Fargate vCPU/GB-hours, NAT, ALB, RDS class, ElastiCache node, S3 baseline, data transfer). This is what the spend-gate UI shows.
4. Build `utils/tagging.py` — emits the mandatory tag set; one source of truth used by every Terraform call and boto3 client.
5. Build `run_local.py` that reads `.claude/specs/pillar5-dummy-input.json`, instantiates `DevOpsState`, and prints it as JSON.

### Week 2 — Terraform templates + tool wrappers

6. Write reusable HCL under `terraform_templates/` for networking, ECS Fargate, data-layer (RDS PostgreSQL + ElastiCache + S3), ALB. Each module has `main.tf`, `variables.tf`, `outputs.tf`, and the shared `backend.tf` from LLD §7.6.
7. `terraform plan` each module locally against your own AWS sandbox account (or LocalStack) to prove they compile.
8. Implement `tools.py` wrappers — `terraform_run`, `aws_ecs_register_task_def`, `aws_ecs_create_service`, `codedeploy_create_application`, `codedeploy_create_deployment`, `route53_upsert`, `acm_request_certificate`, `secrets_manager_create`, `http_health_check`, `github_upsert_file`. Mock-friendly (inject a transport).

### Week 3 — Nodes + routers + retry plumbing

9. Implement every node in `nodes/` as a pure async function over `DevOpsState`. Each node returns the partial dict to merge — never mutates the state object.
10. Implement `routers.py` (copy directly from LLD §3.2 — minimal logic).
11. Implement `utils/retry.py` (LLD §7.3) and `utils/sla.py` (LLD §7.5). Decorate every node.
12. Implement `nodes/hitl_spend_gate.py` (LLD §7.4) and `nodes/error_handler.py` (LLD §7.2) — both fully testable with a fake Redis + fake boto3.

### Week 4 — Graph wiring + tests + evals

13. Implement `graph.py` with the LangGraph `StateGraph` from LLD §3.2. Use an in-memory checkpointer (Postgres comes free once UDAL lands).
14. Implement `agent.py` — `DevOpsAgent` subclass of `BaseAgent` (stub the import; replace once AF-036 lands). `execute()` delegates to the compiled graph.
15. Write unit tests for every node + router. Golden tests (Promptfoo) for prompt outputs.
16. Write the LocalStack integration test (`tests/integration/test_localstack_e2e.py`) — spins up LocalStack, runs the full graph with a fake LLM that returns recorded fixtures, asserts a `DevOpsOutput` is produced.
17. Write the multi-tenant isolation test — two `run_local` invocations with different `organization_id` produce non-overlapping resource names, secret names, S3 paths, Terraform state keys.

### When platform foundation lands

18. Replace stubbed `BaseAgent` import with the real one (AF-036).
19. Replace direct `boto3` writes with `UDAL.object()` for artefact persistence (AF-027).
20. Register prompts in the Prompt Registry (AF-048); route LLM calls through the Model Router (AF-049).
21. Wire the agent into the orchestrator's per-pillar SQS queue (AF-035).

---

## 6. Review checklist (use during PR review against the LLD)

Use this as the PR template for `feature/devops-agent`:

**State & contract**
- [ ] `DevOpsState` matches LLD §2 (ECS / CodeDeploy / RDS substitutions applied).
- [ ] All enums (`NodeStatus`, `ApprovalStatus`, `DeployStrategy`, `InfraStatus`, `DeployStatus`) present.
- [ ] `parent_run_id` and `grandparent_run_id` carried through.
- [ ] `DevOpsOutput` proto fields match LLD §8 (incl. `rds_db_instance_identifier`, `compute_target`).

**Graph & routing**
- [ ] 14 nodes + `error_handler` registered.
- [ ] `interrupt_before=["hitl_spend_gate"]` set.
- [ ] All parallel fan-outs join at the documented barriers (`infra_join`, `deploy_join`, `postdeploy_join`).
- [ ] Every conditional edge can route to `error_handler`.

**Prompts**
- [ ] 8 templates, all use strict Jinja2 (no undefined variables).
- [ ] Resource tags emitted in every Terraform prompt.
- [ ] All secret/bucket/cluster names are `{organization_id}`-scoped.

**Tools**
- [ ] Each tool has a `StructuredTool` + Pydantic input schema.
- [ ] Timeouts ≤ LLD §4.2 limits.
- [ ] No tool reads from environment without an explicit allow-list.

**Error handling**
- [ ] `with_retry` on every node; backoff matches `RetryPolicy`.
- [ ] `error_handler` attempts Terraform destroy of partial infra (incl. RDS via the data-layer module).
- [ ] Slack webhook posted on every fatal error.
- [ ] HITL spend gate: 15 min timeout, Redis poll every 60 s.

**Security & tenancy**
- [ ] No `*:*` IAM in any HCL.
- [ ] Every S3 path prefixed with `{organization_id}/{run_id}/`.
- [ ] Every Secrets Manager name prefixed with `{organization_id}/{run_id}/` (incl. `{organization_id}/{run_id}/rds`).
- [ ] Terraform state key = `{organization_id}/{run_id}/{module}.tfstate`; DynamoDB lock present.
- [ ] ECS API endpoints accessed via VPC endpoints / private routing where applicable.
- [ ] RDS: `publicly_accessible = false`, SG inbound 5432 from ECS tasks SG only, storage encrypted, master credentials sourced from Secrets Manager (no plaintext in HCL).
- [ ] ECS task definitions inject `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` via `secrets[]` `valueFrom` against the RDS secret ARN (never `environment[]`).

**Observability**
- [ ] OTel spans on every node.
- [ ] Mandatory log fields: `organization_id · pillar=5 · agent_id=devops · model · run_id · env`.
- [ ] Per-tenant cost emitted to the FinOps Prometheus counter.

**Tests**
- [ ] Unit coverage ≥ 80% on `nodes/`, `routers.py`, `utils/`.
- [ ] LocalStack integration test passes.
- [ ] Multi-tenant isolation test passes.
- [ ] Promptfoo golden sets pass (no regression > 2%).

---

## 7. Coordination & dependencies

| Need from | What | When |
|---|---|---|
| Asit | AF-027 UDAL, AF-028 FastAPI bootstrap, AF-033 `RunState`, AF-036 `BaseAgent` | Blocking — required before live integration. |
| Asit (pair) | Share the **platform** Terraform modules (AF-012–021); reuse, don't fork. | Now — your *product* infra mirrors the *platform* infra. |
| Vishal (Pillar 4) | Stable shape of `CoderOutput` (already locked in `coder-agent.md`). | Reference only. |
| Pallavi (Pillar 6) | Confirm the `DevOpsOutput` fields Marketing actually needs. | Before PR. |
| Purnima | Register your 8 prompts in AF-048, register your task class in AF-049's router, plug your golden set into AF-050. | Before PR-merge. |

---

## 8. The dummy input file

A realistic `CoderOutput` (post-Reviewer) is provided at:

**`.claude/specs/pillar5-dummy-input.json`**

Use it via `python run_local.py --input ../../.claude/specs/pillar5-dummy-input.json`. The file is shaped exactly to the proto in `docs/architecture/Agents-Architecture/coder-agent.md` (~L2095) and contains two services (`api-gateway`, `web`) with ECR URIs, all the IDs you need (`run_id`, `parent_run_id`, `grandparent_run_id`, `organization_id`), and the upstream artefact pointers (Architect's ERD + OpenAPI).

Modify it freely while developing — keep the field names stable.

---

*Pillar 5 Plan v1.1 — 2026-06-04 — feature/devops-agent*
