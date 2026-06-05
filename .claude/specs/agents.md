# Agents & Orchestration Spec — AutoFounder AI

> Extracted from `CLAUDE.md` §7, §8, §9, §10, §30, §32, §33 by `split_claude.py` (2026-06-04).
> `CLAUDE.md` is the lean index; this file holds the detail.
> Section numbers (`§N`) are preserved so cross-references stay valid.

---

## 7. Agent Architecture

### 7.1 Roster (canonical 7 specialized agents + sub-agents)

| Agent (Lead) | Pillar | Role | Key Sub-Agents |
|---|---|---|---|
| **Strategy & Ideation Agent** | 1 | Owns end-to-end idea validation | Competitor Tracker, Trend Analyst, Persona Builder, Canvas Composer |
| **Product Planner Agent** | 1.5 | PRDs, roadmaps, requirements, user stories | — |
| **Research Agent** | 1 | Market/user/competitor/tech research | — |
| **Engineering Agent (Architect + Coder + Reviewer + DevOps composite domain)** | 2–5 | Code, architecture, APIs, infra | Architect, Schema Designer, API Contract Agent, Stack Advisor, Cost Estimator, Frontend Specialist, Backend Specialist, Integration Agent, Repo Manager, QA & Test Agent, Reviewer, Self-Healer, Sandbox Manager, Quality Gate Agent, DevOps, Infra Provisioner, Deployment Orchestrator, DNS & SSL Agent, Observability Agent, Security & Compliance Agent |
| **Marketing Agent** | 6 | GTM, content, campaigns | SEO Writer, Visual Designer, Social Scheduler, Email Marketer, Launch Coordinator, Analytics Agent |
| **Finance Agent** | (cross) | Financial models, unit economics, projections | — |
| **Ops & Risk Agent** | (cross) | Risk assessment, compliance, operations | — |
| **LLMOps Agent (Analytics Agent lead)** | 7 | Continuous learning | Feedback Loop Agent, Prompt Optimizer, Model Router, Drift Monitor, Experimentation Agent |

### 7.2 Standard agent capabilities (every agent exposes)

- **Planning** — goal → DAG of atomic steps.
- **Reasoning & Reflection** — chain-of-thought + self-critique pass.
- **Tool / API Use** — typed tool calls via MCP and internal gRPC.
- **Memory & Context Use** — short-term (Redis), long-term (Vector + Graph).
- **Self-Learning Loop** — feeds traces into LLMOps Agent.
- **Goal Decomposition & Execution** — recursive breakdown until atomic.

### 7.3 Agent contract (Python)

```python
from abc import ABC, abstractmethod
from typing import AsyncIterable

class Agent(ABC):
    id: str              # e.g. "strategist.v3"
    organization_id: str
    capabilities: list[str]
    tools: list[ToolSpec]

    @abstractmethod
    async def understand(self, input: AgentInput) -> Intent: ...

    @abstractmethod
    async def plan(self, intent: Intent) -> Plan: ...        # DAG of Steps

    @abstractmethod
    async def execute(self, plan: Plan) -> AsyncIterable[StepEvent]: ...

    @abstractmethod
    async def verify(self, output: AgentOutput) -> VerifyResult: ...

    @abstractmethod
    async def learn(self, trace: ExecutionTrace) -> None: ...  # emits to LLMOps
```

### 7.4 Pillar 1 — Strategy & Ideation (detail)

- **Inputs**: raw text idea (and optionally PDFs, voice notes, URLs).
- **Sub-workflows**: Market Sizing (TAM/SAM/SOM), Competitor Discovery, Keyword & Intent Mining, Persona Generation, Lean Canvas, Viability Scoring (0–100), Bias Audit, Pivot Suggestions.
- **Tools**: Tavily, SerpAPI, Crunchbase, ProductHunt, G2, Capterra, SimilarWeb, Reddit, Hacker News, LinkedIn, Google Trends.
- **Outputs**: 5-page Market Analysis, Lean Canvas, ICPs (3–5), viability score, bias audit, 3 pivot options.
- **SLA**: < 30 min total.

### 7.5 Pillar 2 — Architecture & Tech Stack

- **Sub-workflows**: Requirements Extraction (FRs/NFRs/use cases), DB Schema Design (ERD + indexes), API Contract (OpenAPI), Tech Stack Selection, Microservice Boundary Analysis, Auth Strategy, Scaling Plan & Cost Forecast.
- **Tools**: GitHub, Mermaid, draw.io, Postman, Swagger Hub, AWS Pricing API, dbdiagram.io, Confluence.
- **Architecture principles enforced**: Security by Design, Scalable by Default, Cost Optimized, Observable & Reliable, Modular & Evolvable.
- **Gate**: Founder Approval Gate (HITL).

### 7.6 Pillar 3 — Autonomous Code Generation

- **Sub-workflows**: Repo Scaffolding, parallel Frontend (Next.js 14 + Tailwind + shadcn/ui) + Backend (FastAPI) generation, Database layer (SQLAlchemy + Supabase migrations + seeds), Auth (OAuth/JWT/RBAC via Supabase Auth), Stripe integration, Admin Panel auto-gen, Code Style Enforcement (Prettier + ESLint + Black + Ruff).
- **Output deliverables**: Source Code, CI/CD Pipeline, Documentation, Deployed Preview, PR with Checks.
- **Targets**: zero linting errors, TypeScript strict, mypy clean.

### 7.7 Pillar 4 — Testing & Self-Healing

- **Sub-workflows**: Static Analysis → Unit Test Generation → Integration Tests → Security Scanning (Trivy/Semgrep/Snyk/OWASP ZAP/Gitleaks) → Sandbox Execution (ephemeral Docker, isolated network) → Self-Correction Loop → AST-Aware Refactoring → LLM-as-Judge Review.
- **Retry policy**: max 5 self-heal cycles; on failure escalate to human.
- **Targets**: ≥ 80% coverage, ≥ 90% auto-fix rate, OWASP Top 10 clean.
- **Sandbox SLA**: < 10 s spin-up (Docker + Firecracker + gVisor + Testcontainers).

### 7.8 Pillar 5 — Deployment & Infrastructure

- **Sub-workflows**: Containerization (multi-stage Dockerfile + compose), IaC (Terraform/CloudFormation/Pulumi/CDK), Cluster Provisioning (**ECS Fargate** + Supabase + ElastiCache + S3), Domain & SSL (Route53 + ACM + Let's Encrypt), Secrets Management (AWS Secrets Manager + SSM Parameter Store), Monitoring Setup (CloudWatch + Prometheus + Grafana + Sentry + Datadog), CI/CD Pipeline, Rollback Plan (blue/green or canary, 1-click revert).
- **Deploy SLA**: < 10 min code → live.
- **Uptime target**: 99.9%+.

> ⚠️ **Architecture correction**: prior internal docs mentioned EKS. The authoritative deployment target is **Amazon ECS on Fargate** (see §18). Migrate any references.

### 7.9 Pillar 6 — Marketing & Launch Automation

- **Sub-workflows**: Brand Generation (name/logo/palette/voice), Landing Page Build (SEO hero/features/pricing/social proof/CTA), SEO Content Engine (10 blog drafts targeting target keywords + internal linking), Email Drip Sequences (welcome/onboarding/value/retention/re-engagement), Product Hunt Kit, Hacker News post, X/Twitter launch thread (8–10 tweets), LinkedIn + Reddit cross-posts.
- **Tools**: ProductHunt, X, LinkedIn, Reddit, Hacker News, Mailchimp, Resend, Typefully, Webflow, Framer, Ahrefs, DALL-E 3, Midjourney.
- **Hallucination check**: every claim must be cross-referenced against the Architect Agent's feature list.
- **Approval gate**: Launch Control Center — nothing posts publicly without founder sign-off.

### 7.10 Pillar 7 — Growth, LLMOps & Continuous Learning

- **Sub-workflows**: User Feedback Capture → Trace Analysis (LangSmith) → Prompt Optimization (DSPy/Promptfoo) → Model Routing → Hallucination Tracking → Drift Detection → A/B & Canary Experimentation → Cost Telemetry (per-user, per-MVP token + compute).
- **Cadence**: weekly fine-tune / prompt-opt cycle.
- **Tools**: LangSmith, TruLens, Promptfoo, DSPy, PostHog, Mixpanel, Amplitude, AWS Step Functions, S3, Prometheus, Grafana, AWS Cost Explorer.

---

## 8. LLM Orchestration Layer

### 8.1 Orchestrator

- **Primary**: LangGraph (stateful, graph-based, deterministic checkpoints).
- **Fallback**: AutoGen for free-form multi-agent chat patterns.
- **State**: every node persists checkpoint to PostgreSQL (`orchestrator.checkpoints`) and Redis (hot cache).
- **Plans**: each run produces a DAG serialized as JSON in `orchestrator.runs`.

### 8.2 Dynamic task allocation

- Tasks pulled from a priority queue (Redis Streams + SQS).
- Router weights: tenant tier (Enterprise > Startup > Solo), pillar, SLA deadline, current model COGS, agent health.

### 8.3 Inter-agent communication

- **Synchronous**: gRPC (Protocol Buffers) for low-latency request/response.
- **Asynchronous**: AWS EventBridge + SQS/SNS for fan-out events (`run.started`, `agent.completed`, `gate.required`, `human.approved`).
- **Streaming**: Supabase Realtime for live log + token streaming to the Founder Portal.

### 8.4 Workflow & plan management

- Plans are DAGs with: nodes (steps), edges (deps), checkpoints, retry policies, HITL gates, time budgets.
- Engine: LangGraph + AWS Step Functions for long-running multi-day pipelines (Pillar 7 weekly cycle).

### 8.5 HITL (Human-in-the-Loop) gates

| Gate | Pillar | Default policy |
|---|---|---|
| Validation Approve/Pivot | 1 | Required |
| Architecture Approval | 2 | Required |
| Infrastructure Spend > $X | 5 | Required (configurable) |
| Launch Control (public post) | 6 | Required |
| Production Rollout (canary → 100%) | 7 | Auto if metrics pass |

---

## 9. Memory Architecture

| Layer | Store | Purpose | TTL |
|---|---|---|---|
| Working / Scratch | In-process | Current step buffer | step |
| Short-term (Session) | Redis Cluster | Active build state, agent message bus | 24 h sliding |
| Episodic | Supabase PostgreSQL (`memory.episodes`) | Per-run trace, gates, decisions | 90 d default |
| Semantic (Long-term) | Supabase pgvector | Embeddings of patterns, prior MVPs, user prefs | unbounded (tenant-scoped) |
| Procedural | Prompt + Tool Registry (Postgres) + Feature Store | Reusable agent skills/playbooks | versioned |
| Relational Knowledge | Neo4j / Amazon Neptune | Entity graphs (competitors ↔ markets ↔ personas) | unbounded |
| Cold Archive | S3 (Raw Data Lake) | Compressed traces, RLHF datasets | 7 y (audit) |

Memory is always **tenant-partitioned** (key prefix `organization_id/`, row-level security in Postgres, namespace per tenant in vector store).

---

## 10. Knowledge Base / Vector DB Design

### 10.1 Collections (per-tenant namespaces)

| Collection | Embedding model | Used by |
|---|---|---|
| `market_intelligence` | `gemini-embedding-2` | Strategy, Research |
| `competitor_features` | `gemini-embedding-2` | Strategy, Marketing |
| `code_patterns` | `gemini-embedding-2` | Engineering |
| `architecture_decisions` | `gemini-embedding-2` | Engineering, LLMOps |
| `brand_voice_examples` | `gemini-embedding-2` | Marketing |
| `prompt_library` | `gemini-embedding-2` | LLMOps |
| `user_preferences` | `gemini-embedding-2` | All |

### 10.2 RAG pipeline

```
Query → Query Rewriting (LLM) → Hybrid Retrieval (BM25 + ANN) →
Cross-encoder Re-ranking → Context Compression → LLM Answer →
Citation Check (Output Guardrail) → Response
```

Implementation: LlamaIndex / LangChain Retrievers; reranker via Cohere Rerank or BGE-reranker-large.

---

## 30. Prompt Management Strategy

- **Storage**: versioned in `prompt_registry` (Postgres) + S3 (immutable artifacts).
- **Lifecycle**: draft → eval (Promptfoo + LangSmith golden sets) → canary (5% traffic) → promote.
- **A/B testing**: LLMOps Agent assigns variant by user/tenant bucket; Promptfoo regression suite gates promotion.
- **Optimization**: weekly DSPy pipeline auto-tunes prompts using captured RLHF data.
- **Templating**: Jinja2 with strict variable validation; no string-concat prompts.

---

## 32. Tool Calling / MCP Integration

- All tools registered in `tool_registry` with JSON-schema args + auth scope + cost class.
- Agents call tools via MCP-style typed handles; the Execution Guardrail validates each call (schema, allow-list, rate-limit, cost-cap).
- Tool execution is sandboxed (ephemeral Fargate task with strict egress policy).
- Failures are typed (`ToolError.RateLimit`, `ToolError.Auth`, `ToolError.Schema`) and feed the self-heal planner.

---

## 33. RAG Pipeline

See §10.2. Mandatory components: query rewriting, hybrid retrieval (BM25 + dense), reranking, context compression, citation/groundedness check on output. Every RAG response logs retrieved doc IDs + scores to LangSmith for groundedness audits.

---
