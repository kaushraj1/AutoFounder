# AutoFounder AI — High-Level Design (HLD)

**Org**: Euron AutoFounder AI · **Contact**: product@euron.one  
**Version**: 1.0 · **Date**: 2026-05-19

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [System Context](#2-system-context)
3. [10-Layer Reference Architecture](#3-10-layer-reference-architecture)
4. [End-to-End Workflow](#4-end-to-end-workflow)
5. [Agent Architecture & Data Flow](#5-agent-architecture--data-flow)
6. [Multi-Agent Communication](#6-multi-agent-communication)
7. [Memory Architecture](#7-memory-architecture)
8. [Data Architecture](#8-data-architecture)
9. [API Layer](#9-api-layer)
10. [Guardrails Pipeline](#10-guardrails-pipeline)
11. [Multi-Tenant AWS Infrastructure](#11-multi-tenant-aws-infrastructure)
12. [Observability Stack](#12-observability-stack)
13. [CI/CD Pipeline](#13-cicd-pipeline)
14. [Security Architecture](#14-security-architecture)
15. [Performance & Scalability](#15-performance--scalability)
16. [Key Design Decisions](#16-key-design-decisions)

---

## 1. Purpose & Scope

AutoFounder AI converts a single text idea into a **fully validated, designed, built, tested, deployed, marketed, and continuously-improved software business — autonomously**.

| Metric | Traditional Path | AutoFounder AI |
|---|---|---|
| Idea → Validated | 3 weeks | 30 minutes |
| Validated → MVP Built | 3–6 months | 7 days |
| MVP → Deployed | 1 week | 10 minutes |
| Deployed → Marketed | 2–3 weeks | 2 hours |
| **Total Cost** | **$20K–$60K** | **$200–$700** |

**Four pillars of differentiation**: Multi-Agent Collaboration · Persistent Memory · Secure & Scalable · Multi-Tenant SaaS

---

## 2. System Context

```mermaid
C4Context
  title AutoFounder AI — System Context

  Person(founder, "Founder / User", "Submits idea, approves gates, monitors build")
  Person(admin, "Super Admin", "Platform ops, tenant management")

  System(autofounder, "AutoFounder AI", "Multi-tenant agentic AI SaaS that autonomously builds startups from a text idea")

  System_Ext(llm, "LLM Providers", "Google AI (Gemini 3.5 Flash + gemini-embedding-2)")
  System_Ext(research, "Research APIs", "Tavily, SerpAPI, Crunchbase, G2, SimilarWeb, Google Trends")
  System_Ext(devtools, "Dev & Deploy Tools", "GitHub, Stripe, Supabase, Vercel, AWS")
  System_Ext(marketing, "Marketing Platforms", "ProductHunt, X, LinkedIn, Reddit, Mailchimp, Resend")
  System_Ext(monitoring, "Observability Tools", "LangSmith, Prometheus/Grafana, Sentry")

  Rel(founder, autofounder, "Submits idea, approves HITL gates", "HTTPS / WebSocket")
  Rel(admin, autofounder, "Manages tenants, monitors platform", "HTTPS")
  Rel(autofounder, llm, "LLM calls for reasoning, code gen, embeddings", "HTTPS / gRPC")
  Rel(autofounder, research, "Market & competitor research", "HTTPS")
  Rel(autofounder, devtools, "Repo creation, deployment, auth integration", "HTTPS / gRPC")
  Rel(autofounder, marketing, "Content publishing (after founder approval)", "HTTPS")
  Rel(autofounder, monitoring, "Traces, metrics, logs, LLM evals", "OTel / HTTPS")
```

---

## 3. 10-Layer Reference Architecture

```mermaid
block-beta
  columns 1

  block:input["1. INPUT LAYER"]:1
    I1["Text / PDFs / Images / Voice / Video"]
    I2["APIs / Webhooks / IoT Streams"]
    I3["User Feedback / Market Data"]
  end

  block:orch["2. AGENT ORCHESTRATION LAYER (LangGraph)"]:1
    O1["Dynamic Task Allocation"]
    O2["Inter-Agent Event Bus (Confluent Kafka · EventBridge)"]
    O3["Workflow & Plan Management (DAGs)"]
    O4["HITL Gates · Monitoring"]
  end

  block:agents["3. AI AGENTS LAYER"]:1
    A1["Strategy & Ideation"]
    A2["Product Planner"]
    A3["Research"]
    A4["Engineering (Architect · Coder · Reviewer · DevOps)"]
    A5["Marketing"]
    A6["Finance"]
    A7["Ops & Risk · LLMOps"]
  end

  block:models["4. MODEL & CAPABILITY LAYER"]:1
    M1["LLMs (Gemini 3.5 Flash)"]
    M2["Embeddings · Vision · Speech (Whisper)"]
    M3["RAG & Retrieval · RLHF / Alignment"]
  end

  block:data["5. DATA & KNOWLEDGE LAYER"]:1
    D1["PostgreSQL 16 (Relational)"]
    D2["Supabase pgvector (Vector)"]
    D3["Neo4j / Neptune (Graph)"]
    D4["Redis / DynamoDB (Cache)"]
    D5["S3 Raw Data Lake"]
  end

  block:output["6. OUTPUT & EXPERIENCE LAYER"]:1
    X1["Reports · Plans · Code · Dashboards"]
    X2["Real-time Notifications · Knowledge Updates"]
  end

  block:services["7. SERVICE & INTEGRATION LAYER"]:1
    S1["REST / GraphQL / gRPC API Gateway"]
    S2["3rd-party CRM / ERP / Dev Tools / Payments"]
    S3["Automation (Zapier / n8n / Step Functions)"]
  end

  block:guardrails["8. GUARDRAILS & GOVERNANCE LAYER"]:1
    G1["Input · Instruction · Execution · Output Guardrails"]
    G2["Policy & Rules (OPA) · Audit & Lineage"]
  end

  block:compliance["9. COMPLIANCE & SECURITY LAYER"]:1
    C1["GDPR · CCPA · SOC 2 · ISO 27001 · HIPAA-ready"]
    C2["Encryption · PII Masking · Model Versioning"]
  end

  block:observability["10. OBSERVABILITY & MLOPS FOUNDATION"]:1
    OB1["Prometheus / Grafana · OpenTelemetry · LangSmith"]
    OB2["Feature Store (Feast) · Cost FinOps · CI/CD"]
  end
```

---

## 4. End-to-End Workflow

```mermaid
flowchart TD
    A([User submits text idea]) --> B

    subgraph P1["Pillar 1 — Strategy & Ideation"]
        B[Strategy Agent\nMarket sizing · Competitor discovery\nPersona gen · Lean Canvas · Viability score]
    end

    B --> B1{Founder Approves\nor Pivots?}
    B1 -- Pivot --> B
    B1 -- Approve --> C

    subgraph P2["Pillar 2 — Architecture & Tech Stack"]
        C[Engineering Agent — Architect\nFRs/NFRs · ERD · OpenAPI · Stack selection\nAuth strategy · Cost forecast]
    end

    C --> C1{Architecture\nApproval Gate}
    C1 -- Reject --> C
    C1 -- Approve --> D

    subgraph P3["Pillar 3 — Autonomous Code Generation"]
        D[Engineering Agent — Coder\nRepo scaffolding · Frontend ∥ Backend\nDB migrations · Auth · Stripe · CI/CD]
    end

    D --> E

    subgraph P4["Pillar 4 — Testing & Self-Healing"]
        E[Engineering Agent — Reviewer\nStatic analysis · Unit + Integration tests\nSecurity scans · Self-correction loop ≤5 retries]
    end

    E --> E1{All tests green?}
    E1 -- No, retries exhausted --> EH([Escalate to Human])
    E1 -- Yes --> F

    subgraph P5["Pillar 5 — Deploy & Infrastructure"]
        F[Engineering Agent — DevOps\nContainerize · Terraform/ECS · DNS/SSL\nSecrets · Monitoring setup]
    end

    F --> G

    subgraph P6["Pillar 6 — Marketing & Launch"]
        G[Marketing Agent\nBrand · Landing page · SEO content\nEmail drip · ProductHunt kit · Social posts]
    end

    G --> G1{Launch Control Center\nFounder Approves}
    G1 -- Edit --> G
    G1 -- Approve --> H([Public Launch])

    H --> I

    subgraph P7["Pillar 7 — LLMOps & Continuous Learning"]
        I[LLMOps Agent\nTelemetry · RLHF · A/B experiments\nPrompt opt · Model routing · Cost tracking]
    end

    I -. weekly feedback .-> B
    I -. prompt updates .-> D
    I -. content tuning .-> G

    style EH fill:#f66,color:#fff
    style H fill:#2a2,color:#fff
```

---

## 5. Agent Architecture & Data Flow

### 5.1 Agent Contract

Every agent exposes a standard interface:

```
┌─────────────────────────────────────────────────┐
│                    Agent<TInput, TOutput>        │
│  understand(input) → Intent                      │
│  plan(intent)      → DAG of Steps               │
│  execute(plan)     → AsyncIterable<StepEvent>   │
│  verify(output)    → VerifyResult                │
│  learn(trace)      → void   ──▶ LLMOps          │
└─────────────────────────────────────────────────┘
```

### 5.2 Pillar-to-Agent Mapping

```mermaid
graph LR
    subgraph Pillar1["Pillar 1 — Strategy & Ideation"]
        STR[Strategy & Ideation Agent]
        RES[Research Agent]
        PP[Product Planner Agent]
        STR --> |"TAM/SAM, personas\nLean Canvas"| PP
        RES --> |"competitor data\nmarket signals"| STR
    end

    subgraph Pillar2_3["Pillars 2–3 — Architect & Build"]
        ARC[Architect Sub-Agent]
        COD[Coder Sub-Agent]
        ARC --> |"OpenAPI + ERD\nstack spec"| COD
    end

    subgraph Pillar4["Pillar 4 — Review & Heal"]
        REV[Reviewer Sub-Agent]
        SH[Self-Healer Sub-Agent]
        QG[Quality Gate Sub-Agent]
        REV --> |"lint/test failures"| SH
        SH --> |"patched code"| REV
        REV --> QG
    end

    subgraph Pillar5["Pillar 5 — Deploy"]
        DVO[DevOps Sub-Agent]
        INF[Infra Provisioner]
        DNS[DNS & SSL Agent]
        DVO --> INF --> DNS
    end

    subgraph Pillar6["Pillar 6 — Marketing"]
        MKT[Marketing Agent]
        SEO[SEO Writer]
        VIS[Visual Designer]
        SOC[Social Scheduler]
        MKT --> SEO & VIS & SOC
    end

    subgraph Pillar7["Pillar 7 — LLMOps"]
        LMO[LLMOps Agent]
        PR[Prompt Optimizer]
        MR[Model Router]
        DM[Drift Monitor]
        LMO --> PR & MR & DM
    end

    PP --> |"PRD + requirements"| ARC
    COD --> |"artifacts"| REV
    QG --> |"approved repo"| DVO
    DNS --> |"live_url + brand"| MKT
    LMO --> |"model/prompt updates"| STR & COD & MKT
```

### 5.3 Inter-Pillar Data Flow

```mermaid
sequenceDiagram
    participant U as Founder
    participant FE as Founder Portal
    participant GW as FastAPI API GW
    participant ORCH as LangGraph Orchestrator
    participant STR as Strategy Agent
    participant ENG as Engineering Agent
    participant MKT as Marketing Agent
    participant LMO as LLMOps Agent
    participant UDAL as Unified Data Access Layer
    participant DB as Data Stores
    participant BUS as EventBridge
    participant OBS as Observability

    U->>FE: Submit idea text
    FE->>GW: POST /v1/ideas (JWT + tenant_id)
    GW->>ORCH: createRun(idea, tenant)
    ORCH->>OBS: emit run.started

    Note over ORCH,STR: Pillar 1
    ORCH->>STR: dispatch validate(idea)
    STR->>UDAL: read market_intelligence vectors
    UDAL->>DB: query (tenant-scoped namespace)
    DB-->>STR: competitor + market context
    STR->>OBS: LangSmith trace (prompts + outputs)
    STR-->>ORCH: {canvas, viability_score, personas}
    ORCH->>BUS: emit pillar.completed{1}
    ORCH-->>U: HITL gate — Approve / Pivot

    Note over ORCH,ENG: Pillars 2–5
    U->>ORCH: approve
    ORCH->>ENG: dispatch design + build + test + deploy
    ENG->>UDAL: write code_patterns, architecture_decisions
    ENG-->>ORCH: {live_url, repo_url}
    ORCH->>BUS: emit pillar.completed{2,3,4,5}

    Note over ORCH,MKT: Pillar 6
    ORCH->>MKT: dispatch launch(brand, live_url)
    MKT-->>ORCH: {landing_page, social_assets}
    ORCH-->>U: Launch Control Center gate
    U->>ORCH: approve launch
    ORCH->>BUS: emit pillar.completed{6}

    Note over BUS,LMO: Pillar 7 (continuous)
    BUS-->>LMO: all run.* events
    LMO->>UDAL: read traces + feedback
    LMO-->>ORCH: updated prompt versions + model routing rules

    ORCH-->>FE: WebSocket stream (live tokens + step events)
    FE-->>U: real-time progress
```

---

## 6. Multi-Agent Communication

```mermaid
flowchart LR
    subgraph Sync["Synchronous (gRPC)"]
        direction TB
        A1[Agent A] -->|"Proto request"| A2[Agent B]
        A2 -->|"Proto response"| A1
    end

    subgraph Async["Asynchronous (EventBridge + SQS/SNS)"]
        direction TB
        ORCH2[Orchestrator] -->|"run.started\npillar.completed\ngate.required\nhuman.approved"| EB[EventBridge]
        EB --> SQS[SQS Queues\nper-pillar]
        EB --> SNS[SNS Fan-out\nnotifications]
        SQS --> Workers["Agent Workers\nECS Fargate"]
    end

    subgraph Stream["Streaming (WebSocket)"]
        direction TB
        ORCH3[Orchestrator] -->|"pg_notify\nchange events"| WS[Supabase Realtime\nManaged WebSocket]
        WS -->|"WebSocket"| Portal[Founder Portal]
    end

    subgraph LongRun["Long-running (Step Functions)"]
        direction TB
        LMO2[LLMOps Agent] -->|"weekly eval cycle\nprompt opt pipeline"| SF[AWS Step Functions]
    end
```

**Communication patterns by use case**:

| Pattern | Protocol | When |
|---|---|---|
| Agent → Agent (low latency) | gRPC (Protocol Buffers) | Synchronous request/response |
| Orchestrator → Agents | EventBridge → SQS | Async task dispatch |
| Run events (fan-out) | EventBridge → SNS | Notifications, webhooks |
| Live token/log stream | Supabase Realtime (WebSocket) | Founder Portal real-time updates |
| LLMOps weekly cycle | AWS Step Functions | Long-running multi-day pipelines |
| High-throughput telemetry | Confluent Kafka | LLMOps trace ingestion |

---

## 7. Memory Architecture

```mermaid
graph TB
    subgraph MemoryTiers["Memory Tiers (per tenant)"]
        direction TB

        WM["Working Memory\nIn-process buffer\nTTL: current step"]
        ST["Short-term / Session\nRedis Cluster\nTTL: 24h sliding"]
        EP["Episodic\nPostgreSQL memory.episodes\nTTL: 90 days"]
        SEM["Semantic / Long-term\nSupabase pgvector\nTTL: unbounded"]
        PROC["Procedural\nPrompt + Tool Registry (Postgres)\nTTL: versioned"]
        REL["Relational Knowledge\nNeo4j / Amazon Neptune\nTTL: unbounded"]
        COLD["Cold Archive\nS3 Object Lock\nTTL: 7 years (audit)"]
    end

    WM -->|"flush on step complete"| ST
    ST -->|"promote patterns"| EP
    EP -->|"embed + index"| SEM
    SEM -->|"skill extraction"| PROC
    EP & SEM -->|"graph entities"| REL
    EP & SEM & REL -->|"compress + archive"| COLD

    PROC -->|"skills / playbooks"| Agents[All Agents]
    SEM -->|"RAG context"| Agents
    ST -->|"hot state"| Agents
    REL -->|"entity graph lookups"| Agents
```

**Tenant isolation**: all keys prefixed `tenant_id/`; Postgres schema-per-tenant; vector store namespace-per-tenant.

---

## 8. Data Architecture

### 8.1 Polyglot Persistence

```mermaid
graph LR
    UDAL["Unified Data Access Layer\n(packages/db)\nEnforces tenant_id · Routes calls\nEmits lineage events"]

    UDAL -->|"udal.relational()"| PG["PostgreSQL 16\nRDS Multi-AZ\nSchema-per-tenant + RLS\nruns · artifacts · gates\nmemory.episodes · prompt_registry"]
    UDAL -->|"udal.vector()"| VEC["Supabase pgvector\nPGVECTOR extension\nvector(768) HNSW index\nSchema-per-tenant\n7 collections"]
    UDAL -->|"udal.graph()"| GRAPH["Neo4j / Amazon Neptune\nCompetitor ↔ Market\n↔ Persona entity graph"]
    UDAL -->|"cache"| REDIS["Redis (ElastiCache)\nSession state\nPlan checkpoints\nEmbedding cache"]
    UDAL -->|"udal.object()"| S3["Supabase Storage\nArtifacts · Assets\nRLHF datasets\nbucket/{tenant_id}/..."]
```

### 8.2 RAG Pipeline

```mermaid
flowchart LR
    Q[User Query] --> QR[Query Rewriting\n LLM]
    QR --> HR[Hybrid Retrieval\nBM25 + ANN Dense]
    HR --> RERANK[Cross-encoder\nReranking\nCohere / BGE]
    RERANK --> CC[Context\nCompression]
    CC --> LLM[LLM Answer\nGeneration]
    LLM --> CIT[Citation Check\nOutput Guardrail]
    CIT --> RESP[Response\n+ source doc IDs]

    HR -->|"logs doc IDs + scores"| LS[LangSmith\nGroundedness Audit]
```

### 8.3 Core PostgreSQL Schemas

```
tenant_<uuid>.runs           — pillar, status, plan DAG (JSONB), created_at
tenant_<uuid>.artifacts      — run_id, kind, uri, metadata (JSONB)
tenant_<uuid>.gates          — run_id, kind, state, decided_by, decided_at
orchestrator.checkpoints     — LangGraph DAG checkpoints
orchestrator.runs            — serialized plan DAGs
memory.episodes              — per-run traces, decisions, gate outcomes
prompt_registry              — prompt versions (immutable, semver-tagged)
tool_registry                — MCP tool specs, auth scope, cost class
```

---

## 9. API Layer

### 9.1 Protocol Overview

```mermaid
graph TB
    FE[Founder Portal\nNext.js 14] -->|"REST + GraphQL\nHTTPS"| GW
    MOBILE[Mobile / Webhooks] -->|"REST HTTPS"| GW
    ADMIN[Admin Dashboard] -->|"REST HTTPS"| GW

    GW["FastAPI API Gateway\napps/api :8000\nAuth · Tenancy · Rate-limits\nJWT validation"]

    GW -->|"gRPC"| ORCH[LangGraph Orchestrator\napps/orchestrator]
    GW -->|"gRPC"| AI[FastAPI Agent Workers\napps/ai-services]
    GW -->|"WebSocket /v1/runs/{id}/stream"| RT[Supabase Realtime\nManaged WebSocket]

    ORCH -->|"gRPC"| AI
    RT -->|"WebSocket"| FE
```

### 9.2 Key REST Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/ideas` | Submit idea → returns `run_id` |
| `GET` | `/v1/runs/{id}` | Run state, active gates, artifacts |
| `POST` | `/v1/runs/{id}/gates/{gate_id}` | Approve / reject HITL gate |
| `GET` | `/v1/runs/{id}/artifacts` | List artifacts (canvas, repo, live URL…) |
| `GET` | `/v1/runs/{id}/stream` | WebSocket — live token + step events |
| `POST` | `/v1/tenants/{id}/keys` | Rotate tenant API keys |
| `GET` | `/v1/llmops/cost?tenant_id=…` | Per-tenant cost telemetry |
| `POST` | `/v1/feedback` | Accept/reject signal for RLHF |

All new endpoints require an OpenAPI 3.1 entry in `apps/api/openapi.yaml`. Breaking changes use `/v2/` namespacing.

---

## 10. Guardrails Pipeline

Every agent invocation passes through a 6-stage pipeline:

```mermaid
flowchart LR
    IN[User Input\nor Agent Call] --> G1

    subgraph Pipeline["6-Stage Guardrails Pipeline"]
        G1["Stage 1\nPolicy & Rules\nOPA / Cedar\nPermissions · Access Control"]
        G2["Stage 2\nInput Guardrails\nLlama Guard · Presidio\nPII redaction · Injection detection"]
        G3["Stage 3\nInstruction Guardrails\nSystem prompt constraints\nStatic validators"]
        G4["Stage 4\nExecution Guardrails\nTool schema validation\nCost caps · Rate limits\nAllow-list enforcement"]
        G5["Stage 5\nOutput Guardrails\nHallucination check\nToxicity · Citation check\nTruLens / Llama Guard"]
        G6["Stage 6\nMonitoring Guardrails\nAnomaly & drift detection\nAbuse detection\nEvidently AI · PostHog"]
    end

    G1 --> G2 --> G3 --> G4 --> G5 --> G6 --> OUT[Verified Output\nor Rejection]

    G1 & G2 & G3 & G4 & G5 & G6 -->|"immutable AUDIT log"| S3L["S3 Object Lock\n7-year retention"]

    G5 -->|"Marketing Agent: feature-claim\ncross-ref vs Architect's feature list"| MKT_NOTE[["Required check\nfor all marketing copy"]]
```

---

## 11. Multi-Tenant AWS Infrastructure

### 11.1 Network Topology

```mermaid
graph TB
    INET([Internet]) --> CF[CloudFront CDN\n+ WAF + Shield]
    CF --> ALB[Application Load Balancer\nL7 · HTTPS termination]

    subgraph VPC["AWS VPC — Multi-AZ"]
        subgraph PUBLIC["Public Subnets (AZ-a, AZ-b)"]
            ALB
            NAT[NAT Gateways]
        end

        subgraph PRIVATE_APP["Private App Subnets (AZ-a, AZ-b)"]
            ECS_WEB["ECS Fargate\napps/web :3000\nFounder Portal"]
            ECS_API["ECS Fargate\napps/api :8000\nFastAPI API GW"]
            ECS_AI["ECS Fargate\napps/ai-services :8000\nFastAPI Agent Workers"]
            ECS_ORCH["ECS Fargate\napps/orchestrator\nLangGraph Engine"]
            ECS_RT["Supabase Realtime\nManaged WebSocket\npg_notify broadcast"]
        end

        subgraph PRIVATE_DATA["Private Data Subnets (AZ-a, AZ-b)"]
            RDS["RDS PostgreSQL 16\nMulti-AZ Primary + Replica"]
            REDIS["ElastiCache Redis\nMulti-AZ Cluster"]
        end

        subgraph SANDBOX["Ephemeral Sandbox Subnet"]
            SBENV["ECS Fargate Sandbox Tasks\nFirecracker / gVisor isolation\nStrict egress allow-list\nEphemeral — minutes TTL"]
        end
    end

    subgraph EXTERNAL["External / Managed Services"]
        SUPA["Supabase\nPostgreSQL + pgvector + Storage\n+ Auth + Realtime"]
        S3["Amazon S3\nRLHF Data Lake · Audit Archive"]
        ECR["Amazon ECR\nContainer Registry"]
        SM["Secrets Manager\n+ SSM Parameter Store"]
        EB["EventBridge\n+ SQS / SNS"]
        SF["Step Functions\nLong-running pipelines"]
        MSK["Kafka / MSK\nLLMOps telemetry"]
        R53["Route 53\nDNS"]
        ACM["ACM\nTLS Certificates"]
    end

    ALB --> ECS_WEB & ECS_API
    ECS_API --> ECS_ORCH & ECS_AI
    ECS_ORCH --> ECS_AI
    ECS_AI --> SBENV

    ECS_API & ECS_ORCH & ECS_AI --> REDIS
    ECS_API & ECS_ORCH & ECS_AI --> SUPA
    ECS_AI --> S3
    ECS_ORCH --> EB & SF
    ECS_AI --> MSK

    PRIVATE_APP --> NAT --> INET
    ECS_API --> SM
```

### 11.2 ECS Service Layout

| ECS Service | Image | Port | Scale Trigger |
|---|---|---|---|
| `web` | Next.js 14 | 3000 | CPU target 60% |
| `api` | FastAPI | 8000 | RPS target |
| `ai-services` | FastAPI | 8001 | SQS queue depth |
| `orchestrator` | Python / LangGraph | internal | SQS queue depth |
| `sandbox-runner` | Docker-in-Fargate | ephemeral | On-demand per build |

Note: Supabase Realtime is a managed service — no ECS task needed.

### 11.3 Tenant Isolation Model

```mermaid
graph TB
    subgraph TenantA["Tenant A"]
        TA_JWT["JWT\ntenant_id=A"]
        TA_SCHEMA["PG Schema\ntenant_A"]
        TA_NS["Vector Namespace\ntenant_A"]
        TA_S3["S3 Prefix\ns3://bucket/A/..."]
    end

    subgraph TenantB["Tenant B"]
        TB_JWT["JWT\ntenant_id=B"]
        TB_SCHEMA["PG Schema\ntenant_B"]
        TB_NS["Vector Namespace\ntenant_B"]
        TB_S3["S3 Prefix\ns3://bucket/B/..."]
    end

    UDAL["UDAL\nResolves tenant_id from JWT\nRoutes + enforces isolation\nEmits lineage events"]

    TA_JWT --> UDAL
    TB_JWT --> UDAL
    UDAL --> TA_SCHEMA & TB_SCHEMA
    UDAL --> TA_NS & TB_NS
    UDAL --> TA_S3 & TB_S3

    UDAL -->|"Hard fail → SEV-1\nif cross-tenant access detected"| SEC["Security On-call"]
```

### 11.4 Deployment Strategy (Blue/Green)

```mermaid
flowchart LR
    PR[GitHub PR] --> GA[GitHub Actions\nlint · typecheck · tests\nsecurity scan · ECR push]
    GA --> CD[AWS CodeDeploy\nBlue/Green on ECS]
    CD --> SMOKE[Smoke Tests]
    SMOKE -->|"pass"| CANARY[10% Canary\nmetrics watch]
    CANARY -->|"metrics OK"| FULL[100% Traffic\nmark live]
    CANARY -->|"metrics fail"| ROLLBACK[Auto Rollback\nto Blue]
    FULL --> NOTIFY[Notify Founder]
```

---

## 12. Observability Stack

```mermaid
graph TB
    subgraph Sources["Signal Sources"]
        AGENTS[Agent Workers]
        ORCH[Orchestrator]
        API[API Gateway]
        FE[Frontend]
        LLM_CALLS[LLM API Calls]
    end

    subgraph Signals["Telemetry Signals"]
        LOGS["Structured Logs\n{tenant_id, pillar, agent_id,\nmodel, run_id, env}"]
        METRICS["Metrics\nRED + USE method"]
        TRACES["Distributed Traces\nW3C traceparent end-to-end"]
        LLM_TRACES["LLM Traces\nprompts, completions, scores"]
    end

    subgraph Backends["Observability Backends"]
        ELK["CloudWatch\n+ Fluent Bit\nStructured logs"]
        PROM["Prometheus\n+ Grafana\n+ Amazon Managed Grafana"]
        XRAY["AWS X-Ray\n(OTel exporter)"]
        LS["LangSmith\nLLM call spans\nEval scores\nGroundedness"]
        SENTRY["Sentry\nFrontend + Backend errors"]
        TL["LangSmith Evals\nDrift · Quality · Bias"]
    end

    AGENTS & ORCH & API --> LOGS & METRICS & TRACES
    LLM_CALLS --> LLM_TRACES

    LOGS --> ELK
    METRICS --> PROM
    TRACES --> XRAY
    LLM_TRACES --> LS
    FE --> SENTRY
    LLM_TRACES --> TL
```

**Mandatory tags on every signal**: `tenant_id` · `pillar` · `agent_id` · `model` · `run_id` · `env`

---

## 13. CI/CD Pipeline

```mermaid
flowchart TD
    DEV[Developer pushes branch] --> PR[Pull Request\nto main]

    subgraph GHA["GitHub Actions"]
        L[Lint\neslint · ruff · black] --> TC[Typecheck\ntsc strict · mypy]
        TC --> UT[Unit Tests\njest · pytest]
        UT --> IT[Integration Tests\nPlaywright · testcontainers]
        IT --> SEC[Security Scans\nTrivy · Semgrep · Snyk\nGitleaks · OWASP ZAP]
        SEC --> EVAL[LLM-as-Judge Eval\nLangSmith golden sets]
        EVAL --> BUILD[Build Images\npush to ECR]
    end

    PR --> L
    BUILD -->|"all gates pass"| DEPLOY

    subgraph DEPLOY["AWS CodeDeploy — ECS Blue/Green"]
        BG[Blue/Green Deploy] --> SMOKE2[Smoke Tests]
        SMOKE2 --> CAN[10% Canary]
        CAN --> FULL2[Ramp to 100%]
        FULL2 --> LIVE[Mark Live]
    end

    LIVE --> NOTIFY2[Notify Founder / On-call]

    L & TC & UT & IT & SEC & EVAL -->|"any gate fails"| BLOCK[Block PR merge]
```

**PR gates** (all must pass before merge): lint · typecheck · unit tests · integration tests · security scan · LLM-judge score ≥ threshold. No direct push to `main`.

---

## 14. Security Architecture

```mermaid
graph TB
    subgraph Edge["Edge Layer"]
        CF2[CloudFront] --> WAF2[AWS WAF\n+ Shield DDoS]
        WAF2 --> ALB2[ALB\nTLS 1.3 termination]
    end

    subgraph Auth["Authentication & Authorization"]
        AUTH0[Auth0\nOAuth 2.0 + SAML 2.0\nMFA enforced]
        JWT2[Short-lived JWTs\n15 min + refresh tokens\nclaims: tenant_id · role · scopes]
        OPA2[OPA Policy Engine\nRBAC + ABAC\nPolicy-as-code]
        MTLS[mTLS + signed JWTs\nService-to-service identity\nSPIFFE-style]
    end

    subgraph Secrets["Secrets Management"]
        SM2[AWS Secrets Manager] 
        SSM2[SSM Parameter Store]
        KMS2[AWS KMS\nAES-256 at rest]
    end

    subgraph Scanning["Vulnerability Scanning"]
        TRIVY2[Trivy\nContainers]
        SEMG[Semgrep + Bandit\nSAST]
        SNYK2[Snyk\nDependencies]
        GITL[Gitleaks\nSecrets in code]
        ZAP[OWASP ZAP\nDAST]
        ECR2[ECR\nImage scanning on push]
    end

    subgraph Audit["Audit & Compliance"]
        CT[CloudTrail]
        AUDITLOG[App Audit Logs\nAUDIT level — immutable]
        S3LOCK[S3 Object Lock\n7-year retention]
        CT & AUDITLOG --> S3LOCK
    end

    subgraph SandboxSec["Sandbox Security"]
        FC[Firecracker\nVM-level isolation]
        GVISOR[gVisor\nSyscall interception]
        EGRESS[Strict Egress Allow-list\nno arbitrary outbound]
    end
```

**Prompt injection defense**: all user-supplied text passes through Input Guardrail (PII redaction + injection classifier) before reaching any LLM call.

---

## 15. Performance & Scalability

### Non-Negotiable SLAs

| Metric | Target |
|---|---|
| UI response time (P95) | < 100 ms |
| Sandbox spin-up | < 10 s |
| Idea → Validated | < 30 min |
| End-to-end MVP build | ≤ 7 days |
| Deploy (code → live) | < 10 min |
| Self-heal auto-fix rate | ≥ 90% |
| First-run deploy success | ≥ 85% |
| Test coverage (generated code) | ≥ 80% |
| Platform uptime | 99.9% |
| Concurrent builds | 500 |
| COGS per MVP | < ₹500 |

### Scalability Design

```mermaid
graph LR
    subgraph Compute["ECS Auto Scaling"]
        API_ASG["api service\nTarget: RPS"]
        AI_ASG["ai-services\nTarget: SQS depth"]
        ORCH_ASG["orchestrator\nTarget: SQS depth"]
    end

    subgraph DB["Database Scaling"]
        PG_PRIMARY["RDS Primary"]
        PG_RR["Read Replicas\n(read-heavy workloads)"]
        PGBOUNCER["PgBouncer\nConnection pooling"]
        PG_PART["Partition by tenant_id\nfor large tables"]
        PG_PRIMARY --> PG_RR
        PG_PRIMARY --> PGBOUNCER
    end

    subgraph Cache["Caching Strategy"]
        REDIS2["Redis\nPlan checkpoints\nPrompt cache\nEmbedding cache\nSemantic cache (RAG)"]
    end

    subgraph Queue["Work Queue"]
        SQS2["SQS per-pillar queues\nDLQ configured\nExponential backoff + jitter"]
    end

    ALB3[ALB] --> API_ASG
    API_ASG --> ORCH_ASG & AI_ASG
    ORCH_ASG & AI_ASG --> PGBOUNCER & REDIS2
    ORCH_ASG & AI_ASG --> SQS2
```

---

## 16. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Orchestration** | LangGraph (primary) + AutoGen (fallback) | Stateful DAGs with deterministic checkpoints; AutoGen for free-form multi-agent patterns |
| **Compute** | Amazon ECS on Fargate | Serverless containers, no cluster management, per-task isolation; Kubernetes deferred to v2 |
| **Vector store** | Supabase pgvector | Eliminates separate vector DB; uses pgvector extension with vector(768) for gemini-embedding-2; HNSW index; schema-per-tenant |
| **Graph DB** | Neo4j / Amazon Neptune | TBD — pending benchmark on competitor ↔ market ↔ persona query patterns |
| **Agent isolation** | Tenant-scoped UDAL (mandatory) | Agents can never issue direct DB calls; prevents cross-tenant data leakage |
| **LLM routing** | Gemini 3.5 Flash via LiteLLM router | Unified model for all task classes; gemini-embedding-2 (768-dim) for all collections; cost optimized |
| **Prompt management** | Versioned in `prompt_registry` + S3; DSPy auto-tune | Immutable prompt artifacts + automated weekly optimization using RLHF data |
| **Sandbox isolation** | Firecracker + gVisor + strict egress allow-list | Defense-in-depth for code execution; VM-level + syscall-level isolation |
| **Deploy strategy** | Blue/green on ECS via AWS CodeDeploy | Zero-downtime; instant 1-click rollback; canary ramp before full traffic |
| **Tenant DB isolation** | Schema-per-tenant + RLS as defense-in-depth | Strong isolation with RLS as secondary safety net |
| **Human-in-the-loop** | Required gates at Pillars 1, 2, 5 (spend), 6 | Ensures founder oversight at critical decision points before irreversible actions |
| **Retry / self-heal** | Max 5 cycles in Pillar 4; then HITL escalation | Bounded autonomy — prevents infinite loops; degrades gracefully to human review |

---

*Generated from `CLAUDE.md` v1.0 — 2026-05-19*
