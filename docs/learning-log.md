# AutoFounder AI — Learning Log

Append-only project journal. Newest entries at the bottom.

---

## 2026-06-04 — Pillar 5 DevOps Agent: ECS-only sync with `devops-agent.md`

- **Topic**: Reconcile `docs/architecture/Agents-Architecture/devops-agent.md` LLD with the authoritative spec in `.claude/CLAUDE.md` (ECS Fargate + AWS CodeDeploy blue/green + Supabase PostgreSQL+pgvector) and with `.claude/specs/Pillar5-PLAN.md`. Prior LLD hardcoded EKS / Helm / ArgoCD / RDS which contradicted §17, §18 and §48 of CLAUDE.md.

- **Key decisions**:
  - Ship **one compute target first** — `ecs_fargate` — and defer a multi-stack dispatcher (S3+CloudFront, Lambda+APIGW, EKS) behind `NotImplementedError` guards. The strategy-dispatcher pattern keyed on `ArchitectOutput.stack.target` is the correct long-term shape but costs 4× prompts + 4× Terraform modules + 4× tool sets + 4× golden eval suites; not worth it for Phase 1.
  - Renamed graph nodes: `build_helm_charts` → `build_task_defs`, `configure_argocd` → `configure_codedeploy`. Topology (14 nodes + `error_handler`) is unchanged.
  - Replaced Pydantic sub-models: `EKSCluster`/`EKSNodeGroup` → `ECSCluster`/`ECSService`; `RDSInstance` → `SupabaseRef`; `HelmChart`+`ArgoCDApp` → `ECSTaskDef`+`CodeDeployApp`. `DevOpsState` field renames followed.
  - Frontend (Next.js 14, port 3000) + Backend (FastAPI, port 8000) deploy as **two ECS Fargate services in one cluster** behind a shared ALB with host/path-based listener rules. `services: list[ServiceManifest]` already supports N services — no schema change needed for multi-service deploys.
  - Added forward-compat field `compute_target: str = "ecs_fargate"` to both `DevOpsState` and the `DevOpsOutput` proto so a future dispatcher can widen without breaking the Marketer contract.
  - New AWS tool wrappers in §4: `ecs_register_task_def`, `ecs_update_service`, `codedeploy_create_deployment`, `acm_request_certificate`. Removed `kubectl`, `helm_cli`, `argocd_sync`.

- **Key insights**:
  - The LangGraph topology is naturally **stack-agnostic** — only the leaf node bodies + Pydantic sub-models hardcode the runtime. That makes a future dispatcher cheap on the graph layer.
  - `services: list[ServiceManifest]` was already N-service capable; the historical doc just talked about it as if it were single-service.
  - Single source of truth for stack choice should be `ArchitectOutput.stack.target` (Architect Agent decides; DevOps Agent dispatches). Today DevOps validates this is `"ecs_fargate"` and errors otherwise.
  - `compute_target` on `DevOpsOutput` lets the Marketer Agent (and LLMOps) attribute cost + behaviour per stack once more targets exist.

- **Gotchas**:
  - **HITL spend gate timeout drift**: LLD §7.5 says 15 min / 60 s poll; `Pillar5-PLAN.md` says 10 min / 30 s poll. Must pick one before scaffolding `packages/agents/engineering/devops/` — currently still inconsistent.
  - **Architect Agent LLD is stale**: `architect-agent.md` still references NestJS / Auth0 / EKS / RDS in its prompts. Generated `stack.json` must include `target: "ecs_fargate"` so DevOps `ingest_input` can validate it. Separate sync PR needed; out of scope for this Pillar 5 pass.
  - **VPC security-group enum** changed: drop `'eks_nodes'` and `'rds'`; use `'alb'`, `'ecs_tasks'`, `'redis'`. Supabase Postgres is reached via the Supabase-managed TLS endpoint with credentials from Secrets Manager — no in-VPC SG (until a future VPC-peering option).
  - Future Lambda/APIGW or S3/CloudFront targets will break several nodes per-target (no ALB → `provision_data_layer` Redis SG changes; API Gateway custom domain instead of Route 53 alias for the Lambda case; no ECS task metrics for `configure_monitoring`). Each new target needs a compatibility matrix before adding.
  - CodeDeploy blue/green to ECS requires **two ALB target groups per service** (prod + test listener); the compute Terraform module must provision both up-front or CodeDeploy will fail at first deployment.
  - From `/memories/lessons.md`: re-confirm IAM least-privilege when adding the new ECS/CodeDeploy/ACM tool wrappers — the task execution role and task role need to be scoped to the per-tenant Secrets Manager prefix and per-tenant S3 path, not `*`.

- **Status**: `devops-agent.md` now matches `Pillar5-PLAN.md` and CLAUDE.md §17/§18/§48. Ready for `packages/agents/engineering/devops/` scaffold. Architect Agent LLD sync queued separately.


## 2026-06-04 � Architect Agent LLD sync with DevOps + HITL timeout decision

- **Topic**: Bring `docs/architecture/Agents-Architecture/architect-agent.md` in line with the ECS-Fargate + Supabase + FastAPI authoritative stack so the Architect emits a valid handoff for the DevOps Agent's `ingest_input`. Resolve the HITL spend-gate timeout drift between `Pillar5-PLAN.md` (10 min / 30 s) and `devops-agent.md` (15 min / 60 s).
- **Key decisions**:
  - HITL spend gate canonical values: **15 min timeout, 60 s poll**. Founder-facing infra approval is deliberative (cost review, context switch); SSE push handles snappy UX, so the poll interval is a fallback only � 60 s reduces Redis load.
  - `Pillar5-PLAN.md` updated to match LLD (15 min / 60 s).
  - Add `TechStack.target: str = "ecs_fargate"` (Pydantic) and `ArchitectOutput.compute_target = 24` (proto) so DevOps Agent gets the discriminator field it validates.
  - Swap Prisma ORM for **SQLAlchemy 2.x + Supabase migration SQL** throughout schema, prompts, linter, sequence diagrams, render_doc, and proto.
  - Auth provider: **Auth0 -> Supabase Auth** (OAuth 2.0 + SSO add-on for SAML 2.0). Frees us from Auth0 vendor + bundles into the Supabase plan.
  - API gateway language: **NestJS -> FastAPI (Python 3.12)** � all backend now Python (matches CLAUDE.md �13).
  - Compute target in microservice map: drop `EKS pod | Lambda | ECS task` enum, hardcode `"ECS Fargate task"` for v1.0.
  - Linter swap: `lint_prisma` (npx prisma validate) -> `lint_db_schema` (py_compile + ruff for SQLAlchemy + sqlfluff postgres dialect for Supabase SQL).
  - Scaling-plan prompt rewritten from k8s HPA to **ECS Service Auto Scaling** (target-tracking on `ECSServiceAverageCPUUtilization` / `ALBRequestCountPerTarget`); cooldowns split into scale-out 60 s / scale-in 300 s.
  - AWS cost forecast baseline: drop EKS+RDS line items, add ECS Fargate vCPU/GB-hours + Supabase Pro plan + ALB + ACM (free). AWS Pricing API calls: `AmazonECS` / `AmazonElastiCache` instead of `AmazonEKS` / `AmazonRDS`.
- **Key insights**:
  - The Architect LLD is the **single source of truth for the stack triple** (compute target, ORM, auth provider). Every downstream agent (Coder, DevOps, Marketer) reads `stack.json` for its bootstrap � keep the proto stable and discriminator-keyed.
  - `target` lives on `TechStack` (not `MicroserviceMap`) because it's a deployment-tier decision, not a service-decomposition one. Microservices inherit it via `deployment_unit = "ECS Fargate task"`.
  - Supabase consolidates 3 prior choices (Postgres, pgvector, Auth) into one platform line item � net cost forecast simplification.
  - When the future multi-stack dispatcher lands, `TechStack.target` becomes a discriminated union; `MicroserviceMap.services[].deployment_unit` widens accordingly. No proto field renumbering needed.
- **Gotchas**:
  - Supabase Auth's SAML SSO is on the Pro plan add-on � pricing forecast in 5.7 currently assumes Pro base + usage; if a tenant needs Enterprise SSO bundled, the per-tenant COGS jumps. Flag in cost optimisation suggestions.
  - SQLAlchemy + RLS coexistence: SQLAlchemy doesn't manage Postgres RLS policies � those live only in the Supabase migration SQL. The lint pass enforces both files but the Coder Agent must run them in order (migration first, then SQLAlchemy `Base.metadata.create_all` skipped because Supabase owns DDL).
  - The proto added two new fields (23 `supabase_migration_s3_uri`, 24 `compute_target`). Coder Agent + DevOps Agent gRPC stubs must regenerate before they will deserialise the new payload.
  - `deployment_unit` enum tightening to `"ECS Fargate task"` only is a **breaking change** for any prompt golden eval that produces `"EKS pod"` or `"Lambda"`. Update golden fixtures.
  - Legacy S3 artefact path `schema.prisma` is gone; downstream consumers must read `models.py` + `migration.sql` instead. Search Coder Agent LLD and `packages/agents/engineering/coder/` once that scaffold lands.


## 2026-06-04 - Naming standard: `tenant_id` -> `organization_id` (Option B)

- **Topic**: Reconcile field-name drift between authoritative `CLAUDE.md` (`organization_id`) and the Pillar 5 LLDs / dummy input (`tenant_id`) before any code or DB schema lands.
- **Decision**: Adopt `organization_id` as the single canonical identifier name across all field/var/path uses. Chose **Option B**: keep the AWS resource tag KEY `Tenant=` unchanged (only the value source becomes `{{ organization_id }}`) so existing FinOps/observability filters that group by `Tenant=` keep working.
- **Scope of rename** (97 replacements across 4 files):
  - `docs/architecture/Agents-Architecture/devops-agent.md` (53)
  - `docs/architecture/Agents-Architecture/architect-agent.md` (30)
  - `.claude/specs/Pillar5-PLAN.md` (13)
  - `.claude/specs/pillar5-dummy-input.json` (1, key only - value left as opaque string)
- **What changed**: Pydantic field `tenant_id` -> `organization_id`; Jinja2 vars `{{ tenant_id }}` -> `{{ organization_id }}`; Python attrs `state.tenant_id` -> `state.organization_id`; S3 path templates `{tenant_id}/{run_id}/...` -> `{organization_id}/{run_id}/...`; Secrets Manager prefixes; Terraform `var.tenant_id` -> `var.organization_id`; CloudWatch log group templates; sequence-diagram payloads; LLM-judge rubric (`Missing organization_id isolation`); DB schema mandate (`All tables must include id, organization_id (FK), created_at, updated_at`); RLS policy bodies (`USING (organization_id = (auth.jwt() ->> 'organization_id')::uuid)`); HTTP header `x-tenant-id` -> `x-organization-id`.
- **What was preserved**:
  - AWS tag KEY `Tenant=` (Option B).
  - Protobuf field NUMBERS (e.g., `string organization_id = 3;` - number 3 unchanged, wire-format compatible; only the generated Python attr name changes, which is a compile-time break that helpfully catches missed call sites).
  - The concept word "tenant" in prose ("multi-tenant", "per-tenant", "tenant isolation") - semantic, not an identifier.
- **Key insights**:
  - Cheapest possible moment to do this rename: BEFORE any code, migrations, or live data exist. After this point the cost is N x schema migrations + RLS policy rewrites + JWT claim re-issuance + per-tenant data backfill.
  - Verified other agent LLDs (strategist/coder/reviewer/marketer/llmops) had zero `tenant_id` hits - they should adopt `organization_id` directly when those fields are introduced.
  - JWT claim name is `organization_id`; RLS policies must read `auth.jwt() ->> 'organization_id'`; UDAL must extract `organization_id` from verified JWT before any tenant-scoped query.
- **Gotchas**:
  - Anyone editing AWS tag-based cost reports / Grafana queries: the tag KEY stays `Tenant`, not `OrganizationId`. Don't "fix" it.
  - When regenerating proto stubs, expect a compile-time break on every consumer that referenced `msg.tenant_id` - fix the attr name, the wire bytes are unchanged.
  - Slack/email message LABEL text `Tenant:` (user-facing display) was deliberately left as-is; only the Python attribute feeding it was renamed.
- **Status**: All four files clean (grep verified 0 residual `tenant_id` / `x-tenant-id`). `CLAUDE.md`, `PLAN.md`, `PLAN-BUILD-SEQUENCE.md`, `architecture.md` were already correct.


## 2026-06-04 - Project coding conventions (locked)

- **Topic**: Pin the build-style rules so every agent scaffold (Pillar 1-7) looks the same and avoids the typical AI-generated code bloat (verbose docstrings, premature abstractions, speculative defensive code, emoji decoration).
- **Rules** (mirrored into `.claude/PLAN.md` sec.5 rule 8):
  1. Use the latest stable library versions and the idiomatic pattern of the day. Don't pin old majors out of caution.
  2. Simplicity first. No over-engineering. No speculative `try/except` around code paths that cannot raise. No extra config knobs, factories, or abstraction layers until a second caller demands them.
  3. Validate only at system boundaries (HTTP request, queue consumer, external API response). Trust internal call sites.
  4. README and docstring length: one line unless a non-obvious *why* needs explaining. Never restate what the code already says.
  5. No emojis anywhere - code, comments, READMEs, commit messages, PR descriptions, Slack templates, log lines.
  6. Use `organization_id` as the canonical tenant identifier in every field/path/var/log. Never `tenant_id`. AWS tag key `Tenant=` is the single preserved exception (FinOps compatibility).
- **Why now**: Pillar 5 scaffold (`packages/agents/engineering/devops/`) is the first agent skeleton landing in-repo. If we don't lock the house style here, the next 6 agents will each drift in their own direction and code review becomes an opinion fight instead of a correctness check.
- **Applied to**: Pillar 5 DevOps scaffold (64 files) - all stub docstrings are one-line, no emojis, no defensive scaffolding code, no helper modules invented before a node needs them. The `tests/fixtures/coder_output_dummy.json` stub was kept (one line) because the plan calls for a per-package fixture; the real dummy at `.claude/specs/pillar5-dummy-input.json` remains the source of truth.
- **Enforcement**: future PR reviews should reject - on sight - multi-paragraph docstrings, emoji, `tenant_id`, defensive code without a justifying comment, and abstractions with one caller.
