# Architecture Spec — AutoFounder AI

> Extracted from `CLAUDE.md` §4, §5, §6, §11, §29, §37 by `split_claude.py` (2026-06-04).
> `CLAUDE.md` is the lean index; this file holds the detail.
> Section numbers (`§N`) are preserved so cross-references stay valid.

---

## 4. High-Level Architecture (10 Layers)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  1. INPUT LAYER  (multi-modal, multi-source)                              │
│     IoT/Wearables · APIs/Webhooks/Streams · Docs/PDFs · Images · Videos   │
│     · Voice/Audio · User Feedback · Third-party Market Data               │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────────────────────────────────────────────┐
│  2. AGENT ORCHESTRATION LAYER  (LangGraph)                                │
│     Dynamic Task Allocation · Inter-Agent Comms (event bus) · Workflow & │
│     Plan Mgmt (DAGs, checkpoints) · Monitoring & Observability · HITL    │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────────────────────────────────────────────┐
│  3. AI AGENTS LAYER  (specialized & collaborative)                        │
│     Strategy & Ideation · Product Planner · Research · Engineering ·     │
│     Marketing · Finance · Ops & Risk                                     │
│     Capabilities: Planning · Reasoning · Tool Use · Memory · Self-Learn  │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────────────────────────────────────────────┐
│  4. MODEL & CAPABILITY LAYER                                              │
│     LLM (foundational + instruction-tuned) · Embeddings · Vision ·       │
│     Speech/Audio · RAG & Retrieval · RLHF / Alignment                    │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────────────────────────────────────────────┐
│  5. DATA & KNOWLEDGE LAYER                                                │
│     Raw Data Lake (S3) · Relational + Vector (Supabase — PostgreSQL +    │
│     pgvector + Storage) · Graph (Neo4j / Neptune) · Object Store ·       │
│     Cache & Session (Redis / DynamoDB)                                   │
│     ⇣ Unified Data Access Layer (APIs) ⇣                                 │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                ▼                                     ▼
┌──────────────────────────────┐  ┌───────────────────────────────────────┐
│ 6. OUTPUT & EXPERIENCE LAYER │  │ 7. SERVICE & INTEGRATION LAYER         │
│   Customisation Output       │  │   Multi-Channel Delivery (Web/Mobile/  │
│   Knowledge Updates          │  │   Email/Slack/Teams/APIs)              │
│   Enriched Synthetic Data    │  │   3rd-party (CRM/ERP/DevTools/Pay)    │
│   Actionable Automations     │  │   Automation (Zapier/n8n/Airflow/SF)   │
│   Real-time Notifications    │  │   API Gateway (REST/GraphQL/gRPC)      │
└──────────────────────────────┘  └───────────────────────────────────────┘
                                   │
┌──────────────────────────────────────────────────────────────────────────┐
│  8. GUARDRAILS & GOVERNANCE LAYER                                         │
│     Policy & Rules · Input Guardrails · Instruction Guardrails ·         │
│     Execution Guardrails · Output Guardrails · Monitoring Guardrails ·   │
│     Audit & Lineage                                                      │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────────────────────────────────────────────┐
│  9. COMPLIANCE & SECURITY LAYER                                           │
│     Ethics & Responsible AI · Regulatory (GDPR/SOC2/ISO/HIPAA) ·         │
│     Data Privacy · Interoperability/Explainability · Model Versioning · │
│     Human-AI Collaboration                                               │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────────────────────────────────────────────┐
│ 10. OBSERVABILITY & MLOPS FOUNDATION                                      │
│     Logging (ELK/OpenSearch) · Metrics (Prom/Grafana) · Tracing (OTel) · │
│     Model Monitoring · CI/CD (GitHub Actions) · Feature Store             │
│     (Feast/Tecton) · Cost & FinOps · Env Management                      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. End-to-End Workflow

The 7 product pillars map onto a single linear workflow with checkpoints and human-approval gates.

```mermaid
flowchart TD
    A[User submits text idea] --> B[Pillar 1: Strategy + Ideation]
    B --> B1{Founder Approves or Pivots?}
    B1 -- Pivot --> B
    B1 -- Approve --> C[Pillar 2: Architecture & Tech Stack]
    C --> C1{Founder Approval Gate}
    C1 -- Reject --> C
    C1 -- Approve --> D[Pillar 3: Autonomous Code Gen<br/>Frontend ‖ Backend]
    D --> E[Pillar 4: Testing & Self-Healing<br/>Max 5 retries]
    E --> E1{All green?}
    E1 -- No, retries exhausted --> EH[Escalate to Human]
    E1 -- Yes --> F[Pillar 5: Deploy & Infra<br/>Containerize, Terraform, ECS, DNS, SSL]
    F --> G[Pillar 6: Marketing & Launch<br/>Brand, SEO, Email, Social]
    G --> G1{Launch Control Center: Founder Approves}
    G1 -- Edit --> G
    G1 -- Approve --> H[Public Launch]
    H --> I[Pillar 7: LLMOps & Continuous Learning<br/>Telemetry, RLHF, A/B, Cost]
    I -.feedback.-> B
    I -.feedback.-> D
    I -.feedback.-> G
```

ROI baseline (must remain truthful in generated marketing copy):

| Stage | Traditional | AutoFounder AI |
|---|---|---|
| Idea → Validated | 3 weeks | 30 minutes |
| Validated → Built MVP | 3–6 months | 7 days |
| MVP → Deployed | 1 week | 10 minutes |
| Deployed → Marketed | 2–3 weeks | 2 hours |
| **Total** | **4–7 months** | **~7 days** |
| **Total cost** | **$20K–$60K** | **$200–$700** |

---

## 6. Component Breakdown

| # | Layer | Responsibility | Primary Tech |
|---|---|---|---|
| 1 | Input | Ingest multi-modal idea inputs | FastAPI API GW, Supabase Storage uploads, Whisper (audio), Tesseract/Vision |
| 2 | Orchestration | Schedule, route, coordinate agents | LangGraph + AutoGen fallback, Confluent Kafka, EventBridge, SQS/SNS |
| 3 | Agents | Specialized autonomous workers | LangGraph nodes, FastAPI workers |
| 4 | Models | Generate, embed, classify, vision | Gemini 3.5 Flash + gemini-embedding-2 (primary), Claude Sonnet (fallback), Whisper, DALL-E 3/Midjourney |
| 5 | Data & Knowledge | Persist all state and memory | Supabase (PostgreSQL + pgvector + Storage), Neo4j, S3, Redis |
| 6 | Output & Experience | Deliver artifacts to founder | Next.js 14 Founder Portal, Monaco editor, WebSocket streams |
| 7 | Service & Integration | Talk to 3rd parties | REST/GraphQL/gRPC, Zapier, n8n, Step Functions |
| 8 | Guardrails | Filter inputs, outputs, actions | OPA, Llama Guard, Prompt Armor, custom validators |
| 9 | Compliance | Enforce regulatory posture | AWS Config, Model Registry, Audit logs (7yr) |
| 10 | Observability/MLOps | See everything, learn from it | OpenTelemetry, ELK, Prometheus, Grafana, LangSmith, Feast |

---

## 11. Data Flow

```mermaid
sequenceDiagram
    participant U as User (Founder)
    participant FE as Next.js Portal
    participant GW as FastAPI API GW
    participant ORCH as LangGraph Orchestrator
    participant AG as Agent (Pillar N)
    participant LLM as Model Layer
    participant DAL as Unified Data Access Layer
    participant DB as PostgreSQL / Vector / Graph
    participant OBS as Observability

    U->>FE: Submit idea
    FE->>GW: POST /v1/ideas (JWT, organization_id)
    GW->>ORCH: createRun(idea, tenant)
    ORCH->>OBS: emit run.started
    ORCH->>AG: dispatch(step)
    AG->>DAL: read context
    DAL->>DB: query (tenant-scoped)
    DB-->>DAL: rows + vectors
    DAL-->>AG: context
    AG->>LLM: complete(prompt + tools)
    LLM-->>AG: response
    AG->>DAL: write artifacts
    AG->>OBS: trace (LangSmith + OTel)
    AG-->>ORCH: step.completed
    ORCH-->>GW: WebSocket stream
    GW-->>FE: live updates
    ORCH->>U: HITL gate (approve/pivot)
```

---

## 29. Multi-Agent Communication Flow

```mermaid
sequenceDiagram
    participant ORCH as LangGraph Orchestrator
    participant STR as Strategy Agent
    participant ARC as Architect (Engineering)
    participant COD as Coder (Engineering)
    participant REV as Reviewer (Engineering)
    participant DEV as DevOps (Engineering)
    participant MKT as Marketing Agent
    participant LMO as LLMOps Agent
    participant BUS as EventBridge

    ORCH->>STR: validate(idea)
    STR-->>ORCH: viability + canvas
    ORCH->>BUS: emit pillar.completed{1}
    ORCH->>ARC: design(spec)
    ARC-->>ORCH: arch + OpenAPI
    ORCH->>COD: build(arch)
    COD-->>REV: artifacts
    REV-->>COD: patches (loop ≤5)
    REV-->>ORCH: pass
    ORCH->>DEV: deploy(repo)
    DEV-->>ORCH: live_url
    ORCH->>MKT: launch(brand+url)
    MKT-->>ORCH: assets
    BUS-->>LMO: all run.* events
    LMO-->>ORCH: prompt/model updates (next run)
```

---

## 37. Output & Experience Layer (Layer 6 detail)

Outputs delivered to founders across channels:

- **Customisation Output**: reports, plans, dashboards, documents, generated code.
- **Knowledge Updates**: insights, recommendations, learnings (delivered via portal + email digest).
- **Enriched Synthetic Data**: simulations, mock data for testing.
- **Actionable Automations**: auto-tasks, workflows, execution outputs.
- **Real-time Notifications**: alerts, updates, reminders (in-app + email + Slack/Teams + SMS).

Delivery channels (Layer 7): Web App, Mobile, Email, Slack, MS Teams, public APIs.

---
