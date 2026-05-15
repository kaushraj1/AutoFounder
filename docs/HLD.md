# High-Level Design — Auto-Founder AI

> **Version**: 1.0 | **Status**: Draft | **Date**: May 2026
> **Owner**: Euron Auto-Founder AI Platform Team | product@euron.one
> **Classification**: Internal — Engineering

---

## Table of Contents

1. [Document Purpose & Scope](#1-document-purpose--scope)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Technology Layer Breakdown](#3-technology-layer-breakdown)
4. [The 7-Agent Pipeline](#4-the-7-agent-pipeline)
5. [Component Interactions](#5-component-interactions)
6. [Data Flow Between Agents](#6-data-flow-between-agents)
7. [Multi-Tenant Architecture](#7-multi-tenant-architecture)
8. [AWS Infrastructure](#8-aws-infrastructure)
9. [Security Architecture](#9-security-architecture)
10. [Memory & State Architecture](#10-memory--state-architecture)
11. [Observability & LLMOps](#11-observability--llmops)
12. [CI/CD Pipeline](#12-cicd-pipeline)
13. [Performance Targets](#13-performance-targets)
14. [Phased Rollout](#14-phased-rollout)
15. [Open Design Questions](#15-open-design-questions)

---

## 1. Document Purpose & Scope

This High-Level Design covers the end-to-end system architecture of **Auto-Founder AI** — an autonomous, multi-agent SaaS platform that transforms a single text idea into a fully validated, production-ready, and marketed software business.

**In scope**: Platform architecture, the 7-agent pipeline, multi-tenancy model, AWS infrastructure, security boundaries, observability, and CI/CD.

**Not in scope**: Agent-level implementation details (covered in `docs/lld/`), individual prompt templates, Terraform module internals.

**Audience**: Engineering leads, platform architects, DevOps, security reviewers, and technical investors.

---

## 2. System Architecture Overview

Auto-Founder AI is structured as a **LangGraph-orchestrated multi-agent system** deployed on AWS EKS, surfaced to founders through a Next.js portal and streamed to them in real-time via a Go WebSocket server.

```mermaid
flowchart TD
    subgraph Clients["🖥️  Client Layer"]
        FP["Founder Portal\nNext.js 14 · App Router"]
        AD["Admin Dashboard\nNext.js 14"]
        API_CLI["API Clients\nREST / gRPC"]
    end

    subgraph Edge["🌐  Edge & Gateway"]
        CF["CloudFront CDN\nStatic assets + API cache"]
        R53["Route53 DNS\nautofounderdai.euron.one"]
        ALB["Application Load Balancer\nSSL termination · WAF"]
        GW["NestJS API Gateway\nAuth · Rate limit · Tenant validation · OpenAPI"]
        WS["Go WebSocket Server\nReal-time agent log streaming"]
    end

    subgraph Orchestration["⚙️  Orchestration Layer"]
        LG["LangGraph Orchestrator\nStateGraph · Checkpointing · Fan-out · HITL"]
        CP["PostgreSQL Checkpoint Store\nGraph state persistence"]
        KF["Apache Kafka\nInter-agent event bus"]
    end

    subgraph Agents["🤖  Agent Worker Pods  (AWS EKS — ap-south-1)"]
        STR["1 · Strategist\nIdea Validation"]
        ARC["2 · Architect\nTech Stack Design"]
        COD["3 · Coder\nCode Generation"]
        REV["4 · Reviewer\nTesting & Self-Healing"]
        DEV["5 · DevOps\nDeployment & Infra"]
        MKT["6 · Marketer\nLaunch & GTM"]
        OPS["7 · LLMOps\nGrowth & Learning"]
    end

    subgraph LLMs["🧠  LLM Routing Layer"]
        CL["Claude Sonnet\nComplex reasoning\nArchitecture · Self-healing"]
        G4["GPT-4o\nCode gen · Marketing copy"]
        G4M["GPT-4o-mini\nSimple CRUD · Classification"]
        DALL["DALL-E 3\nBrand assets · Visuals"]
    end

    subgraph Data["🗄️  Data Tier"]
        RDS["PostgreSQL 16\nSchema-per-tenant\nRelational store"]
        REDIS["Redis Cluster\nSession · Agent state cache"]
        QD["Qdrant\nVector memory\nLong-term patterns"]
        ES["Elasticsearch\nFull-text search"]
        S3["AWS S3\nArtefacts · Reports · RLHF data"]
        KF2["Kafka Topics\nrun.events · agent.traces · billing.events"]
    end

    subgraph Sandbox["📦  Sandbox Layer"]
        DC["Ephemeral Docker Containers\ngVisor isolation · Egress restricted"]
        ECR["AWS ECR\nBase images · Generated app images"]
    end

    subgraph External["🔌  External Integrations"]
        GH["GitHub API\nRepo · PR · Actions"]
        STR2["Stripe\nBilling · Webhooks"]
        A0["Auth0\nOAuth2 · SAML · MFA"]
        TAV["Tavily Search"]
        SRP["SerpAPI · Crunchbase · G2"]
        BUF["Buffer · Typefully\nSocial scheduling"]
        PH["ProductHunt API"]
        SG["SendGrid · Resend\nTransactional email"]
        AWS_SVC["AWS Services\nRoute53 · ACM · Secrets Manager · CloudWatch"]
    end

    FP & AD & API_CLI --> CF
    CF --> R53 --> ALB
    ALB --> GW & WS
    GW --> LG
    LG --> CP
    LG --> KF
    LG --> STR --> ARC --> COD --> REV --> DEV --> MKT
    OPS -.->|learns from all agents| STR & ARC & COD & REV & DEV & MKT
    STR & ARC & COD & REV & DEV & MKT & OPS --> LLMs
    STR & ARC & COD & REV & DEV & MKT & OPS --> Data
    COD & REV --> Sandbox
    Sandbox --> ECR
    STR --> TAV & SRP
    ARC --> GH
    COD --> GH
    REV --> GH
    DEV --> AWS_SVC
    MKT --> BUF & PH & SG
    GW --> A0
    GW --> STR2
    WS --> REDIS

    style Clients        fill:#f0f4ff,stroke:#4f46e5
    style Edge           fill:#faf5ff,stroke:#7c3aed
    style Orchestration  fill:#fff7ed,stroke:#ea580c
    style Agents         fill:#f0fdf4,stroke:#16a34a
    style LLMs           fill:#fef2f2,stroke:#dc2626
    style Data           fill:#f0f9ff,stroke:#0284c7
    style Sandbox        fill:#fefce8,stroke:#ca8a04
    style External       fill:#f8fafc,stroke:#64748b
```

---

## 3. Technology Layer Breakdown

### 3.1 Layer summary

| Layer | Technology | Role |
|---|---|---|
| **Portal UI** | Next.js 14 (App Router), Tailwind CSS, shadcn/ui | Founder interaction, real-time build monitoring |
| **API Gateway** | NestJS (Node.js), TypeScript strict | Auth, rate limiting, tenant validation, REST + WebSocket |
| **Realtime** | Go + WebSocket | Agent log streaming (< 100ms latency) |
| **Orchestration** | LangGraph, Python | Stateful agent graphs, fan-out, checkpointing, HITL interrupts |
| **Agent Workers** | FastAPI + Python 3.11, EKS pods | 7 specialist agents, each independently scalable |
| **LLM Router** | Custom routing layer (LLMOps Agent) | Routes tasks to cheapest capable model |
| **Data — Relational** | PostgreSQL 16, Prisma | Schema-per-tenant, audit logs, 7-year retention |
| **Data — Cache** | Redis Cluster 7.x | Session state, approval signals, pub/sub |
| **Data — Vector** | Qdrant | Long-term memory, pattern retrieval |
| **Data — Search** | Elasticsearch | Full-text search across generated artefacts |
| **Data — Objects** | AWS S3 | Reports, code bundles, RLHF datasets |
| **Message Bus** | Apache Kafka | Async inter-agent events, billing events, trace logs |
| **Sandbox** | Docker + gVisor | Isolated code execution for Coder + Reviewer |
| **Container Registry** | AWS ECR | Base images + generated app images |
| **Infra** | AWS EKS, Terraform, Helm, ArgoCD | Kubernetes orchestration, GitOps CD |
| **Observability** | LangSmith, Prometheus, Grafana, CloudWatch | Tracing, metrics, cost telemetry |
| **Auth** | Auth0 | OAuth 2.0, SAML 2.0, MFA, RBAC |
| **Billing** | Stripe | Subscriptions, webhooks, billing portal |

### 3.2 LLM routing policy

```mermaid
flowchart LR
    Task["Incoming Task"] --> Router["LLMOps Router\n(cost-aware)"]

    Router -->|"Complex reasoning\nArchitecture · Self-healing\nSecurity review"| CL["Claude Sonnet\n~$15/M tokens"]
    Router -->|"Code gen · Marketing copy\nStandard analysis"| G4["GPT-4o\n~$5/M tokens"]
    Router -->|"Simple CRUD · Classification\nFormatting · Boilerplate"| G4M["GPT-4o-mini\n~$0.15/M tokens"]
    Router -->|"Visual assets\nBrand kit · Social images"| DALL["DALL-E 3\nper image"]

    G4M -->|"COGS guard\nper-task cost tracked"| OPS["LLMOps Agent\nCost telemetry"]
    CL --> OPS
    G4 --> OPS

    style CL   fill:#fef2f2,stroke:#dc2626
    style G4   fill:#f0f4ff,stroke:#4f46e5
    style G4M  fill:#f0fdf4,stroke:#16a34a
    style DALL fill:#faf5ff,stroke:#7c3aed
```

---

## 4. The 7-Agent Pipeline

### 4.1 Pipeline topology

Each agent follows the same **5-stage autonomous loop**: `Understand → Plan → Execute → Verify → Learn`. Agents communicate via gRPC (synchronous handoff) and Kafka (asynchronous events). Two **Human-in-the-Loop (HITL) gates** block forward progress until founder approval is received.

```mermaid
flowchart LR
    IDEA(["💡 Founder Idea\n(text prompt)"])

    subgraph P1["Pillar 1 · < 30 min"]
        STR["Strategist\nMarket analysis\nLean Canvas\nViability Score"]
    end

    subgraph GATE1["🔴 HITL Gate 1"]
        VS{"Viability\nBand?"}
        REJECT["❌ Notify founder\nDo not proceed"]
    end

    subgraph P2["Pillar 2 · < 45 min"]
        ARC["Architect\nOpenAPI spec · ERD\nTech stack · Cost forecast"]
    end

    subgraph GATE2["🔴 HITL Gate 2"]
        FA{"Founder\nApproved?"}
        REVISE["↩️ Revise\narchitecture"]
    end

    subgraph P3["Pillar 3 · < 15 min"]
        COD["Coder\nNext.js 14 · NestJS\nStripe · Auth0 · Tests"]
    end

    subgraph P4["Pillar 4 · < 20 min"]
        REV["Reviewer\nLint · Tests · Security\nSelf-healing · LLM judge"]
    end

    subgraph P5["Pillar 5 · < 10 min"]
        DOPS["DevOps\nTerraform · EKS\nDNS · SSL · Monitoring"]
    end

    subgraph P6["Pillar 6 · < 2 hrs"]
        MKT["Marketer\nLanding page · SEO\nProduct Hunt · Social"]
    end

    subgraph GATE3["🟡 HITL Gate 3"]
        LC["Launch\nControl Center\nFounder reviews\nbefore posting"]
    end

    subgraph P7["Pillar 7 · Continuous"]
        OPS["LLMOps\nFeedback loops\nPrompt optimization\nCost telemetry"]
    end

    IDEA --> STR
    STR --> VS
    VS -->|"reject (0–24)"| REJECT
    VS -->|"weak (25–49)\nwith pivot suggestions"| ARC
    VS -->|"moderate / strong\n(50–100)"| ARC
    ARC --> FA
    FA -->|"rejected"| REVISE --> ARC
    FA -->|"approved"| COD
    COD --> REV
    REV -->|"pass"| DOPS
    REV -->|"fail after 5 retries"| ESCALATE(["🚨 Human escalation"])
    DOPS --> MKT
    MKT --> LC
    LC -->|"approved"| LIVE(["🚀 Live MVP\n+ Marketing live"])
    LC -->|"rejected"| MKT

    STR & ARC & COD & REV & DOPS & MKT --> OPS

    style GATE1 fill:#fef2f2,stroke:#dc2626
    style GATE2 fill:#fef2f2,stroke:#dc2626
    style GATE3 fill:#fefce8,stroke:#ca8a04
    style LIVE  fill:#f0fdf4,stroke:#16a34a
    style REJECT fill:#fee2e2,stroke:#dc2626
```

### 4.2 Agent SLA summary

| Agent | Input | Output | SLA | HITL? |
|---|---|---|---|---|
| **Strategist** | Raw text idea | Market report + Lean Canvas + Viability Score | < 30 min | After: viability gate |
| **Architect** | Strategist output | OpenAPI spec + ERD + Tech stack + Cost forecast | < 45 min | Before start: founder approval |
| **Coder** | Architect artefacts | GitHub PR with full-stack repo | < 15 min | — |
| **Reviewer** | GitHub PR | Passing test suite + security scan; patched code | < 20 min | Escalate after 5 retries |
| **DevOps** | Reviewed, containerised code | Live URL + SSL + DNS + CI/CD + Monitoring | < 10 min | Before: infra spend > ₹10K |
| **Marketer** | Live MVP + brand config | SEO page + social content + launch kit | < 2 hrs | Launch Control Centre |
| **LLMOps** | All agent traces + signals | Optimised prompts + cost report + routing rules | Weekly | — |

### 4.3 Self-healing loop (Reviewer Agent)

```mermaid
flowchart TD
    PR["GitHub PR\n(from Coder Agent)"] --> LINT["Lint check\nESLint · Prettier\nBlack · Ruff"]
    LINT -->|"pass"| UNIT["Unit tests\nJest · pytest"]
    LINT -->|"fail"| PATCH1["AST-aware patch\n(LLM self-correct)"]
    PATCH1 --> LINT

    UNIT -->|"pass"| INT["Integration tests\nPlaywright · Docker sandbox"]
    UNIT -->|"fail"| PATCH2["Diagnose + patch\n(LLM self-correct)"]
    PATCH2 --> UNIT

    INT -->|"pass"| SEC["Security scan\nTrivy · Semgrep · Bandit"]
    INT -->|"fail"| PATCH3["Diagnose + patch"]
    PATCH3 --> INT

    SEC -->|"pass"| JUDGE["LLM-as-Judge\nReadability ·\nMaintainability"]
    SEC -->|"HIGH/CRITICAL CVE"| PATCH4["Security patch"]
    PATCH4 --> SEC

    JUDGE -->|"score ≥ 75"| PASS(["✅ Approved\nEmit to DevOps Agent"])
    JUDGE -->|"score < 75 · ≤ 5 retries"| PATCH5["Improve code quality"]
    PATCH5 --> JUDGE
    JUDGE -->|"fail after 5 total retries"| ESC(["🚨 Escalate to human"])

    COUNTER["Retry counter\n(max 5 across all loops)"] -.->|"check"| PATCH1 & PATCH2 & PATCH3 & PATCH4 & PATCH5

    style PASS fill:#f0fdf4,stroke:#16a34a
    style ESC  fill:#fef2f2,stroke:#dc2626
```

---

## 5. Component Interactions

### 5.1 NestJS API Gateway — request lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Founder
    participant CF  as CloudFront
    participant ALB as Load Balancer
    participant GW  as NestJS Gateway
    participant A0  as Auth0 (JWT validation)
    participant RL  as Rate Limiter (Redis)
    participant TG  as Tenant Guard
    participant LG  as LangGraph Orchestrator
    participant WS  as Go WebSocket

    Founder ->> CF: POST /api/v1/runs { idea_raw }
    CF ->> ALB: forward (TLS 1.3)
    ALB ->> GW: forward
    GW ->> A0: validate Bearer JWT (RS256)
    A0 -->> GW: { sub, tenant_id, roles }
    GW ->> RL: check rate limit for tenant_id
    RL -->> GW: 200 OK (under limit)
    GW ->> TG: validate tenant_id from JWT claims
    TG -->> GW: tenant validated
    GW ->> LG: invoke(StrategistState{ idea_raw, tenant_id, run_id })
    LG -->> GW: 202 Accepted { run_id }
    GW -->> Founder: 202 { run_id, stream_url: wss://.../{run_id} }

    Founder ->> WS: connect wss://api.../runs/{run_id}/logs
    WS ->> RL: subscribe to Redis channel run:{run_id}
    loop Agent progress events
        LG ->> RL: publish({ node, status, progress })
        RL -->> WS: event
        WS -->> Founder: SSE frame { node, status, output_preview }
    end
```

### 5.2 LangGraph Orchestrator — state machine

```mermaid
flowchart TD
    subgraph LangGraph["LangGraph Orchestrator — Agent State Machine"]
        direction LR
        ENTRY["Entry Point\nrun_id · tenant_id · idea_raw"] --> SG["StrategistGraph\nStateGraph[StrategistState]"]
        SG -->|"via gRPC\nStrategistOutput"| AG["ArchitectGraph\nStateGraph[ArchitectState]"]
        AG -->|"via gRPC\nArchitectOutput\n(post founder approval)"| CG["CoderGraph\nStateGraph[CoderState]"]
        CG -->|"via gRPC\nCoderOutput"| RG["ReviewerGraph\nStateGraph[ReviewerState]"]
        RG -->|"via gRPC\nReviewerOutput"| DG["DevOpsGraph\nStateGraph[DevOpsState]"]
        DG -->|"via gRPC\nDevOpsOutput"| MG["MarketerGraph\nStateGraph[MarketerState]"]
    end

    subgraph Checkpoint["Checkpoint Store"]
        PG["PostgreSQL\nEach graph state\ncheckpointed per node"]
    end

    subgraph HITL["HITL Interrupt Points"]
        I1["interrupt_before:\nstrategist viability gate"]
        I2["interrupt_before:\narchitect founder_approval_gate"]
        I3["interrupt_before:\ndevops infra_spend_gate"]
        I4["interrupt_before:\nmarketer launch_control_center"]
    end

    subgraph Kafka["Kafka Event Bus"]
        T1["run.events\n(status changes)"]
        T2["agent.traces\n(LLMOps input)"]
        T3["billing.events\n(token usage)"]
    end

    SG <-.-> PG
    AG <-.-> PG
    CG <-.-> PG
    RG <-.-> PG
    DG <-.-> PG
    MG <-.-> PG

    SG --> I1
    AG --> I2
    DG --> I3
    MG --> I4

    SG & AG & CG & RG & DG & MG --> T1 & T2 & T3
```

### 5.3 Sandbox execution — Coder + Reviewer

```mermaid
flowchart LR
    subgraph AgentPod["Agent Worker Pod (EKS)"]
        CA["Coder / Reviewer\nAgent Process"]
        SM["Sandbox Manager\nasync Python"]
    end

    subgraph Docker["Ephemeral Docker Sandbox"]
        C1["Container\n(gVisor runtime)"]
        FS["Isolated filesystem\n/workspace/{tenant_id}/{run_id}"]
        NET["Network policy\nEgress: npm registry,\npypi only · No inbound"]
    end

    subgraph Outputs["Sandbox Outputs"]
        LOGS["stdout / stderr\n→ Redis pub/sub"]
        ART["Build artefacts\n→ S3 upload"]
        RES["Test results\n→ ReviewerState"]
    end

    CA --> SM
    SM -->|"spin up < 10s"| C1
    C1 --- FS
    C1 --- NET
    C1 -->|"execute\n(max 30 min)"| LOGS & ART & RES
    SM -->|"always destroy\n(finally block)"| C1

    style C1   fill:#fefce8,stroke:#ca8a04
    style NET  fill:#fef2f2,stroke:#dc2626
```

---

## 6. Data Flow Between Agents

### 6.1 End-to-end data flow — idea to live MVP

```mermaid
sequenceDiagram
    autonumber
    actor Founder
    participant GW   as API Gateway
    participant STR  as Strategist Agent
    participant ARC  as Architect Agent
    participant COD  as Coder Agent
    participant REV  as Reviewer Agent
    participant DEV  as DevOps Agent
    participant MKT  as Marketer Agent
    participant OPS  as LLMOps Agent
    participant S3   as AWS S3
    participant GH   as GitHub
    participant AWS  as AWS (EKS / RDS / DNS)

    Founder ->> GW: POST /api/v1/runs { idea_raw }
    GW ->> STR: StrategistState { idea_raw, tenant_id }

    Note over STR: ~30 min · Market research · Lean Canvas
    STR ->> S3: PUT {tenant_id}/{run_id}/report.md
    STR ->> S3: PUT {tenant_id}/{run_id}/lean_canvas.json
    STR -->> GW: StrategistOutput { viability_score, report_url }
    GW -->> Founder: Dashboard: viability band + report preview

    alt viability_band == "reject"
        GW -->> Founder: "Idea scored below threshold. Pivot suggestions: ..."
    else viability_band in ["moderate","strong","weak"]
        STR -->> ARC: gRPC StrategistOutput

        Note over ARC: ~45 min · DB schema · OpenAPI · Cost forecast
        ARC ->> S3: PUT {tenant_id}/{run_id}/openapi.yaml
        ARC ->> S3: PUT {tenant_id}/{run_id}/schema.prisma
        ARC ->> S3: PUT {tenant_id}/{run_id}/architecture.md
        ARC -->> GW: interrupt: "awaiting_founder_approval"
        GW -->> Founder: Architecture preview → Approve / Reject

        Founder ->> GW: POST /runs/{run_id}/approve
        ARC -->> COD: gRPC ArchitectOutput { s3 URIs }

        Note over COD: ~15 min · Code generation · Lint · GitHub PR
        COD ->> GH: Create repo + feature branch
        COD ->> GH: Batch push 150–200 files via Trees API
        COD ->> GH: Open PR "Auto-generated MVP"
        COD -->> REV: gRPC CoderOutput { pr_url, pr_number }

        Note over REV: ~20 min · Tests · Security · Self-healing
        REV ->> GH: Fetch PR diff
        REV ->> REV: Lint → Unit → Integration → Security (max 5 cycles)
        REV ->> GH: Push fixes as additional commits
        REV ->> GH: Approve PR + merge to main
        REV -->> DEV: gRPC ReviewerOutput { commit_sha, image_tag }

        Note over DEV: ~10 min · Terraform · EKS · DNS · SSL
        DEV ->> AWS: terraform apply (EKS + RDS + ElastiCache + S3)
        DEV ->> AWS: helm install (ArgoCD sync)
        DEV ->> AWS: Route53 CNAME → ALB DNS
        DEV ->> AWS: ACM certificate validation
        DEV -->> MKT: gRPC DevOpsOutput { live_url, domain }

        Note over MKT: ~2 hrs · Copy · SEO · Social · Launch kit
        MKT ->> S3: PUT {tenant_id}/{run_id}/marketing/brand_kit.zip
        MKT -->> GW: interrupt: "launch_control_center"
        GW -->> Founder: Review all marketing drafts → Approve

        Founder ->> GW: POST /runs/{run_id}/launch/approve
        MKT ->> MKT: Schedule posts via Buffer / Typefully
        MKT ->> MKT: Submit to ProductHunt API

        GW -->> Founder: 🚀 MVP is LIVE at {live_url}
    end

    Note over OPS: Continuous — learns from all agent traces
    STR & ARC & COD & REV & DEV & MKT ->> OPS: Kafka agent.traces events
    OPS ->> S3: RLHF dataset append
    OPS ->> OPS: Weekly: DSPy prompt optimisation + A/B test
```

### 6.2 Inter-agent contract summary

| Handoff | Protocol | Key fields passed |
|---|---|---|
| Strategist → Architect | gRPC + Kafka | `run_id`, `viability_score`, `lean_canvas_json`, `report_s3_uri`, `bias_flags` |
| Architect → Coder | gRPC + Kafka | `run_id`, `openapi_yaml_s3_uri`, `prisma_schema_s3_uri`, `stack_json_s3_uri`, `overall_pattern` |
| Coder → Reviewer | gRPC + Kafka | `run_id`, `github_repo_full_name`, `pr_number`, `feature_branch`, `lint_all_passed` |
| Reviewer → DevOps | gRPC + Kafka | `run_id`, `commit_sha`, `ecr_image_tag`, `security_scan_passed`, `coverage_pct` |
| DevOps → Marketer | gRPC + Kafka | `run_id`, `live_url`, `domain`, `stack_summary`, `feature_list_s3_uri` |
| All agents → LLMOps | Kafka only (async) | `run_id`, `node_name`, `model_used`, `tokens_in`, `tokens_out`, `latency_ms`, `outcome` |

---

## 7. Multi-Tenant Architecture

### 7.1 Tenant isolation model

```mermaid
flowchart TD
    subgraph Tenant_A["Tenant A (Startup Tier)"]
        TA_UI["Portal Session\ntenant_id: acme-corp"]
        TA_POD["Agent Pod\nscoped to acme-corp builds"]
        TA_SCHEMA["PostgreSQL Schema\nacme_corp.*"]
        TA_S3["S3 prefix\ns3://.../{acme-corp}/"]
        TA_REDIS["Redis keyspace\n{acme-corp}:*"]
    end

    subgraph Tenant_B["Tenant B (Solopreneur Tier)"]
        TB_UI["Portal Session\ntenant_id: raj-saas"]
        TB_POD["Agent Pod\nscoped to raj-saas builds"]
        TB_SCHEMA["PostgreSQL Schema\nraj_saas.*"]
        TB_S3["S3 prefix\ns3://.../{raj-saas}/"]
        TB_REDIS["Redis keyspace\n{raj-saas}:*"]
    end

    subgraph Shared["Shared Infrastructure (isolated by key/schema)"]
        PG["PostgreSQL 16\nCluster"]
        RS["Redis Cluster"]
        S3B["AWS S3 Bucket"]
        EKS["AWS EKS\nKubernetes Cluster"]
        KAFKA["Apache Kafka"]
    end

    subgraph Controls["Isolation Controls"]
        JWT["JWT Claim\ntenant_id validated\non every request"]
        TG["Tenant Guard\n(NestJS)"]
        RLS["Row-Level Security\n(PostgreSQL)"]
        NS["Kubernetes Namespace\nper tenant tier"]
    end

    TA_UI --> JWT --> TG
    TB_UI --> JWT --> TG
    TG --> TA_POD & TB_POD
    TA_POD --> TA_SCHEMA --> PG
    TB_POD --> TB_SCHEMA --> PG
    PG --- RLS
    TA_POD --> TA_S3 --> S3B
    TB_POD --> TB_S3 --> S3B
    TA_POD --> TA_REDIS --> RS
    TB_POD --> TB_REDIS --> RS
    TA_POD & TB_POD --> EKS
    EKS --- NS

    style Tenant_A   fill:#f0f4ff,stroke:#4f46e5
    style Tenant_B   fill:#f0fdf4,stroke:#16a34a
    style Controls   fill:#fef2f2,stroke:#dc2626
    style Shared     fill:#f8fafc,stroke:#64748b
```

### 7.2 Database — schema-per-tenant pattern

Each tenant gets its own PostgreSQL **schema** within the shared cluster. No foreign keys cross schema boundaries. RLS is enabled as an additional defence layer.

```mermaid
erDiagram
    PUBLIC_SCHEMA {
        uuid tenants_id PK
        string tenants_name
        string tenants_tier
        string tenants_stripe_customer_id
        timestamp tenants_created_at
    }

    ACME_CORP_SCHEMA {
        uuid users_id PK
        string users_email
        string users_role
        uuid runs_id PK
        string runs_idea_raw
        string runs_status
        jsonb runs_strategist_output
        jsonb runs_architect_output
        string runs_live_url
        uuid audit_log_id PK
        string audit_log_action
        text audit_log_details
    }

    RAJ_SAAS_SCHEMA {
        uuid users_id PK
        string users_email
        uuid runs_id PK
        string runs_idea_raw
        string runs_status
    }

    PUBLIC_SCHEMA ||--o{ ACME_CORP_SCHEMA : "tenant_id FK (cross-schema ref)"
    PUBLIC_SCHEMA ||--o{ RAJ_SAAS_SCHEMA  : "tenant_id FK (cross-schema ref)"
```

### 7.3 Storage isolation

| Resource | Isolation mechanism | Path pattern |
|---|---|---|
| S3 objects | Bucket policy + IAM condition key on `s3:prefix` | `s3://autofounder-artefacts/{tenant_id}/{run_id}/` |
| Redis keys | Key namespace prefix enforced in SDK wrapper | `{tenant_id}:{resource}:{id}` |
| Kafka topics | Topic-level ACLs scoped to service account | `run.events.{tenant_id}` |
| Qdrant collections | One collection per tenant | `memory-{tenant_id}` |
| Agent pods | Kubernetes labels + `NetworkPolicy` | `tenant: {tenant_id}` label selector |

---

## 8. AWS Infrastructure

### 8.1 Infrastructure overview

```mermaid
flowchart TD
    subgraph Region["AWS Region — ap-south-1 (Mumbai)"]

        subgraph VPC["VPC 10.0.0.0/16"]

            subgraph AZ_A["Availability Zone A"]
                PUB_A["Public Subnet\n10.0.1.0/24\nALB · NAT GW"]
                PRIV_A["Private Subnet\n10.0.11.0/24\nEKS Nodes · RDS Primary"]
            end

            subgraph AZ_B["Availability Zone B"]
                PUB_B["Public Subnet\n10.0.2.0/24\nALB (multi-AZ)"]
                PRIV_B["Private Subnet\n10.0.12.0/24\nEKS Nodes · RDS Standby"]
            end

            subgraph AZ_C["Availability Zone C"]
                PUB_C["Public Subnet\n10.0.3.0/24"]
                PRIV_C["Private Subnet\n10.0.13.0/24\nEKS Nodes"]
            end

            subgraph EKS["EKS Cluster — auto-founder-ai"]
                CP_NS["Namespace: control-plane\nNestJS API · Go WebSocket\nLangGraph Orchestrator"]
                AG_NS["Namespace: agents\nStrategist · Architect · Coder\nReviewer · DevOps · Marketer · LLMOps"]
                SB_NS["Namespace: sandbox\nEphemeral Docker workers\ngVisor runtime"]
                MON_NS["Namespace: monitoring\nPrometheus · Grafana\nFluentBit"]
            end

            subgraph Data_Tier["Data Tier (Private Subnets)"]
                RDS["RDS PostgreSQL 16\ndb.r6g.xlarge\nMulti-AZ · Encrypted"]
                EC["ElastiCache Redis\ncache.r6g.large\nCluster mode"]
                MSK["Amazon MSK\n(Managed Kafka)\n3 brokers · Multi-AZ"]
                QD_EC2["Qdrant on EC2\nr6g.large\nPrivate subnet"]
            end
        end

        subgraph Edge2["Edge Services"]
            CF2["CloudFront Distribution\nSSL · WAF · Cache"]
            R53_2["Route53 Hosted Zone\nautofounderdai.euron.one"]
            ACM["ACM Certificate\n*.euron.one · *.autofounderdai.euron.one"]
        end

        subgraph Supporting["Supporting AWS Services"]
            SM["Secrets Manager\nAll API keys + DB passwords"]
            ECR2["ECR Private Registry\nAgent images + Generated app images"]
            S3_BKT["S3 Buckets\nautofounder-artefacts\nautofounder-rlhf\nautofounder-logs"]
            CW["CloudWatch\nLogs · Metrics · Alarms · Dashboards"]
            SFN["Step Functions\nWeekly LLMOps pipeline"]
            IAM["IAM Roles\nPod Identity · IRSA · Least privilege"]
        end
    end

    Internet(["🌐 Internet"]) --> CF2 --> R53_2
    R53_2 --> ALB_SVC["ALB Service\n(EKS LoadBalancer)"]
    ALB_SVC --> CP_NS
    PUB_A & PUB_B --> NAT["NAT Gateway\nOutbound for private subnets"]
    NAT --> Internet
    CP_NS --> AG_NS
    AG_NS --> SB_NS
    AG_NS --> Data_Tier
    AG_NS --> SM
    AG_NS --> ECR2
    AG_NS --> S3_BKT
    AG_NS --> CW
    SFN --> S3_BKT

    style EKS       fill:#f0f4ff,stroke:#4f46e5
    style Data_Tier fill:#f0fdf4,stroke:#16a34a
    style Edge2     fill:#faf5ff,stroke:#7c3aed
    style Supporting fill:#fff7ed,stroke:#ea580c
```

### 8.2 EKS workload layout

| Namespace | Deployments | HPA trigger | Base replicas | Max replicas |
|---|---|---|---|---|
| `control-plane` | NestJS API, Go WebSocket, LangGraph Orchestrator | CPU > 70% | 2 | 10 |
| `agents` | Strategist, Architect, Coder, Reviewer, DevOps, Marketer, LLMOps | Queue depth > 5 builds | 1 each | 20 each |
| `sandbox` | Docker worker pods | Per-build on demand | 0 | 500 (burst) |
| `monitoring` | Prometheus, Grafana, FluentBit | Fixed | 1 each | 1 each |

### 8.3 Networking rules

```mermaid
flowchart LR
    subgraph Ingress["Allowed Inbound"]
        IN1["HTTPS 443\nPublic → ALB"]
        IN2["WSS 443\nPublic → Go WebSocket"]
        IN3["gRPC 50051\nAgent pods → Orchestrator\n(internal only)"]
    end

    subgraph Egress["Allowed Outbound (NAT Gateway)"]
        EG1["Anthropic · OpenAI · Google\nLLM APIs"]
        EG2["GitHub · Stripe · Auth0\nExternal SaaS"]
        EG3["Tavily · SerpAPI · Crunchbase\nResearch APIs"]
        EG4["npm registry · PyPI\nPackage install (sandbox only)"]
        EG5["AWS Services\nS3 · ECR · Secrets Manager\n(via VPC endpoints)"]
    end

    subgraph Blocked["Blocked (sandbox egress policy)"]
        BL1["❌ All other outbound\nfrom sandbox namespace"]
        BL2["❌ Cross-tenant\npod communication"]
    end

    Ingress --> VPC["VPC\nNetworkPolicy enforced"]
    VPC --> Egress
    SB_NS2["Sandbox namespace"] --> BL1 & EG4
```

---

## 9. Security Architecture

### 9.1 Security boundary overview

```mermaid
flowchart TD
    subgraph Trust["Trust Boundary Model"]
        UNTRUSTED["🌐 Untrusted\nPublic Internet\nFounder input · LLM output"]
        SEMI["🟡 Semi-Trusted\nAuthenticated API calls\nJWT-validated tenant sessions"]
        TRUSTED["🟢 Trusted\nInternal services\nEKS pods · RDS · Secrets Manager"]
        HIGHLY_TRUSTED["🔒 Highly Trusted\nAWS IAM roles · HSM · Secrets Manager"]
    end

    subgraph Controls["Security Controls per Boundary"]
        C1["WAF + CloudFront\nSQLi · XSS · OWASP rules"]
        C2["Auth0 JWT validation\nOAuth 2.0 · SAML 2.0 · MFA\nRS256 · 15-min access token"]
        C3["Tenant Guard · Rate Limiter\nTenant isolation · RBAC"]
        C4["Prompt injection detector\n(src/guardrails/)\nAll LLM inputs scanned"]
        C5["PII masking\nAll LLM outputs scrubbed\nbefore storage"]
        C6["Trivy + Semgrep\nEvery Docker image + PR\nHIGH/CRITICAL = block"]
        C7["AES-256 at rest\nTLS 1.3 in transit\nAll data paths"]
        C8["Secrets Manager\nZero hardcoded secrets\nRotation every 30 days"]
        C9["Audit log\n7-year retention\nAll access + action events"]
        C10["Egress network policy\nSandbox: npm/PyPI only\nNo arbitrary outbound"]
    end

    UNTRUSTED --> C1 --> C2 --> SEMI
    SEMI --> C3 & C4 & C5 --> TRUSTED
    TRUSTED --> C6 & C7 & C8 & C9 & C10 --> HIGHLY_TRUSTED

    style UNTRUSTED      fill:#fef2f2,stroke:#dc2626
    style SEMI           fill:#fefce8,stroke:#ca8a04
    style TRUSTED        fill:#f0fdf4,stroke:#16a34a
    style HIGHLY_TRUSTED fill:#f0f4ff,stroke:#4f46e5
```

### 9.2 Auth flow

```mermaid
sequenceDiagram
    autonumber
    actor Founder
    participant FP  as Founder Portal
    participant A0  as Auth0
    participant GW  as NestJS API Gateway
    participant SM  as Secrets Manager
    participant PG2 as PostgreSQL

    Founder ->> FP: Click "Login"
    FP ->> A0: Redirect (OAuth 2.0 PKCE flow)
    A0 -->> Founder: MFA challenge (TOTP)
    Founder ->> A0: TOTP code
    A0 -->> FP: Authorization code
    FP ->> A0: Exchange code → access_token (RS256 JWT, 15 min) + refresh_token
    A0 -->> FP: { access_token, refresh_token, id_token }

    FP ->> GW: API call + Authorization: Bearer {access_token}
    GW ->> A0: Verify JWT signature (JWKS endpoint)
    A0 -->> GW: { sub, tenant_id, roles, email }
    GW ->> PG2: SELECT tenant WHERE id = tenant_id AND status = 'active'
    PG2 -->> GW: tenant record
    GW -->> GW: Attach { tenant_id, roles } to request context
    GW -->> FP: 200 OK — proceed

    Note over FP,GW: On 401: FP uses refresh_token to get new access_token silently
    Note over GW: RBAC check: roles include required permission for route
```

### 9.3 Compliance controls

| Requirement | Control |
|---|---|
| **GDPR Right to Erasure** | `/api/v1/tenants/{id}/erase` — wipes PostgreSQL schema, S3 prefix, Redis keys, Qdrant collection |
| **CCPA data export** | `/api/v1/tenants/{id}/export` — full S3 dump + DB export in 72 hrs |
| **SOC 2 Type II** | Quarterly pen tests + automated Trivy/Semgrep on every deploy |
| **ISO 27001** | Secrets rotation, audit logs 7yr, MFA enforcement, change management via PRs |
| **PII masking** | All generated code and LLM outputs pass through `src/guardrails/pii_mask.py` before storage |
| **Prompt injection** | All user-supplied text routed through `src/guardrails/injection_detect.py` before LLM call |
| **Content moderation** | Harmful/illegal output filter on all agent outputs (LLM-as-classifier) |

---

## 10. Memory & State Architecture

```mermaid
flowchart LR
    subgraph ShortTerm["⚡ Short-Term Memory (Redis)"]
        RS1["Active run state\nstored per run_id"]
        RS2["HITL approval signals\napproval:{run_id}"]
        RS3["Agent log streaming\npub/sub channel per run"]
        RS4["Rate limit counters\nper tenant_id"]
        RS5["Session tokens\nJWT refresh state"]
    end

    subgraph GraphState["📋 Graph State (PostgreSQL)"]
        PG_CK["LangGraph Checkpoints\nFull Pydantic state\nper node transition"]
        PG_RUN["Run history\nAll state snapshots\n(replay + audit)"]
    end

    subgraph LongTerm["🧠 Long-Term Memory (Qdrant)"]
        QD1["Successful agent patterns\n(vectorised StrategistOutput etc.)"]
        QD2["User preference embeddings\n(accept/reject/edit history)"]
        QD3["Domain-specific code templates\n(retrieved by Coder Agent)"]
    end

    subgraph RLHF["📈 RLHF Dataset (S3)"]
        S3_R1["Weekly batch:\naccepted / rejected / edited\nfounder interactions"]
        S3_R2["DSPy optimisation input\nprompt variants + scores"]
        S3_R3["Model routing labels\n(task → model decisions + COGS)"]
    end

    subgraph AgentAccess["Agent Memory Access Pattern"]
        A["Any Agent Node"]
        A -->|"read/write active state"| RS1
        A -->|"poll approval"| RS2
        A -->|"checkpoint state"| PG_CK
        A -->|"retrieve similar\npast patterns"| QD1 & QD2 & QD3
    end

    OPS["LLMOps Agent\n(weekly pipeline)"] -->|"consume interactions"| S3_R1
    OPS -->|"optimise prompts"| S3_R2
    OPS -->|"update routing rules"| S3_R3
    OPS -->|"update embeddings"| QD1 & QD2

    style ShortTerm  fill:#fef2f2,stroke:#dc2626
    style GraphState fill:#f0f4ff,stroke:#4f46e5
    style LongTerm   fill:#f0fdf4,stroke:#16a34a
    style RLHF       fill:#fff7ed,stroke:#ea580c
```

---

## 11. Observability & LLMOps

### 11.1 Observability stack

```mermaid
flowchart TD
    subgraph Sources["Data Sources"]
        AGT["Agent Nodes\n(every LLM call + tool call)"]
        API_SRC["NestJS API\n(request/response)"]
        EKS_SRC["EKS\n(pod CPU · memory · restarts)"]
        RDS_SRC["RDS · Redis · Kafka\n(query latency · queue depth)"]
        SANDBOX_SRC["Sandbox containers\n(lint errors · test results · CVEs)"]
    end

    subgraph Collection["Collection Layer"]
        LS["LangSmith\nLLM trace capture\nper-node + per-model"]
        FB["FluentBit\nLog aggregation → CloudWatch"]
        PROM["Prometheus\nMetrics scraping"]
        PH["PostHog\nProduct analytics\n(founder interactions)"]
    end

    subgraph Storage2["Storage"]
        CW_L["CloudWatch Logs\n90-day retention"]
        CW_M["CloudWatch Metrics\nCustom namespace: AutoFounderAI/*"]
        S3_LOGS["S3 Logs bucket\nLong-term archive 7yr"]
    end

    subgraph Dashboards["Dashboards & Alerting"]
        GRF["Grafana\nAgent pipeline health\nCOGS per MVP\nToken usage per model\nLLM error rates"]
        CW_DASH["CloudWatch Dashboards\nInfra health · EKS · RDS"]
        SENTRY["Sentry\nException tracking"]
        SLACK_ALERTS["Slack Alerts\n#ops-alerts channel\nFatal errors · SLA breaches · COGS overrun"]
    end

    Sources --> Collection
    LS --> CW_L & S3_LOGS
    FB --> CW_L
    PROM --> CW_M & GRF
    PH --> GRF

    CW_L & CW_M --> CW_DASH & SLACK_ALERTS
    CW_M --> GRF
    AGT --> SENTRY

    style Sources     fill:#f8fafc,stroke:#64748b
    style Collection  fill:#f0f4ff,stroke:#4f46e5
    style Dashboards  fill:#f0fdf4,stroke:#16a34a
```

### 11.2 Key metrics tracked

| Metric | Owner | Alert threshold |
|---|---|---|
| End-to-end MVP generation latency | LangGraph | > 20 min → PagerDuty |
| COGS per MVP build (₹) | LLMOps | > ₹500 → Slack warning |
| First-run deployment success rate | DevOps | < 85% → Slack alert |
| Self-healing auto-fix rate | Reviewer | < 90% over 24h → investigation |
| LLM error rate (5xx) | All agents | > 1% → PagerDuty |
| API P99 latency | NestJS | > 100ms → Slack warning |
| Sandbox spin-up time | Coder/Reviewer | > 10s → Slack warning |
| Token cost per model per agent | LLMOps | Tracked weekly — no hard alert |
| Qdrant retrieval latency | Memory layer | > 200ms → investigation |

### 11.3 LLMOps weekly pipeline

```mermaid
flowchart LR
    SFN_TRIGGER["AWS Step Functions\nCron: Every Sunday 02:00 IST"]

    SFN_TRIGGER --> COLLECT["1. Collect\nPull RLHF interactions\nfrom S3 (past 7 days)"]
    COLLECT --> PREP["2. Prep dataset\nFilter accept/reject/edit signals\nDeduplicate · Quality filter"]
    PREP --> OPT["3. DSPy prompt optimisation\nGenerate candidate prompt variants\nfor each agent node"]
    OPT --> AB["4. A/B eval\nPromptfoo: score variants\nvs baseline on golden set"]
    AB --> PROMOTE["5. Promote winner\nUpdate prompt registry in DB\nDeploy to production agents"]
    PROMOTE --> ROUTING["6. Update model routing\nRecalibrate GPT-4o-mini\nvs Claude thresholds based\non COGS + quality data"]
    ROUTING --> REPORT["7. Weekly report\nSlack: COGS · quality trends\nModel distribution · top errors"]

    style SFN_TRIGGER fill:#fff7ed,stroke:#ea580c
    style PROMOTE     fill:#f0fdf4,stroke:#16a34a
```

---

## 12. CI/CD Pipeline

```mermaid
flowchart LR
    subgraph Dev["Developer Workflow"]
        PR["Pull Request\n(feat/pillar/description)"]
    end

    subgraph CI["GitHub Actions — CI  (every PR)"]
        LINT_CI["Lint + Type-check\nESLint · Prettier\nBlack · Ruff · mypy"]
        TEST_CI["Unit tests\nJest · pytest\nCoverage gate: 80%"]
        SEC_CI["Security scan\nTrivy (Docker images)\nSemgrep (SAST, auto ruleset)\nBandit (Python)"]
        EVAL_CI["LLM evals\nLangSmith + Promptfoo\nAgent golden set"]
        BUILD_CI["Docker build\nmulti-stage · every app"]
    end

    subgraph Gate["Required Status Checks"]
        MERGE["Merge to main\n(all checks green)"]
    end

    subgraph CD["GitHub Actions — CD  (push to main)"]
        PUSH_ECR["Push to ECR\nTagged: git-{SHA}"]
        UPDATE_HELM["Update Helm values.yaml\nimage.tag = git-{SHA}"]
        COMMIT_HELM["Commit values.yaml\nto infra/helm/ (GitOps)"]
    end

    subgraph ArgoCD["ArgoCD — GitOps Deploy"]
        SYNC["Auto-sync detects\nvalues.yaml change"]
        ROLLING["Rolling deploy\nto EKS (zero downtime)"]
        HEALTH["Health check\nReadiness probes pass?"]
        ROLLBACK["Auto-rollback\nif health check fails"]
    end

    subgraph Notify["Notifications"]
        SLACK_CD["Slack #deployments\nDeploy success / rollback"]
    end

    PR --> LINT_CI & TEST_CI & SEC_CI & EVAL_CI & BUILD_CI
    LINT_CI & TEST_CI & SEC_CI & EVAL_CI & BUILD_CI --> Gate
    Gate --> MERGE --> PUSH_ECR --> UPDATE_HELM --> COMMIT_HELM
    COMMIT_HELM --> SYNC --> ROLLING --> HEALTH
    HEALTH -->|"healthy"| SLACK_CD
    HEALTH -->|"unhealthy"| ROLLBACK --> SLACK_CD

    style Gate    fill:#f0fdf4,stroke:#16a34a
    style ROLLBACK fill:#fef2f2,stroke:#dc2626
```

---

## 13. Performance Targets

| Metric | Target | Hard Cap | Measurement |
|---|---|---|---|
| API response time (P99) | < 100 ms | < 500 ms | Prometheus + CloudWatch |
| Sandbox spin-up time | < 10 s | < 30 s | Agent node trace |
| Strategist Agent end-to-end | < 30 min | 45 min | LangGraph run_id trace |
| Architect Agent end-to-end | < 45 min | 60 min (excl. HITL) | LangGraph run_id trace |
| Coder Agent end-to-end | < 15 min | 20 min | LangGraph run_id trace |
| Reviewer Agent end-to-end | < 20 min | 30 min | LangGraph run_id trace |
| DevOps Agent end-to-end | < 10 min | 15 min | Terraform apply duration |
| **Full pipeline (idea → live MVP)** | **≈ 7 days** | — | Wall-clock (incl. HITL waits) |
| COGS per MVP build | < ₹500 | — | LLMOps cost telemetry |
| Self-healing auto-fix rate | ≥ 90% | — | Reviewer retry outcome logs |
| First-run deploy success | ≥ 85% | — | DevOps outcome metric |
| Concurrent builds (horizontal scale) | 500 | — | Load test (Product Hunt spike) |
| System availability | 99.9% | — | CloudWatch alarms |

---

## 14. Phased Rollout

```mermaid
gantt
    title Auto-Founder AI — Rollout Roadmap (2026)
    dateFormat  YYYY-MM
    axisFormat  %b %Y

    section Phase 1 · Validation Engine
    Strategist Agent          :active, p1a, 2026-05, 2026-06
    Architect Agent           :active, p1b, 2026-05, 2026-06
    Founder Portal v1         :active, p1c, 2026-05, 2026-06
    10 pilot clients          :milestone, 2026-06, 0d

    section Phase 2 · MVP Builder
    Coder Agent               :p2a, 2026-07, 2026-08
    Reviewer Agent            :p2b, 2026-07, 2026-08
    Sandbox infrastructure    :p2c, 2026-07, 2026-08
    50 clients                :milestone, 2026-09, 0d

    section Phase 3 · Launch & GTM
    DevOps Agent              :p3a, 2026-09, 2026-10
    Marketer Agent            :p3b, 2026-09, 2026-10
    Launch Control Center     :p3c, 2026-09, 2026-10
    150 clients               :milestone, 2026-11, 0d

    section Phase 4 · Enterprise Scale
    LLMOps Agent              :p4a, 2026-11, 2027-01
    Advanced CT pipelines     :p4b, 2026-11, 2027-01
    Enterprise VPC isolation  :p4c, 2026-11, 2027-01
    300 clients               :milestone, 2027-02, 0d

    section Phase 5 · Global Expansion
    Multi-region (us-east-1)  :p5a, 2027-02, 2027-05
    Localisation (EN/HI/ES)   :p5b, 2027-02, 2027-05
    Marketplace               :p5c, 2027-03, 2027-06
    1000 clients              :milestone, 2027-06, 0d
```

### Phase scope summary

| Phase | Status | Agents active | Key capabilities |
|---|---|---|---|
| **Phase 1** | **Active** | Strategist, Architect | Market analysis, Lean Canvas, tech architecture, Founder Portal |
| **Phase 2** | Upcoming | + Coder, Reviewer | Full-stack code gen, self-healing loop, GitHub PR |
| **Phase 3** | Planned | + DevOps, Marketer | One-click deploy, SEO + social launch, Launch Control Centre |
| **Phase 4** | Planned | + LLMOps | RLHF pipeline, prompt A/B testing, enterprise VPC, white-labeling |
| **Phase 5** | Planned | All 7 | Multi-region, localisation, marketplace, mobile gen (Phase 6 TBD) |

---

## 15. Open Design Questions

These are unresolved architectural decisions. Do not implement solutions without explicit product approval.

| # | Question | Impact | Owner |
|---|---|---|---|
| 1 | How to automate AWS account **Transfer of Ownership** when a founder ejects from the SaaS? | DevOps Agent · Billing | Product |
| 2 | **Multi-cloud support** (GCP / Azure) for AI Researcher persona benchmarking? | DevOps Agent · Infra | Engineering |
| 3 | Rate limit strategy for **X / LinkedIn APIs** at 1,000+ tenant scale without Buffer becoming a bottleneck? | Marketer Agent | Engineering |
| 4 | **Sustainable differentiation**: preventing commoditisation of core features within 12-month horizon? | Strategy | Product |
| 5 | **Phase 6 scope**: native mobile app generation — Flutter vs React Native, model selection, timeline? | Coder Agent · Roadmap | Product |
| 6 | Governance model for **on-prem LLM** deployment (Enterprise tier) — Llama 3? Mistral? Self-hosted Bedrock? | LLMOps · Infra | Engineering |

---

*Auto-Founder AI — High-Level Design v1.0 | May 2026*
*For questions: product@euron.one*
