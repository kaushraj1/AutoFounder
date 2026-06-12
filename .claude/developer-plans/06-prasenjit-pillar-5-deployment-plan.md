# Pillar 5 — Deployment & Infrastructure: Technical Implementation Plan

> **Owner**: Prasenjit Roy
> **Task ID**: AF-043 · **Branch**: `feature/devops-agent`
> **Status**: 🟢 Unblocked — every hard blocker delivered (AF-036 BaseAgent · AF-027 UDAL · AF-012–021 foundation network · AF-042 Reviewer · AF-047 Tool Registry). Ready to build; only a live Coder→Reviewer handoff (AF-041) and AF-049 router remain as soft waits. Agent ❌ not built yet.
> **Date**: 2026-06-05 · **Version**: 1.1.0
> **Depends on**: AF-036 (BaseAgent) ✅, AF-027 (UDAL) ✅, AF-012–021 (Asit foundation network) ✅, AF-042 (Reviewer green repo) ✅ — all delivered
> **SLA**: < 10 min code → live (excludes async HITL gate) · Uptime 99.9% · First-run deploy success ≥ 85%
> **Ground truth (authoritative)**: [devops-agent.md](../../docs/architecture/Agents-Architecture/devops-agent.md) (LLD) and [CLAUDE.md](../CLAUDE.md) §17, §18, §27, §40, §48. This file is the developer-facing implementation summary — if it drifts, those win.

---

## Table of Contents

1. [Pillar Objective](#1-pillar-objective)
2. [Dependencies](#2-dependencies)
3. [Agent Architecture](#3-agent-architecture)
4. [Workflow Design](#4-workflow-design)
5. [Sub-Agent Recommendations](#5-sub-agent-recommendations)
6. [Tools & Integrations](#6-tools--integrations)
7. [Data Models](#7-data-models)
8. [Development Roadmap](#8-development-roadmap)
9. [Testing Strategy](#9-testing-strategy)
10. [Deliverables](#10-deliverables)

---

## 1. Pillar Objective

### 1.1 What Pillar 5 Achieves

Pillar 5 is the **launch pad**. It takes the tested, green repository (approved by Pillar 4) and ships it to a live public URL in under 10 minutes: ingest the `CoderOutput` → cost-gated HITL approval → attach to the shared foundation VPC (Asit's modules) → provision ECS Fargate + RDS PostgreSQL + ElastiCache + S3 → seed Secrets Manager → build ECS task definitions + CodeDeploy appspec → blue/green deploy → Route 53 + ACM → CloudWatch + GitHub Actions → smoke test → deploy report.

**Networking is not a DevOps responsibility.** The shared VPC, subnets, NAT, and IGW come from Asit's foundation Terraform modules (AF-012–021), consumed via a `terraform_remote_state` data source. The DevOps agent creates only product-tier overlays per MVP (ECS task SG, RDS SG, Redis SG, ALB + ALB SG, target groups, VPC endpoints). This is what prevents every MVP from minting its own VPC.

**Core mission**: Collapse "1 week to deploy" into **under 10 minutes, code → live**, at 99.9% uptime, with rollback-safe blue/green deploys and a live URL handed to Marketing (Pillar 6) and the dashboards.

### 1.2 Specific Outputs Produced

| Output Category | Deliverable | Volume |
|---|---|---|
| **Image flow** | CI/CD builds Dockerfiles → pushes to ECR; DevOps deploys ECS services by ECR URI | per service |
| **IaC** | Terraform plan + apply for the product stack (network overlays, compute, data layer) | 1 stack |
| **Foundation network attach** | `terraform_remote_state` lookup of Asit's foundation VPC + product-tier SGs / ALB / target groups | 1 overlay |
| **Compute** | ECS Fargate cluster + services + ALB target groups | 1 cluster |
| **Data layer** | **Amazon RDS for PostgreSQL** (`db.t4g.micro`, private subnets, SG=ecs_tasks only) + ElastiCache Redis + S3 bucket | 1 stack |
| **Secrets** | AWS Secrets Manager entries (per-tenant prefixed; RDS creds, app secrets) | per app |
| **DNS + SSL** | Route 53 records + ACM cert (Let's Encrypt fallback) | 1 domain |
| **Monitoring** | CloudWatch alarms + Prometheus scrape + Grafana + Sentry wiring | 1 stack |
| **CI/CD** | GitHub Actions deploy workflow (OIDC → ECR push → CodeDeploy blue/green) | 1 pipeline |
| **Live URL** | Public, smoke-tested HTTPS URL + deploy status | 1 URL |
| **Deploy report** | Markdown report at `s3://autofounder-artefacts/{organization_id}/{run_id}/deploy-report.md` | 1 doc |
| **Rollback plan** | Blue/green via CodeDeploy; rollback < 60 s | 1 plan |

### 1.3 Inputs Received from Upstream

| Source | Data Consumed | Required / Optional | Used For |
|---|---|---|---|
| **Vishal (Pillar 4)** | `CoderOutput` (post-Reviewer): repo URL, `services[]` with ECR URIs, coverage, scan verdict | **Required (critical)** | The green, image-built repo to deploy |
| **Kaushlendra (Pillar 2)** | stack selection, scaling plan, `estimated_monthly_cost_usd` | Required | Infra sizing + spend-gate threshold |
| **Asit (Platform)** | Foundation Terraform outputs from AF-012–021 (VPC ID, subnet IDs, NAT, IGW) via `terraform_remote_state` | **Required (critical)** | Network attach — DevOps never creates a VPC |

### 1.4 Outputs Produced for Downstream Consumers

| Consumer | Data Emitted | Format |
|---|---|---|
| **Pallavi (Pillar 6)** | `live_url`, DNS records, deploy status (CTA links) | JSON via RunState |
| **Raunak (Deploy Console AF-058)** | live deploy log stream, smoke result, rollback button | REST + Realtime |
| **Yogesh (Mobile)** | deploy status + live URL artifact | REST |
| **Purnima (Pillar 7)** | deploy telemetry, cost-per-deploy | Kafka / Cost Explorer |

---

## 2. Dependencies

### 2.1 Mandatory Dependencies (Hard Blockers)

| Dependency | Task ID | Owner | Why It's Mandatory | Status |
|---|---|---|---|---|
| BaseAgent ABC | AF-036 | Asit | DevOpsAgent subclasses it | ✅ Done |
| UDAL | AF-027 | Asit | Read repo ref, write deploy artifacts | ✅ Done |
| **Foundation network outputs** | AF-012–021 | Asit | `attach_foundation_network` reads VPC / subnets / SGs / NAT / IGW via `terraform_remote_state` — DevOps never creates these | ✅ Done (infra 13/13) |
| Reviewer green CoderOutput | AF-042 | Vishal | Only deploy a green repo with images already in ECR | ✅ Done (Reviewer shipped; live Coder handoff pending AF-041) |
| Tool Registry | AF-047 | Asit | Terraform / AWS / GitHub tool wrappers | ✅ Done (shell; add entries) |
| AWS account + IAM | AF-019 | Asit | Deploy target | ✅ Done |

### 2.2 Soft Dependencies (Optional but Beneficial)

| Dependency | Task ID | Owner | Fallback If Unavailable |
|---|---|---|---|
| Platform Terraform modules | AF-012–021 | Asit | Author product modules; share back |
| Architect scaling/cost | AF-040 | Kaushlendra | Default sizing per tier; estimate cost |
| LLM Router | AF-049 | Purnima | Templated Terraform without LLM tuning |
| Reviewer green repo | AF-042 | Vishal | Deploy a sample tested repo for dev |

### 2.3 Fallback Behavior Matrix

```
+----------------------------------+----------------------------------------------+
| Missing Input / Failure          | Fallback Strategy                            |
+----------------------------------+----------------------------------------------+
| Repo not approved by Pillar 4    | Block -- do not deploy unreviewed code       |
+----------------------------------+----------------------------------------------+
| terraform apply fails            | Auto-rollback; surface plan diff; retry once |
+----------------------------------+----------------------------------------------+
| Smoke test fails post-deploy     | Blue/green: keep old version live; do not    |
|                                  | cut over; alert founder                       |
+----------------------------------+----------------------------------------------+
| ACM cert pending validation      | Serve via Let's Encrypt; retry ACM async     |
+----------------------------------+----------------------------------------------+
| Infra spend > threshold          | HITL gate -- pause for founder approval      |
+----------------------------------+----------------------------------------------+
| Deploy exceeds 10 min SLA        | Continue but log SLA breach; alert           |
+----------------------------------+----------------------------------------------+
```

### 2.4 Dependency Chain Visualization

```
Vishal (Pillar 4: approved green CoderOutput with ECR image URIs)
   |
   v
Asit AF-036 BaseAgent + AF-027 UDAL + foundation network outputs (AF-012-021)
   |
   v
+--------------------------------------------------------------+
|  PRASENJIT -- AF-043 DevOps Agent (14 canonical nodes)       |
|  ingest -> hitl_spend_gate -> attach_foundation_network ->   |
|  [provision_compute || provision_data_layer] -> secrets ->   |
|  [build_task_defs || configure_codedeploy] -> deploy ->      |
|  dns_ssl -> [monitoring || cicd] -> smoke -> report          |
+--------------------------------------------------------------+
   |
   +-----------------+------------------+
   v                 v                  v
Pallavi (P6)    Deploy Console     Mobile (Yogesh)
(live_url)      (Raunak AF-058)    (deploy status)
```

---

## 3. Agent Architecture

### 3.1 Design Philosophy

A single `DevOpsAgent` LangGraph `StateGraph` with **14 nodes + 3 parallel-join barriers + 1 error handler**, gated by a mandatory HITL spend gate (`interrupt_before=["hitl_spend_gate"]`). Networking is consumed from Asit's foundation modules; compute, data layer, and post-deploy steps fan out where they can to keep the end-to-end SLA under 10 minutes. Blue/green via CodeDeploy keeps the old version live until the new one passes its smoke test.

### 3.2 DevOpsAgent Class

```python
# backend/app/agents/devops/agent.py
from app.agents.base import BaseAgent
from app.agents.devops.schema import DevOpsState

class DevOpsAgent(BaseAgent[DevOpsState, DevOpsState]):
    PILLAR = 5
    AGENT_ID = "devops"
    SLA_SECONDS = 600  # < 10 min code -> live (excludes async HITL gate)

    async def understand(self, input_state): ...   # validate CoderOutput, normalise, cost estimate
    async def plan(self, intent): ...              # build 14-node DAG
    async def execute(self, plan): ...             # delegates to compiled LangGraph
    async def verify(self, output): ...            # smoke passed, live_url reachable, rollback ready
    async def learn(self, trace): ...
```

### 3.3 Internal Node Architecture (14 nodes + error handler)

```
+---------------------------------------------------------------------------+
|                    DevOpsAgent (LangGraph StateGraph)                      |
|                                                                           |
|  +------------------+                                                     |
|  | ingest_input     |   (validate CoderOutput, compute cost estimate)     |
|  +--------+---------+                                                     |
|           v                                                               |
|  +------------------+   <-- LangGraph interrupt_before                    |
|  | hitl_spend_gate  |   (founder approves AWS spend; 15 min timeout)      |
|  +--------+---------+                                                     |
|           v (approved)                                                    |
|  +-----------------------------+                                          |
|  | attach_foundation_network   |   (terraform_remote_state → foundation;  |
|  +--------------+--------------+    create only SGs / ALB / target groups)|
|                 |                                                         |
|         +-------+-------+                                                 |
|         v               v                                                 |
|  +--------------+ +--------------------+                                  |
|  |provision_    | | provision_         |                                  |
|  |compute       | | data_layer         |  (RDS + ElastiCache + S3)        |
|  +------+-------+ +---------+----------+                                  |
|         +--------+----------+                                             |
|                  v                                                        |
|         +----------------+                                                |
|         |  infra_join    |  (barrier)                                     |
|         +-------+--------+                                                |
|                 v                                                         |
|         +-------------------+                                             |
|         | provision_secrets |  (Secrets Manager seeding)                  |
|         +-------+-----------+                                             |
|                 |                                                         |
|         +-------+-------+                                                 |
|         v               v                                                 |
|  +--------------+ +-----------------------+                               |
|  |build_task_   | | configure_codedeploy  |  (appspec.yaml + group)       |
|  |defs          | |                       |                               |
|  +------+-------+ +-----------+-----------+                               |
|         +--------+------------+                                           |
|                  v                                                        |
|         +----------------+                                                |
|         |  deploy_join   |  (barrier)                                     |
|         +-------+--------+                                                |
|                 v                                                         |
|         +-------------------+                                             |
|         |deploy_application |  (CodeDeploy blue/green to ECS)             |
|         +-------+-----------+                                             |
|                 v                                                         |
|         +-------------------+                                             |
|         | configure_dns_ssl |  (Route 53 + ACM)                           |
|         +-------+-----------+                                             |
|                 |                                                         |
|         +-------+-------+                                                 |
|         v               v                                                 |
|  +--------------+ +--------------------+                                  |
|  |configure_    | | configure_cicd     |  (GitHub Actions workflow)       |
|  |monitoring    | |                    |                                  |
|  +------+-------+ +---------+----------+                                  |
|         +--------+----------+                                             |
|                  v                                                        |
|         +-------------------+                                             |
|         | postdeploy_join   |  (barrier)                                  |
|         +-------+-----------+                                             |
|                 v                                                         |
|         +-------------------+                                             |
|         |    smoke_test     |  (HTTP health checks; fail → error_handler) |
|         +-------+-----------+                                             |
|                 v (pass)                                                  |
|         +------------------------+                                        |
|         | render_deploy_report   |  → DevOpsOutput → Marketer (Pillar 6) |
|         +------------------------+                                        |
|                                                                           |
|  Any node → error_handler: terraform destroy partial infra; Slack alert.  |
+---------------------------------------------------------------------------+
```

### 3.4 Node Responsibilities (canonical 14)

| # | Node | Responsibility | Model | SLA |
|---|---|---|---|---|
| 1 | `ingest_input` | Validate `CoderOutput`, normalise, compute cost estimate | — | < 15 s |
| 2 | `hitl_spend_gate` | Redis poll (60 s) for founder approval; 15 min timeout | — | async |
| 3 | `attach_foundation_network` | `terraform_remote_state` → foundation VPC; create only product-tier SGs / ALB / target groups / VPC endpoints. **Never creates VPC / subnets / NAT / IGW.** | Claude Sonnet | < 1 min |
| 4 | `provision_compute` | Terraform apply → ECS Fargate cluster + services | Claude Sonnet | < 4 min |
| 5 | `provision_data_layer` | Terraform apply → RDS PostgreSQL + ElastiCache + S3 | Claude Sonnet | < 3 min |
| 6 | `provision_secrets` | boto3 → AWS Secrets Manager, per-tenant prefixed | GPT-4o | < 30 s |
| 7 | `build_task_defs` | Generate ECS task definition JSON per service | GPT-4o | < 2 min |
| 8 | `configure_codedeploy` | Generate CodeDeploy appspec.yaml + deployment group | GPT-4o | < 1 min |
| 9 | `deploy_application` | CodeDeploy blue/green to ECS Fargate | — | < 3 min |
| 10 | `configure_dns_ssl` | Route 53 alias → ALB, ACM cert | GPT-4o | < 1 min |
| 11 | `configure_monitoring` | CloudWatch alarms + Prometheus scrape + Grafana | GPT-4o | < 1 min |
| 12 | `configure_cicd` | GitHub Actions workflow committed to tenant repo | GPT-4o | < 1 min |
| 13 | `smoke_test` | HTTP health checks via ALB | — | < 30 s |
| 14 | `render_deploy_report` | Assemble final Markdown deploy report → S3 → build `DevOpsOutput` | GPT-4o | < 1 min |
| — | `error_handler` | Classify failure, best-effort `terraform destroy` of partial infra, Slack alert | — | — |

---

## 4. Workflow Design

### 4.1 End-to-End Workflow

```
Step 1: INGEST     -- validate CoderOutput; compute estimated_monthly_cost_usd
Step 2: HITL GATE  -- founder approves AWS spend (15 min timeout)
Step 3: NETWORK    -- attach_foundation_network: read Asit's VPC outputs; create SGs/ALB/target groups
Step 4: INFRA      -- parallel: provision_compute (ECS Fargate) + provision_data_layer (RDS + Redis + S3)
Step 5: SECRETS    -- seed Secrets Manager with RDS creds + app secrets
Step 6: DEPLOY GEN -- parallel: build_task_defs + configure_codedeploy
Step 7: DEPLOY     -- CodeDeploy blue/green to ECS Fargate
Step 8: DNS/SSL    -- Route 53 alias + ACM cert
Step 9: POSTDEPLOY -- parallel: configure_monitoring (CW/Prom/Grafana) + configure_cicd (GitHub Actions)
Step 10: SMOKE     -- HTTP health checks via ALB; fail → error_handler (rollback)
Step 11: REPORT    -- render_deploy_report → S3; emit DevOpsOutput → Pillar 6 (Pallavi)
```

### 4.2 Orchestration Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Orch as Orchestrator
    participant Dev as DevOpsAgent
    participant TF as Terraform/AWS
    participant CD as CodeDeploy
    participant U as Founder
    participant Mkt as Marketing (Pillar 6)

    Orch->>Dev: invoke(CoderOutput with services[] & ECR URIs)
    Dev->>Dev: ingest_input (cost estimate)
    Dev->>U: hitl_spend_gate (interrupt_before; 15 min)
    U-->>Dev: approve
    Dev->>TF: attach_foundation_network (terraform_remote_state → foundation VPC)
    par Provision infra in parallel
        Dev->>TF: provision_compute (ECS Fargate)
        Dev->>TF: provision_data_layer (RDS + Redis + S3)
    end
    Dev->>TF: provision_secrets (Secrets Manager)
    par Generate deploy artefacts in parallel
        Dev->>Dev: build_task_defs (ECS task def JSON)
        Dev->>Dev: configure_codedeploy (appspec.yaml)
    end
    Dev->>CD: deploy_application (blue/green)
    Dev->>TF: configure_dns_ssl (Route 53 + ACM)
    par Post-deploy in parallel
        Dev->>TF: configure_monitoring (CW + Prom + Grafana)
        Dev->>TF: configure_cicd (GitHub Actions)
    end
    Dev->>Dev: smoke_test
    alt smoke pass
        Dev->>Dev: render_deploy_report
        Dev-->>Mkt: DevOpsOutput { live_url, ... }
    else smoke fail
        Dev->>CD: rollback (blue stays live)
        Dev->>U: alert; error_handler destroys partial infra
    end
```

### 4.3 Data Passed Between Nodes

```
ingest_input              -> services[], estimated_monthly_cost_usd
hitl_spend_gate           -> approval_status
attach_foundation_network -> vpc_config { vpc_id (foundation), subnet_ids (foundation), sg_ids, alb_arn, target_group_arns }
provision_compute         -> ecs_cluster { cluster_arn, service_arns[] }
provision_data_layer      -> rds_instance, elasticache_cluster, s3_bucket
provision_secrets         -> secrets[] (Secrets Manager ARNs)
build_task_defs           -> task_defs[] (ECS RegisterTaskDefinition requests)
configure_codedeploy      -> codedeploy_app { app_name, deployment_group, appspec_yaml }
deploy_application        -> deploy_status (HEALTHY | FAILED), deployment_id
configure_dns_ssl         -> dns_record, tls_certificate, live_url
configure_monitoring      -> monitoring_config { cloudwatch_alarms, grafana_dashboard_url, log_group_name }
configure_cicd            -> cicd_config { workflow_file_path, workflow_yaml }
smoke_test                -> smoke_test_results[], smoke_tests_passed
render_deploy_report      -> deploy_report_markdown -> DevOpsOutput -> Pillar 6 (Pallavi)
```

---

## 5. Sub-Agent Recommendations

### 5.1 Evaluation Matrix

| Proposed Sub-Agent | Recommendation | Maps to canonical node |
|---|---|---|
| Cost Estimator | ✅ Node | `ingest_input` (cost calc) drives `hitl_spend_gate` |
| Network Attacher | ✅ Node | `attach_foundation_network` (foundation reuse) |
| Compute Provisioner | ✅ Node | `provision_compute` |
| Data-Layer Provisioner | ✅ Node | `provision_data_layer` (RDS + Redis + S3) |
| Secrets Seeder | ✅ Node | `provision_secrets` |
| Deploy Artefact Builder | ✅ Two nodes | `build_task_defs` + `configure_codedeploy` |
| Deployment Orchestrator | ✅ Node | `deploy_application` (CodeDeploy blue/green) |
| DNS & SSL Agent | ✅ Node | `configure_dns_ssl` |
| Observability Agent | ✅ Node | `configure_monitoring` |
| CI/CD Agent | ✅ Node | `configure_cicd` |
| Smoke Test Agent | ✅ Node | `smoke_test` |
| Report Renderer | ✅ Node | `render_deploy_report` |
| Security & Compliance | 🔶 Shared with Pillar 4 + Guardrails | Trivy IaC scan happens in P4 |
| Rollback Agent | ✅ Merged into `error_handler` + `deploy_application` | Rollback is the failure path |

### 5.2 Final Agent Architecture

**Phase 1 (Weeks 1–4):** 14 nodes + 3 join barriers + `error_handler` per the canonical graph.
**Phase 2:** canary ramp (10% → 100%), multi-region, IaC drift detection.
**Phase 3:** spot Fargate optimisation, auto-scaling tuning, eject / AWS-account transfer.

---

## 6. Tools & Integrations

### 6.1 Per-Node Tool Registry (canonical)

| Node | Tool wrapper | Service | Purpose |
|---|---|---|---|
| `attach_foundation_network` | `terraform_run` | AWS | `terraform_remote_state` lookup + product-tier SG / ALB / target-group apply |
| `provision_compute` | `terraform_run`, `aws_ecr_login` | AWS ECS / ECR | ECS Fargate cluster + services; ensure ECR pull role |
| `provision_data_layer` | `terraform_run` | AWS RDS / ElastiCache / S3 | RDS PostgreSQL + Redis + S3 |
| `provision_secrets` | `secrets_manager_create` | AWS Secrets Manager | Per-tenant prefixed secrets |
| `build_task_defs` | (none — deterministic JSON) | AWS ECS | ECS task definition JSON per service |
| `configure_codedeploy` | (none — deterministic YAML) | AWS CodeDeploy | appspec.yaml + deployment group |
| `deploy_application` | `codedeploy_create_deployment`, `ecs_update_service` | AWS CodeDeploy / ECS | Blue/green cutover |
| `configure_dns_ssl` | `route53_upsert`, `acm_request_certificate` | AWS Route 53 / ACM | DNS alias + TLS |
| `configure_monitoring` | (boto3 in node) | AWS CloudWatch | Alarms + log groups |
| `configure_cicd` | `github_upsert_file` | GitHub API | `.github/workflows/deploy.yml` |
| `smoke_test` | `http_health_check` | — | HTTP health checks via ALB |
| `render_deploy_report` | (S3 put via UDAL) | AWS S3 | Markdown report → S3 |

### 6.2 LLM Requirements

| Node | Model | Purpose |
|---|---|---|
| `attach_foundation_network` | Claude Sonnet | Overlay HCL generation (no VPC creation) |
| `provision_compute` | Claude Sonnet | ECS Fargate Terraform |
| `provision_data_layer` | Claude Sonnet | RDS + Redis + S3 Terraform |
| `build_task_defs`, `configure_codedeploy`, `configure_dns_ssl`, `configure_monitoring`, `configure_cicd`, `render_deploy_report` | GPT-4o | Structured JSON / YAML / Markdown |

(Provisioning apply, secrets seeding, deploy, smoke, report S3 write are deterministic — no LLM.)

### 6.3 External Service Rate Limits & Fallbacks

| Service | Limit | Timeout | Retry | Fallback |
|---|---|---|---|---|
| Terraform / AWS | service quotas | 600 s (apply) | 3 × [10, 30, 60] s | Best-effort destroy on final failure |
| ECR | — | 60 s | 3 | Re-push |
| ACM | validation async | — | poll | Let's Encrypt fallback |
| CodeDeploy | — | 120 s | 1 | Auto-rollback (blue stays live) |
| AWS Cost API | quota | 20 s | 3 | Static estimate |
| Claude Sonnet / GPT-4o | per-model RPM | 30 s | 3 | Hard fail → error_handler |

### 6.4 Database & Storage Requirements

| Store | Usage | Path / Key |
|---|---|---|
| PostgreSQL (UDAL) | deploy artefacts, live_url, status | `organization_id.artifacts` |
| S3 | Terraform state, deploy logs, deploy report | `s3://autofounder-tf-state/{organization_id}/{run_id}/...` and `s3://autofounder-artefacts/{organization_id}/{run_id}/deploy-report.md` |
| Secrets Manager | RDS creds + per-app secrets | `{organization_id}/{run_id}/...` |
| Redis | HITL approval state, deploy progress | `devops:approval:{run_id}`, `devops:deploy:{run_id}` |

---

## 7. Data Models

Full `DevOpsState` schema lives in [devops-agent.md §2](../../docs/architecture/Agents-Architecture/devops-agent.md). The output contract handed to the Marketer Agent:

```python
class DevOpsOutput(BaseModel):
    run_id: UUID; parent_run_id: UUID; organization_id: str
    idea_normalised: str; domain: str

    # Live environment
    live_url: str | None = None
    deploy_strategy: str                 # rolling | blue_green | canary

    # Infrastructure identifiers
    ecs_cluster_arn: str | None = None
    rds_db_instance_identifier: str | None = None    # Amazon RDS PostgreSQL (NOT Supabase)
    elasticache_endpoint: str | None = None
    s3_bucket_name: str | None = None
    aws_region: str = "ap-south-1"

    # Deploy + CI/CD
    deploy_status: str                   # provisioning | deployed | smoke_failed | rolled_back
    deployment_id: str | None = None
    cicd_workflow_path: str | None = None
    repo_url: str

    # DNS / TLS
    dns_records: list[dict] = []
    cert_arn: str | None = None

    # Smoke + monitoring
    smoke_passed: bool = False
    cloudwatch_log_group: str | None = None
    grafana_dashboard_url: str | None = None

    # Cost + report
    monthly_cost_usd: float
    deploy_report_s3_uri: str | None = None
    rollback_ready: bool = True
    total_llm_tokens_used: int = 0
```

---

## 8. Development Roadmap

### Phase 1 — MVP (Weeks 1–4)

| Week | Task | Deliverable | Status |
|---|---|---|---|
| 1 | `DevOpsState` schema (copy from LLD §2) + Jinja2 prompts (8 templates) + cost / tagging utils | `schema.py`, `prompts/`, `utils/` | 🟢 Start now |
| 1 | `run_local.py` against `.claude/specs/pillar5-dummy-input.json` | CLI prints `DevOpsState` JSON | 🟢 Start now |
| 2 | Terraform templates: `network_overlays/` (consumes foundation via `terraform_remote_state`), `ecs/`, `data-layer/` (RDS + Redis + S3), `alb/` | `terraform_templates/` | 🟢 Start now |
| 2 | Tool wrappers in `tools.py` (`terraform_run`, `aws_ecr_login`, `aws_ecr_push`, `aws_ecs_*`, `codedeploy_*`, `route53_upsert`, `acm_request_certificate`, `secrets_manager_create`, `http_health_check`, `github_upsert_file`) | `tools.py` | 🟢 Start now |
| 2 | **Pair with Asit** to consume foundation network outputs (AF-012–021) | `network_overlays/main.tf` data source | 🟢 Pair now |
| 3 | 14 nodes + routers + `error_handler` + `with_retry` + per-node SLA | `nodes/`, `routers.py`, `utils/retry.py`, `utils/sla.py` | 🟢 Ready (AF-036 done) |
| 3 | `hitl_spend_gate` (Redis poll 60 s; 15 min timeout) | `nodes/hitl_spend_gate.py` | 🟢 Start now |
| 4 | `graph.py` + `agent.py` + LocalStack integration test + multi-tenant isolation test | `graph.py`, `agent.py`, `tests/integration/` | 🟢 Ready (AF-036 delivered) |
| 4 | Golden evals (Promptfoo) on all 8 prompts | `tests/golden/` | 🟢 Start now |

### Phase 2 (Weeks 5–7)

Real `terraform apply` against sandbox AWS; canary ramp (10% → 100%); IaC drift detection; Deploy Console contract (AF-058).

### Phase 3 (Weeks 8–11)

Multi-region; spot Fargate; auto-scaling tuning; AWS-account eject / transfer automation.

---

## 9. Testing Strategy

### 9.1 Testing Without the Full Platform

Mock UDAL; `FakeLLM` returns recorded Terraform / task-def / appspec / workflow outputs; LocalStack for ECS / IAM / S3 / Secrets Manager / Route 53; mock CodeDeploy; mock BaseAgent until AF-036 lands. Test `smoke_test` against any local app behind a fake ALB.

### 9.2 Test Architecture

```
backend/app/agents/devops/tests/
├── unit/
│   ├── test_schema.py                  # DevOpsState + sub-models
│   ├── test_routers.py                 # route_after_* functions
│   ├── test_cost.py                    # estimated_monthly_cost_usd > cap → gate
│   ├── test_tagging.py                 # mandatory tags emitted
│   ├── test_retry.py                   # with_retry backoff sequence
│   └── test_attach_foundation_network.py  # no aws_vpc / aws_subnet / aws_nat in generated HCL
├── integration/
│   ├── test_localstack_e2e.py          # full 14-node graph against LocalStack
│   ├── test_smoke_fail_rollback.py     # smoke fail → CodeDeploy rollback
│   ├── test_spend_gate.py              # 15 min timeout + reject path
│   └── test_isolation.py               # two organization_id runs cannot read each other's state
└── golden/
    ├── attach_foundation_network.yaml
    ├── provision_compute.yaml
    ├── provision_data_layer.yaml
    ├── build_task_defs.yaml
    ├── configure_codedeploy.yaml
    └── configure_cicd.yaml
```

### 9.3 Sample Data / Fixtures

| Fixture | Stack | Expected |
|---|---|---|
| `.claude/specs/pillar5-dummy-input.json` | Next.js + FastAPI + AI services | live URL, smoke pass |
| `high_cost_stack.json` | many services | spend gate fires |
| `smoke_failing_app.json` | broken healthcheck | rollback, blue stays live |
| `python_only_api.json` | FastAPI only | single-service deploy |
| `two_tenants_concurrent.json` | two `organization_id` runs | no resource / secret / state collisions |

### 9.4 Test Execution Commands

```bash
cd backend && uv run pytest app/agents/devops/tests/unit -v
cd backend && uv run pytest app/agents/devops/tests/integration -v
cd backend && uv run python -m app.agents.devops.run_local --input ../.claude/specs/pillar5-dummy-input.json
```

### 9.5 Key Test Scenarios

| # | Scenario | Type | Pass Criteria |
|---|---|---|---|
| T1 | Green CoderOutput → live URL | Integration | `deploy_status==deployed`; smoke pass |
| T2 | Smoke fail → rollback | Integration | blue stays live; founder alerted |
| T3 | Spend > threshold → gate | Integration | run pauses; 15 min timeout enforced |
| T4 | `attach_foundation_network` generates no `aws_vpc` / `aws_subnet` / `aws_nat_gateway` | Unit | HCL grep returns 0 matches |
| T5 | Terraform plan valid + no `*:*` IAM | Golden | plan succeeds; IAM scoped |
| T6 | ACM pending → Let's Encrypt fallback | Integration | serves over HTTPS |
| T7 | Unreviewed CoderOutput → blocked | Unit | `ingest_input` raises ValidationError |
| T8 | Deploy < 10 min SLA (excl. HITL) | Integration | total duration under SLA or logged breach |
| T9 | Two `organization_id` runs concurrently | Integration | no overlap in resource names / secrets / S3 paths / TF state keys |

---

## 10. Deliverables

### 10.1 File Structure

```
backend/app/agents/devops/        # (per CLAUDE.md §40 backend layout)
├── agent.py  graph.py  schema.py  routers.py
├── nodes/
│   ├── ingest_input.py
│   ├── hitl_spend_gate.py            # 60 s Redis poll, 15 min timeout
│   ├── attach_foundation_network.py  # terraform_remote_state → foundation; SGs / ALB / target groups only
│   ├── provision_compute.py          # ECS Fargate cluster + services
│   ├── provision_data_layer.py       # RDS PostgreSQL + ElastiCache + S3
│   ├── provision_secrets.py
│   ├── build_task_defs.py            # ECS task definition JSON per service
│   ├── configure_codedeploy.py       # appspec.yaml + deployment group
│   ├── deploy_application.py         # CodeDeploy blue/green
│   ├── configure_dns_ssl.py
│   ├── configure_monitoring.py
│   ├── configure_cicd.py
│   ├── smoke_test.py
│   ├── render_deploy_report.py
│   └── error_handler.py
├── tools.py                          # terraform_run, aws_ecr_*, aws_ecs_*, codedeploy_*, route53_upsert, acm_request_certificate, secrets_manager_*, http_health_check, github_upsert_file
├── prompts/                          # 8 Jinja2 templates (attach_foundation_network.j2, provision_compute.j2, ...)
├── utils/                            # retry.py, sla.py, cost.py, tagging.py
├── terraform_templates/
│   ├── network_overlays/             # SGs, ALB, target groups, VPC endpoints. NO aws_vpc / aws_subnet / aws_nat_gateway.
│   ├── ecs/
│   ├── data-layer/                   # RDS + ElastiCache + S3
│   ├── alb/
│   └── _shared/backend.tf            # S3 + DynamoDB lock
├── run_local.py                      # CLI: load dummy input → run subgraph → print DevOpsOutput
└── tests/                            # unit / integration / golden / fixtures

infra/terraform/foundation/           # Asit-owned: VPC, subnets, NAT, IGW (AF-012–021). DevOps only reads outputs.
```

### 10.2 Environment Variables (`.env.example`)

```bash
# --- Pillar 5 (DevOps) ------------------------------------------------------
ROUTE53_ZONE_ID=
CODEDEPLOY_APP=
SENTRY_DSN=
# ECR_REGISTRY, AWS_PRICING_REGION already defined; AWS creds via OIDC
```

### 10.3 Prompt Registry Entries (AF-048) — 8 templates

| Template | Version | Model | Variables |
|---|---|---|---|
| `devops/attach_foundation_network` | 1.0.0 | Claude Sonnet | `organization_id`, `run_id`, `aws_region`, `domain`, `services` |
| `devops/provision_compute` | 1.0.0 | Claude Sonnet | `organization_id`, `run_id`, `aws_region`, `services`, foundation vpc / subnet refs |
| `devops/provision_data_layer` | 1.0.0 | Claude Sonnet | `organization_id`, `run_id`, `vpc_id`, `private_subnet_ids`, `ecs_tasks_sg_id`, `rds_credentials_secret_arn` |
| `devops/build_task_defs` | 1.0.0 | GPT-4o | `services`, `rds_credentials_secret_arn`, role ARNs |
| `devops/configure_codedeploy` | 1.0.0 | GPT-4o | `ecs_cluster`, `services`, `alb_target_group_arns` |
| `devops/configure_monitoring` | 1.0.0 | GPT-4o | `ecs_cluster`, `services`, `sns_topic_arn` |
| `devops/configure_cicd` | 1.0.0 | GPT-4o | `aws_account_id`, `ecr_registry`, `codedeploy_app`, `repo_url` |
| `devops/render_deploy_report` | 1.0.0 | GPT-4o | full `DevOpsState` |

### 10.4 Tool Registry Entries (AF-047)

| Tool | Scope | Auth | Cost | Rate Limit |
|---|---|---|---|---|
| `terraform_run` | DevOps | IAM (OIDC) | Compute | quota |
| `aws_ecr_login`, `aws_ecr_push` | DevOps + CI/CD | IAM | Compute | quota |
| `aws_ecs_register_task_def`, `aws_ecs_update_service` | DevOps | IAM | Free | AWS default |
| `codedeploy_create_application`, `codedeploy_create_deployment` | DevOps | IAM | Free | AWS default |
| `route53_upsert`, `acm_request_certificate` | DevOps | IAM | Free | AWS default |
| `secrets_manager_create`, `secrets_manager_update` | DevOps | IAM | Per-secret | AWS default |
| `http_health_check` | DevOps | — | Free | local |
| `github_upsert_file` | DevOps | GitHub App PAT | Free | 5000 req/hr |

### 10.5 Prometheus Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `devops_deploy_duration_seconds` | Histogram | tenant, status | Code → live duration (< 10 min) |
| `devops_first_run_success_total` | Counter | status | First-run deploy success (≥ 85%) |
| `devops_rollback_total` | Counter | reason | Rollbacks triggered |
| `devops_monthly_cost_usd` | Histogram | tenant | Per-deploy cost |
| `devops_spend_gate_total` | Counter | outcome | Infra-spend gate hits |
| `devops_smoke_test_total` | Counter | result | Smoke pass/fail |

### 10.6 Kafka / EventBridge Events Emitted

| Event | Bus | Payload |
|---|---|---|
| `pillar.started{5}` | EventBridge | `{ run_id, reviewer_run_id }` |
| `pillar.completed{5}` | EventBridge | `{ run_id, live_url, next_pillar: 6 }` |
| `gate.required{infra_spend}` | EventBridge → UI | `{ run_id, monthly_cost_usd }` |
| `devops.deployed` | Kafka | `{ run_id, live_url, duration_s }` |
| `devops.rolled_back` | EventBridge → Slack | `{ run_id, reason }` |

### 10.7 Output Contract (DevOpsOutput protobuf)

```protobuf
syntax = "proto3";
package autofounder.devops.v1;
message DevOpsOutput {
  string run_id = 1; string organization_id = 2; string reviewer_run_id = 3;
  string repo_url = 4; string image_tag = 5;
  string live_url = 6; string deploy_status = 7;
  string cert_arn = 8; double monthly_cost_usd = 9;
  bool   rollback_ready = 10; bool smoke_passed = 11;
  string deployment_id = 12; int32 total_llm_tokens_used = 13;
}
```

### 10.8 Immediate Action Items (🟢 Start Today)

| # | Task | Priority | Output |
|---|---|---|---|
| 1 | Copy `DevOpsState` schema from LLD §2 into `schema.py` | P0 | `schema.py` |
| 2 | Write all 8 Jinja2 prompts | P0 | `prompts/*.j2` |
| 3 | `terraform_templates/network_overlays/` consuming foundation via `terraform_remote_state` | P0 | `terraform_templates/network_overlays/` |
| 4 | `terraform_templates/ecs/`, `data-layer/`, `alb/` | P0 | `terraform_templates/` |
| 5 | `tools.py` wrappers (terraform_run, ecr, ecs, codedeploy, route53, acm, secrets, http, github) | P0 | `tools.py` |
| 6 | `utils/cost.py` + `utils/tagging.py` | P0 | `utils/` |
| 7 | `nodes/hitl_spend_gate.py` (Redis 60 s / 15 min) | P0 | `nodes/hitl_spend_gate.py` |
| 8 | `nodes/error_handler.py` (best-effort destroy) | P0 | `nodes/error_handler.py` |
| 9 | `run_local.py` against `.claude/specs/pillar5-dummy-input.json` | P0 | CLI prints `DevOpsState` JSON |
| 10 | **Pair with Asit** to lock the foundation network output schema | P0 | Documented data-source contract |

**All ten are doable offline before BaseAgent (AF-036) lands.**

---

## Appendix A: Key Decisions Log

| # | Decision | Choice | Rationale |
|---|---|---|---|
| D1 | Compute target | ECS Fargate (not EKS) | CLAUDE.md §17 authoritative |
| D2 | Deploy strategy | Blue/green via CodeDeploy | Rollback-safe; blue stays live until smoke passes |
| D3 | Infra-spend gate | HITL above threshold; 15 min timeout, 60 s Redis poll | Protect founder from surprise bills; matches LLD §7.4 |
| D4 | DNS / SSL | Route 53 + ACM, Let's Encrypt fallback | Managed cert with fallback for pending validation |
| D5 | **Networking ownership** | **Foundation VPC reused from Asit's modules (AF-012–021) via `terraform_remote_state`** | One platform VPC for all MVPs; DevOps never creates a VPC |
| D6 | Data layer for tenant MVPs | **Amazon RDS for PostgreSQL** (NOT Supabase) | Supabase is reserved for the AutoFounder internal control-plane |
| D7 | Image pipeline | CI/CD generates Dockerfile (templated) → ECR push; DevOps deploys ECS services by ECR URI | ECR stores images; it does not generate Dockerfiles |
| D8 | Node graph | **14 canonical nodes + 3 parallel-join barriers + `error_handler`** | Matches devops-agent.md (LLD §3, §7) |

## Appendix B: Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Deploy regression | Medium | High | Blue/green + smoke test + 1-click rollback + canary (Phase 2) |
| Surprise infra cost | Medium | High | Cost estimate + infra-spend HITL gate + per-tenant caps |
| Terraform drift | Medium | Medium | All infra via PR + plan review; drift detection Phase 2 |
| ACM cert delays | Medium | Low | Let's Encrypt fallback; async ACM retry |
| Deploying unreviewed code | Low | Critical | Hard gate on Pillar 4 approval |
| Wildcard IAM in generated stack | Low | High | Least-privilege templates; Trivy IaC scan in Pillar 4 |

## Appendix C: Coordination Checklist

| Who | What | When | Status |
|---|---|---|---|
| **Vishal (Pillar 4)** | Agree `ReviewerOutput` → DevOps input (approved repo) | Immediately | ⬜ Pending |
| **Pallavi (Pillar 6)** | Agree `live_url` + DNS output for CTAs | Immediately | ⬜ Pending |
| **Asit (Platform)** | Share Terraform modules (AF-012-021); BaseAgent + UDAL | Phase 2 | ⬜ Pending |
| **Kaushlendra (Pillar 2)** | Stack + scaling + cost forecast for sizing/gate threshold | Soon | ⬜ Pending |
| **Raunak (Frontend)** | Deploy Console data contract (AF-058) | When mock data ready | ⬜ Pending |
| **Purnima (Pillar 7)** | Register devops prompts (AF-048) + deploy cost telemetry | When shells exist | ⬜ Pending |

---

*Auto-Founder AI — Pillar 5: Deployment & Infrastructure Technical Plan v1.1.0 | June 2026*
*Ground truth: [devops-agent.md](../../docs/architecture/Agents-Architecture/devops-agent.md) + CLAUDE.md*
*Owner: Prasenjit Roy | Ground truth: [devops-agent.md](../../docs/architecture/Agents-Architecture/devops-agent.md) + [CLAUDE.md](../CLAUDE.md) | Reviewed by: [Pending team review]*
