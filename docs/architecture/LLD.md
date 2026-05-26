# AutoFounder AI — Low-Level Design (LLD)

**Org**: Euron AutoFounder AI · **Contact**: product@euron.one  
**Version**: 1.0 · **Date**: 2026-05-19  
**Companion**: `docs/HLD.md` (system-level view)

---

## Table of Contents

1. [Module Breakdown](#1-module-breakdown)
2. [Data Models & Schemas](#2-data-models--schemas)
   - 2.1 PostgreSQL (per-tenant schema)
   - 2.2 TypeScript domain types
   - 2.3 Python/Pydantic models
   - 2.4 Vector store document schemas
   - 2.5 Graph DB node/edge schema
   - 2.6 Redis key schema
3. [API Contracts](#3-api-contracts)
   - 3.1 REST API (FastAPI)
   - 3.2 gRPC proto definitions
   - 3.3 WebSocket message protocol
   - 3.4 Internal event schema (EventBridge)
4. [Component Interfaces](#4-component-interfaces)
   - 4.1 Agent base interface
   - 4.2 UDAL interface
   - 4.3 Guardrails middleware interface
   - 4.4 Tool registry interface
   - 4.5 Prompt registry interface
5. [Sequence Diagrams](#5-sequence-diagrams)
   - 5.1 Idea submission and run creation
   - 5.2 Pillar 1 — Strategy & ideation
   - 5.3 Pillar 2 — Architecture approval gate
   - 5.4 Pillar 3 — Parallel code generation
   - 5.5 Pillar 4 — Self-heal loop
   - 5.6 Pillar 5 — ECS deployment
   - 5.7 Pillar 6 — Launch control center gate
   - 5.8 Pillar 7 — LLMOps weekly cycle
   - 5.9 JWT auth and tenant resolution
   - 5.10 RAG pipeline
   - 5.11 Guardrails pipeline per agent call
6. [Service-Level Component Breakdown](#6-service-level-component-breakdown)
   - 6.1 `apps/api` — FastAPI API Gateway
   - 6.2 `apps/orchestrator` — LangGraph Engine
   - 6.3 `apps/ai-services` — FastAPI Agent Workers
   - 6.4 Supabase Realtime — WebSocket Fan-out (Managed)
   - 6.5 `apps/web` — Next.js Founder Portal
   - 6.6 `packages/db` — UDAL
   - 6.7 `packages/agents` — Agent implementations
   - 6.8 `packages/guardrails` — Guardrails pipeline
   - 6.9 `packages/tools` — MCP tool registry
   - 6.10 `packages/prompts` — Prompt registry
7. [Key Design Decisions & Trade-offs](#7-key-design-decisions--trade-offs)
8. [Dependency Matrix](#8-dependency-matrix)
9. [Error Handling Specifications](#9-error-handling-specifications)
10. [Configuration & Environment Variables](#10-configuration--environment-variables)

---

## 1. Module Breakdown

```
autofounder-ai/
├── apps/
│   ├── api/                         # FastAPI API Gateway  (Python 3.12)
│   │   ├── main.py                  # FastAPI app, lifespan, middleware
│   │   ├── routers/
│   │   │   ├── ideas.py             # POST /v1/ideas
│   │   │   ├── runs.py              # GET /v1/runs/:id, artifacts
│   │   │   ├── gates.py             # POST /v1/runs/:id/gates/:gate_id
│   │   │   ├── tenants.py           # Tenant management
│   │   │   ├── llmops.py            # GET /v1/llmops/cost
│   │   │   └── feedback.py          # POST /v1/feedback
│   │   ├── auth/
│   │   │   ├── jwt.py               # Supabase JWT validation
│   │   │   ├── opa.py               # OPA policy guard
│   │   │   └── tenant.py            # TenantContext dependency
│   │   ├── schemas/                 # Pydantic request/response models
│   │   ├── grpc_client.py           # gRPC stubs → orchestrator
│   │   ├── openapi.yaml             # OpenAPI 3.1 spec (auto-generated + pinned)
│   │   └── tests/
│   │
│   ├── orchestrator/                # LangGraph engine  (Python 3.12)
│   │   ├── orchestrator/
│   │   │   ├── main.py              # FastAPI entrypoint + gRPC server
│   │   │   ├── graph/
│   │   │   │   ├── builder.py       # LangGraph StateGraph factory
│   │   │   │   ├── nodes.py         # Node definitions (one per pillar step)
│   │   │   │   ├── edges.py         # Conditional edge logic
│   │   │   │   ├── state.py         # RunState TypedDict
│   │   │   │   └── checkpointer.py  # Postgres + Redis checkpointer
│   │   │   ├── planner/
│   │   │   │   ├── dag.py           # Plan → DAG serializer
│   │   │   │   └── router.py        # Task priority router
│   │   │   ├── hitl/
│   │   │   │   ├── gate_manager.py  # Gate state machine
│   │   │   │   └── notifier.py      # EventBridge gate.required events
│   │   │   ├── events/
│   │   │   │   ├── producer.py      # EventBridge publisher
│   │   │   │   └── consumer.py      # SQS consumer
│   │   │   └── proto/               # Generated gRPC stubs
│   │   └── tests/
│   │
│   ├── ai-services/                 # FastAPI agent workers  (Python 3.12)
│   │   ├── main.py                  # FastAPI app + SQS worker loop
│   │   ├── agents/                  # Agent entry-points (thin wrappers)
│   │   │   ├── strategy_runner.py
│   │   │   ├── engineering_runner.py
│   │   │   └── marketing_runner.py
│   │   ├── llm/
│   │   │   ├── router.py            # LiteLLM model router
│   │   │   ├── cache.py             # Semantic + prompt cache (Redis)
│   │   │   └── clients.py           # Google AI (Gemini) client
│   │   ├── rag/
│   │   │   ├── retriever.py         # Hybrid BM25 + ANN
│   │   │   ├── reranker.py          # Cohere / BGE reranker
│   │   │   └── pipeline.py          # End-to-end RAG chain
│   │   ├── sandbox/
│   │   │   ├── runner.py            # Fargate sandbox task launcher
│   │   │   └── executor.py          # Code execution + output capture
│   │   └── proto/
│   │
│   # Realtime: Supabase Realtime (managed service — no separate app service)
│   # Frontend subscribes directly to Supabase Realtime channels per run_id.
│   # Orchestrator publishes step events via Supabase client (postgres NOTIFY).
│   │
│   ├── web/                         # Next.js 14 Founder Portal
│   │   ├── app/
│   │   │   ├── (auth)/              # Supabase Auth login/callback routes
│   │   │   ├── dashboard/           # Run list + overview
│   │   │   ├── runs/[id]/
│   │   │   │   ├── validation/      # Pillar 1 — Validation Studio
│   │   │   │   ├── architecture/    # Pillar 2 — Architecture Studio
│   │   │   │   ├── code/            # Pillar 3 — Code Review Studio
│   │   │   │   ├── deploy/          # Pillar 5 — Deploy Console
│   │   │   │   ├── launch/          # Pillar 6 — Launch Control Center
│   │   │   │   └── llmops/          # Pillar 7 — LLMOps Dashboard
│   │   │   └── admin/               # Super-admin (separate layout)
│   │   ├── components/
│   │   │   ├── lean-canvas/
│   │   │   ├── erd-viewer/
│   │   │   ├── openapi-viewer/
│   │   │   ├── monaco-diff/
│   │   │   ├── deploy-console/
│   │   │   └── llmops-dashboard/
│   │   ├── lib/
│   │   │   ├── api-client.ts        # Typed REST client (fetch wrapper)
│   │   │   ├── ws-client.ts         # WebSocket hook
│   │   │   └── store/               # Zustand stores (per surface)
│   │   └── hooks/
│   │       ├── useRun.ts            # React Query + WS merge
│   │       └── useGate.ts           # Gate polling + mutation
│   │
│   └── admin/                       # Next.js super-admin (internal)
│
├── packages/
│   ├── agents/                      # Agent logic (Python)
│   │   ├── strategy/
│   │   │   ├── agent.py             # StrategyAgent(BaseAgent)
│   │   │   ├── sub_agents/
│   │   │   │   ├── competitor_tracker.py
│   │   │   │   ├── trend_analyst.py
│   │   │   │   ├── persona_builder.py
│   │   │   │   └── canvas_composer.py
│   │   │   └── prompts/             # Jinja2 templates
│   │   ├── research/
│   │   │   └── agent.py             # ResearchAgent(BaseAgent)
│   │   ├── product_planner/
│   │   │   └── agent.py             # ProductPlannerAgent(BaseAgent)
│   │   ├── engineering/
│   │   │   ├── architect/agent.py
│   │   │   ├── coder/
│   │   │   │   ├── agent.py
│   │   │   │   ├── frontend_specialist.py
│   │   │   │   └── backend_specialist.py
│   │   │   ├── reviewer/
│   │   │   │   ├── agent.py
│   │   │   │   └── self_healer.py
│   │   │   └── devops/agent.py
│   │   ├── marketing/
│   │   │   ├── agent.py
│   │   │   └── sub_agents/
│   │   │       ├── seo_writer.py
│   │   │       ├── visual_designer.py
│   │   │       └── social_scheduler.py
│   │   ├── finance/agent.py
│   │   ├── ops_risk/agent.py
│   │   ├── llmops/
│   │   │   ├── agent.py
│   │   │   ├── prompt_optimizer.py  # DSPy pipeline
│   │   │   ├── model_router.py      # LiteLLM routing rules
│   │   │   └── drift_monitor.py     # TruLens + Evidently
│   │   └── base_agent.py            # BaseAgent ABC
│   │
│   ├── guardrails/                  # Guardrails pipeline (Python)
│   │   ├── pipeline.py              # 6-stage orchestrator
│   │   ├── stages/
│   │   │   ├── policy.py            # Stage 1 — OPA call
│   │   │   ├── input_guard.py       # Stage 2 — Llama Guard + Presidio
│   │   │   ├── instruction_guard.py # Stage 3 — Prompt validators
│   │   │   ├── execution_guard.py   # Stage 4 — Tool call middleware
│   │   │   ├── output_guard.py      # Stage 5 — TruLens + citation check
│   │   │   └── monitoring_guard.py  # Stage 6 — anomaly rules
│   │   └── audit.py                 # Immutable audit log writer
│   │
│   ├── tools/                       # MCP tool definitions (Python)
│   │   ├── registry.py              # ToolRegistry singleton
│   │   ├── research/
│   │   │   ├── tavily.py
│   │   │   ├── serpapi.py
│   │   │   └── crunchbase.py
│   │   ├── engineering/
│   │   │   ├── github.py
│   │   │   ├── stripe.py
│   │   │   └── aws_pricing.py
│   │   ├── marketing/
│   │   │   ├── producthunt.py
│   │   │   ├── twitter.py
│   │   │   └── resend.py
│   │   └── base_tool.py             # BaseTool ABC
│   │
│   ├── prompts/                     # Versioned Jinja2 prompt templates
│   │   ├── registry.py              # PromptRegistry (DB-backed)
│   │   ├── templates/
│   │   │   ├── strategy/
│   │   │   ├── engineering/
│   │   │   ├── marketing/
│   │   │   └── shared/
│   │   └── validator.py             # Variable completeness checker
│   │
│   ├── db/                          # UDAL + SQLAlchemy (Python) + Supabase client
│   │   ├── python/
│   │   │   ├── udal.py              # UDAL Python client (primary)
│   │   │   ├── relational.py        # SQLAlchemy async + Supabase PostgreSQL
│   │   │   ├── vector.py            # Supabase pgvector (vecs client)
│   │   │   ├── graph.py             # Neo4j async driver
│   │   │   └── object.py            # Supabase Storage + S3 (data lake)
│   │   ├── ts/
│   │   │   └── udal.ts              # UDAL TypeScript client (frontend read-only)
│   │   └── migrations/              # Supabase SQL migrations
│   │       └── supabase/
│   │
│   ├── shared/                      # Cross-language shared types
│   │   ├── types/
│   │   │   ├── run.ts
│   │   │   ├── agent.ts
│   │   │   ├── gate.ts
│   │   │   └── events.ts
│   │   └── constants.ts
│   │
│   └── eval/                        # Eval harness
│       ├── run_evals.py
│       ├── golden_sets/
│       └── promptfoo.config.yaml
│
└── infra/
    ├── terraform/
    │   ├── modules/
    │   │   ├── ecs/                 # Task defs, services, auto-scaling
    │   │   # rds/ removed — database managed by Supabase
    │   │   ├── elasticache/         # Redis cluster
    │   │   ├── networking/          # VPC, subnets, NAT, SGs
    │   │   ├── alb/                 # ALB + listener rules
    │   │   ├── s3/                  # Buckets + lifecycle
    │   │   ├── eventbridge/         # Event buses + rules
    │   │   └── iam/                 # Roles + policies
    │   └── env/
    │       ├── staging.tfvars
    │       └── production.tfvars
    └── codedeploy/
        ├── appspec.yml
        └── scripts/
```

---

## 2. Data Models & Schemas

### 2.1 PostgreSQL — Platform Schema (`platform`)

```sql
-- ─────────────────────────────────────────────
-- PLATFORM schema (shared across all tenants)
-- ─────────────────────────────────────────────

CREATE SCHEMA platform;

CREATE TABLE platform.tenants (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  slug          TEXT UNIQUE NOT NULL,
  tier          TEXT NOT NULL CHECK (tier IN ('solo','startup','enterprise')),
  status        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','deleted')),
  settings      JSONB NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at    TIMESTAMPTZ
);

CREATE TABLE platform.tenant_api_keys (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES platform.tenants(id) ON DELETE CASCADE,
  key_hash      TEXT NOT NULL UNIQUE,   -- bcrypt hash; never store raw key
  label         TEXT,
  scopes        TEXT[] NOT NULL DEFAULT '{}',
  expires_at    TIMESTAMPTZ,
  revoked_at    TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE platform.model_registry (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_id      TEXT NOT NULL,          -- e.g. "gemini-1.5-flash-002"
  provider      TEXT NOT NULL,          -- "google"|"openai"|"bedrock"
  version       TEXT NOT NULL,
  task_classes  TEXT[] NOT NULL,        -- ["complex_reasoning","self_healing",...]
  cost_per_1k_input_tokens   NUMERIC(12,6) NOT NULL,
  cost_per_1k_output_tokens  NUMERIC(12,6) NOT NULL,
  eval_scores   JSONB NOT NULL DEFAULT '{}',
  is_active     BOOLEAN NOT NULL DEFAULT true,
  rollback_to   UUID REFERENCES platform.model_registry(id),
  registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE platform.prompt_registry (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,          -- e.g. "strategy.market_sizing.v2"
  version       TEXT NOT NULL,          -- semver
  agent         TEXT NOT NULL,
  template_s3   TEXT NOT NULL,          -- s3://bucket/prompts/{name}/{version}.j2
  variables     JSONB NOT NULL,         -- required variable schema
  status        TEXT NOT NULL DEFAULT 'draft'
                  CHECK (status IN ('draft','canary','active','deprecated')),
  eval_score    NUMERIC(5,2),
  created_by    TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (name, version)
);

CREATE TABLE platform.tool_registry (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL UNIQUE,   -- e.g. "tavily.search"
  description   TEXT NOT NULL,
  args_schema   JSONB NOT NULL,         -- JSON Schema for input args
  auth_scope    TEXT NOT NULL,          -- required permission scope
  cost_class    TEXT NOT NULL CHECK (cost_class IN ('free','low','medium','high')),
  rate_limit    JSONB NOT NULL DEFAULT '{}',  -- {requests_per_min, tokens_per_day}
  is_active     BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE platform.audit_log (
  id            BIGSERIAL PRIMARY KEY,
  tenant_id     UUID,
  run_id        UUID,
  agent_id      TEXT,
  action        TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id   TEXT,
  actor         TEXT NOT NULL,         -- user_id or "system"
  outcome       TEXT NOT NULL CHECK (outcome IN ('allowed','denied','error')),
  metadata      JSONB,
  occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- audit_log is append-only; writes are funnelled through audit.py only.
-- S3 Object Lock export runs nightly.
```

### 2.2 PostgreSQL — Per-Tenant Schema (`tenant_<uuid>`)

```sql
-- ─────────────────────────────────────────────
-- PER-TENANT schema (one schema per tenant)
-- Created automatically on tenant provisioning.
-- RLS is set as defense-in-depth; UDAL is the primary enforcement.
-- ─────────────────────────────────────────────

-- RUNS
CREATE TABLE runs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pillar        TEXT NOT NULL,                -- "1"|"2"|"3"|"4"|"5"|"6"|"7"
  status        TEXT NOT NULL DEFAULT 'queued'
                  CHECK (status IN ('queued','running','paused','completed','failed','cancelled')),
  plan          JSONB NOT NULL DEFAULT '{}',  -- serialized LangGraph DAG
  idea_text     TEXT NOT NULL,
  idea_meta     JSONB NOT NULL DEFAULT '{}',  -- multimodal attachments, URLs
  current_step  TEXT,
  retry_count   INT NOT NULL DEFAULT 0,
  model_used    TEXT,
  cost_usd      NUMERIC(12,6) NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at    TIMESTAMPTZ,
  completed_at  TIMESTAMPTZ,
  created_by    TEXT NOT NULL               -- user_id from JWT
);
CREATE INDEX ON runs (status, created_at DESC);

-- ARTIFACTS
CREATE TABLE artifacts (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id        UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  pillar        TEXT NOT NULL,
  kind          TEXT NOT NULL,
                -- 'lean_canvas'|'market_analysis'|'personas'|'erd'|
                -- 'openapi_spec'|'repo_url'|'live_url'|'brand_kit'|
                -- 'landing_page'|'email_sequence'|'social_posts'
  uri           TEXT NOT NULL,               -- s3:// or https://
  size_bytes    BIGINT,
  checksum      TEXT,                        -- SHA-256 of artifact
  metadata      JSONB NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON artifacts (run_id, kind);

-- GATES (HITL checkpoints)
CREATE TABLE gates (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id        UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  kind          TEXT NOT NULL,
                -- 'validation_approve'|'architecture_approve'|
                -- 'infra_spend_approve'|'launch_approve'|'canary_rollout'
  state         TEXT NOT NULL DEFAULT 'pending'
                  CHECK (state IN ('pending','approved','rejected','timed_out')),
  payload       JSONB NOT NULL DEFAULT '{}',  -- data displayed to founder
  decided_by    TEXT,                          -- user_id
  decided_at    TIMESTAMPTZ,
  timeout_at    TIMESTAMPTZ,                   -- NULL = no timeout
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON gates (run_id, state);

-- STEP EVENTS (append-only agent execution log)
CREATE TABLE step_events (
  id            BIGSERIAL PRIMARY KEY,
  run_id        UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  step_id       TEXT NOT NULL,
  agent_id      TEXT NOT NULL,
  event_type    TEXT NOT NULL,
                -- 'step.started'|'step.completed'|'step.failed'|
                -- 'llm.call'|'tool.call'|'tool.result'|'self_heal'
  payload       JSONB NOT NULL DEFAULT '{}',
  token_cost    JSONB,                         -- {input_tokens, output_tokens, cost_usd}
  occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON step_events (run_id, occurred_at);

-- MEMORY EPISODES
CREATE TABLE memory_episodes (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id        UUID REFERENCES runs(id) ON DELETE SET NULL,
  agent_id      TEXT NOT NULL,
  kind          TEXT NOT NULL,   -- 'decision'|'reflection'|'gate_outcome'|'tool_result'
  content       TEXT NOT NULL,
  embedding_id  TEXT,            -- reference to vector store document ID
  importance    NUMERIC(3,2),   -- 0.0–1.0, used for memory retrieval ranking
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at    TIMESTAMPTZ      -- NULL = permanent (within 90d default)
);
CREATE INDEX ON memory_episodes (agent_id, created_at DESC);
CREATE INDEX ON memory_episodes (run_id);

-- COST LEDGER (per-run, per-model billing)
CREATE TABLE cost_ledger (
  id              BIGSERIAL PRIMARY KEY,
  run_id          UUID NOT NULL REFERENCES runs(id),
  model_id        TEXT NOT NULL,
  input_tokens    BIGINT NOT NULL DEFAULT 0,
  output_tokens   BIGINT NOT NULL DEFAULT 0,
  cost_usd        NUMERIC(12,6) NOT NULL,
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.3 TypeScript Domain Types (`packages/shared/types/`)

```typescript
// run.ts

export type RunStatus =
  | 'queued' | 'running' | 'paused'
  | 'completed' | 'failed' | 'cancelled';

export type PillarId = '1' | '2' | '3' | '4' | '5' | '6' | '7';

export interface Run {
  id: string;
  tenantId: string;
  pillar: PillarId;
  status: RunStatus;
  plan: PlanDAG;
  ideaText: string;
  ideaMeta: IdeaMeta;
  currentStep: string | null;
  retryCount: number;
  costUsd: number;
  createdAt: Date;
  startedAt: Date | null;
  completedAt: Date | null;
  createdBy: string;
}

export interface IdeaMeta {
  attachments?: { kind: 'pdf' | 'image' | 'audio' | 'url'; uri: string }[];
  locale?: string;
  targetMarket?: string;
}

export interface PlanDAG {
  nodes: PlanNode[];
  edges: PlanEdge[];
  checkpointId: string | null;
}

export interface PlanNode {
  id: string;
  agentId: string;
  stepType: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  retryPolicy: RetryPolicy;
  timeBudgetMs: number | null;
  hitlGateId: string | null;
}

export interface PlanEdge {
  from: string;
  to: string;
  condition?: string; // e.g. "gate.approved"
}

export interface RetryPolicy {
  maxAttempts: number;
  backoffMs: number;
  backoffMultiplier: number;
}

// gate.ts

export type GateKind =
  | 'validation_approve'
  | 'architecture_approve'
  | 'infra_spend_approve'
  | 'launch_approve'
  | 'canary_rollout';

export type GateState = 'pending' | 'approved' | 'rejected' | 'timed_out';

export interface Gate {
  id: string;
  runId: string;
  kind: GateKind;
  state: GateState;
  payload: Record<string, unknown>;
  decidedBy: string | null;
  decidedAt: Date | null;
  timeoutAt: Date | null;
  createdAt: Date;
}

// agent.ts

export type Capability =
  | 'planning' | 'reasoning' | 'tool_use'
  | 'memory' | 'self_learning' | 'code_gen'
  | 'market_research' | 'deployment' | 'marketing';

export interface ToolSpec {
  name: string;
  argsSchema: Record<string, unknown>;
  authScope: string;
  costClass: 'free' | 'low' | 'medium' | 'high';
}

export interface Intent {
  goal: string;
  constraints: string[];
  context: Record<string, unknown>;
  priority: 'low' | 'normal' | 'high' | 'critical';
}

export interface StepEvent {
  stepId: string;
  agentId: string;
  eventType: string;
  payload: Record<string, unknown>;
  tokenCost?: { inputTokens: number; outputTokens: number; costUsd: number };
  occurredAt: Date;
}

export interface VerifyResult {
  passed: boolean;
  score: number;        // 0.0–1.0
  issues: string[];
  suggestedFixes: string[];
}

export interface ExecutionTrace {
  runId: string;
  stepId: string;
  agentId: string;
  prompt: string;
  response: string;
  toolCalls: ToolCallRecord[];
  tokenCost: { inputTokens: number; outputTokens: number; costUsd: number };
  latencyMs: number;
  guardrailResults: GuardrailResult[];
  verifyResult: VerifyResult;
}

export interface ToolCallRecord {
  toolName: string;
  args: Record<string, unknown>;
  result: unknown;
  latencyMs: number;
  error?: string;
}

export interface GuardrailResult {
  stage: 1 | 2 | 3 | 4 | 5 | 6;
  passed: boolean;
  action: 'allow' | 'block' | 'modify' | 'flag';
  reason?: string;
}

// events.ts

export type EventType =
  | 'run.started' | 'run.completed' | 'run.failed' | 'run.cancelled'
  | 'pillar.completed' | 'step.started' | 'step.completed' | 'step.failed'
  | 'gate.required' | 'gate.approved' | 'gate.rejected'
  | 'agent.failed' | 'human.approved'
  | 'llmops.prompt_updated' | 'llmops.model_rotated';

export interface PlatformEvent {
  id: string;
  type: EventType;
  tenantId: string;
  runId: string;
  pillar?: PillarId;
  agentId?: string;
  model?: string;
  env: 'sandbox' | 'staging' | 'production';
  payload: Record<string, unknown>;
  emittedAt: Date;
}
```

### 2.4 Python / Pydantic Models (`packages/agents/`)

```python
# packages/agents/base_agent.py

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncIterator, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class Capability(str):
    PLANNING = "planning"
    REASONING = "reasoning"
    TOOL_USE = "tool_use"
    MEMORY = "memory"
    SELF_LEARNING = "self_learning"
    CODE_GEN = "code_gen"
    MARKET_RESEARCH = "market_research"
    DEPLOYMENT = "deployment"
    MARKETING = "marketing"


class Intent(BaseModel):
    goal: str
    constraints: list[str] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
    priority: str = "normal"


class PlanStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    tool_calls: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    retry_policy: dict = Field(default_factory=lambda: {
        "max_attempts": 3,
        "backoff_ms": 1000,
        "backoff_multiplier": 2.0,
    })
    time_budget_ms: int | None = None


class Plan(BaseModel):
    steps: list[PlanStep]
    estimated_cost_usd: float = 0.0
    estimated_duration_ms: int = 0


class StepEvent(BaseModel):
    step_id: str
    agent_id: str
    event_type: str
    payload: dict = Field(default_factory=dict)
    token_cost: dict | None = None
    occurred_at: datetime = Field(default_factory=datetime.utcnow)


class VerifyResult(BaseModel):
    passed: bool
    score: float  # 0.0–1.0
    issues: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)


class ExecutionTrace(BaseModel):
    run_id: str
    step_id: str
    agent_id: str
    tenant_id: str
    prompt: str
    response: str
    tool_calls: list[dict] = Field(default_factory=list)
    token_cost: dict = Field(default_factory=dict)
    latency_ms: int = 0
    guardrail_results: list[dict] = Field(default_factory=list)
    verify_result: VerifyResult | None = None


class BaseAgent(ABC, Generic[TInput, TOutput]):
    def __init__(self, agent_id: str, tenant_id: str):
        self.id = agent_id
        self.tenant_id = tenant_id

    @property
    @abstractmethod
    def capabilities(self) -> list[str]: ...

    @property
    @abstractmethod
    def tools(self) -> list[str]: ...

    @abstractmethod
    async def understand(self, input: TInput) -> Intent: ...

    @abstractmethod
    async def plan(self, intent: Intent) -> Plan: ...

    @abstractmethod
    async def execute(self, plan: Plan) -> AsyncIterator[StepEvent]: ...

    @abstractmethod
    async def verify(self, output: TOutput) -> VerifyResult: ...

    async def learn(self, trace: ExecutionTrace) -> None:
        # Emit to LLMOps agent via EventBridge — default implementation
        from packages.tools.registry import tool_registry
        await tool_registry.get("eventbridge.publish").call({
            "event_type": "agent.trace",
            "tenant_id": self.tenant_id,
            "payload": trace.model_dump(),
        })


# ─── Strategy agent models ───────────────────────────────────────────────────

class StrategyInput(BaseModel):
    idea_text: str
    attachments: list[dict] = Field(default_factory=list)
    locale: str = "en"
    target_market: str | None = None


class Persona(BaseModel):
    name: str
    role: str
    pain_points: list[str]
    goals: list[str]
    channels: list[str]
    willingness_to_pay: str


class LeanCanvas(BaseModel):
    problem: list[str]
    solution: list[str]
    unique_value_proposition: str
    unfair_advantage: str
    customer_segments: list[str]
    key_metrics: list[str]
    channels: list[str]
    cost_structure: list[str]
    revenue_streams: list[str]


class MarketSizing(BaseModel):
    tam_usd: float
    sam_usd: float
    som_usd: float
    assumptions: list[str]


class StrategyOutput(BaseModel):
    lean_canvas: LeanCanvas
    personas: list[Persona]          # 3–5 ICPs
    market_sizing: MarketSizing
    viability_score: float           # 0–100
    bias_audit: dict
    pivot_options: list[dict]        # 3 alternatives
    market_analysis_s3_uri: str
    competitors: list[dict]


# ─── Engineering agent models ─────────────────────────────────────────────────

class ArchitectInput(BaseModel):
    run_id: str
    strategy_output: StrategyOutput
    founder_prefs: dict = Field(default_factory=dict)


class TechStackChoice(BaseModel):
    frontend: str
    backend: str
    database: str
    auth: str
    deployment: str
    rationale: str
    cost_estimate_usd_monthly: float


class ERDEntity(BaseModel):
    name: str
    fields: list[dict]               # [{name, type, nullable, pk, fk, indexed}]
    relationships: list[dict]        # [{target, cardinality}]


class APIContract(BaseModel):
    openapi_version: str = "3.1.0"
    title: str
    version: str
    paths: dict                       # OpenAPI paths object


class ArchitectOutput(BaseModel):
    tech_stack: TechStackChoice
    erd: list[ERDEntity]
    api_contract: APIContract
    architecture_diagram_s3_uri: str
    scaling_plan: dict
    security_plan: dict
    cost_forecast_usd_monthly: float


class CoderInput(BaseModel):
    run_id: str
    architect_output: ArchitectOutput


class CoderOutput(BaseModel):
    repo_url: str
    pr_url: str
    branch: str
    files_generated: int
    lint_passed: bool
    typecheck_passed: bool


# ─── Marketing agent models ───────────────────────────────────────────────────

class MarketingInput(BaseModel):
    run_id: str
    strategy_output: StrategyOutput
    live_url: str
    feature_list: list[str]


class BrandKit(BaseModel):
    name: str
    tagline: str
    colors: dict                    # {primary, secondary, accent}
    logo_s3_uri: str
    voice: str                      # tone description
    og_image_s3_uri: str


class MarketingOutput(BaseModel):
    brand_kit: BrandKit
    landing_page_url: str
    blog_posts: list[dict]          # [{title, s3_uri, target_keyword}]
    email_sequences: list[dict]     # [{name, subject_lines, body_s3_uri}]
    social_posts: dict              # {twitter: [...], linkedin: [...], reddit: [...]}
    producthunt_kit_s3_uri: str
```

### 2.5 Vector Store Document Schema

All collections live in Supabase pgvector, namespaced per tenant (schema-per-tenant + pgvector extension).

```sql
-- All vector tables live in the per-tenant schema "tenant_<uuid>"
-- pgvector extension enabled: CREATE EXTENSION IF NOT EXISTS vector;

-- market_intelligence
CREATE TABLE market_intelligence (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id      UUID,
  source      TEXT,                  -- "tavily" | "crunchbase" | etc.
  source_url  TEXT,
  content     TEXT NOT NULL,
  embedding   vector(768),           -- gemini-embedding-2
  topic       TEXT,                  -- "tam" | "competitor" | "trend" | "regulation"
  created_at  TIMESTAMPTZ DEFAULT now(),
  expires_at  TIMESTAMPTZ
);
CREATE INDEX ON market_intelligence USING hnsw (embedding vector_cosine_ops);

-- code_patterns
CREATE TABLE code_patterns (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  language      TEXT,
  framework     TEXT,
  pattern_type  TEXT,                -- "crud" | "auth" | "payment" | "webhook"
  code          TEXT NOT NULL,
  embedding     vector(768),         -- gemini-embedding-2
  quality_score NUMERIC(3,2),
  created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON code_patterns USING hnsw (embedding vector_cosine_ops);

-- architecture_decisions
CREATE TABLE architecture_decisions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id       UUID,
  decision     TEXT NOT NULL,
  rationale    TEXT,
  alternatives TEXT[],
  outcome      TEXT,                 -- "chosen" | "rejected" | "deferred"
  embedding    vector(768),         -- gemini-embedding-2
  created_at   TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON architecture_decisions USING hnsw (embedding vector_cosine_ops);

-- prompt_library
CREATE TABLE prompt_library (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_name TEXT NOT NULL,
  version     TEXT NOT NULL,
  content     TEXT NOT NULL,
  embedding   vector(768),          -- gemini-embedding-2
  eval_score  NUMERIC(5,2),
  created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON prompt_library USING hnsw (embedding vector_cosine_ops);

-- user_preferences
CREATE TABLE user_preferences (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         TEXT NOT NULL,
  preference_key  TEXT NOT NULL,
  preference_val  TEXT,
  embedding       vector(768),       -- gemini-embedding-2
  created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON user_preferences USING hnsw (embedding vector_cosine_ops);
```

### 2.6 Graph DB Schema (Neo4j)

```
Nodes:
  (:Tenant   {id, name, tier})
  (:Idea     {id, run_id, text, created_at})
  (:Competitor {id, name, url, category, founded_year})
  (:Market   {id, name, tam_usd, geography})
  (:Persona  {id, name, role, pain_points[]})
  (:Feature  {id, name, description, mvp_run_id})
  (:Technology {id, name, category, version})

Relationships:
  (Tenant)-[:HAS_RUN]->(Idea)
  (Idea)-[:TARGETS]->(Market)
  (Competitor)-[:OPERATES_IN]->(Market)
  (Competitor)-[:HAS_FEATURE]->(Feature)
  (Persona)-[:MEMBER_OF]->(Market)
  (Idea)-[:ADDRESSES_PAIN_OF]->(Persona)
  (Idea)-[:USES_TECH]->(Technology)
  (Feature)-[:IMPLEMENTED_WITH]->(Technology)
  (Competitor)-[:COMPETES_WITH {similarity_score: float}]->(Competitor)
```

### 2.7 Redis Key Schema

```
# Plan checkpoints (LangGraph hot cache)
Key:  "orch:checkpoint:{run_id}"
Type: Hash
TTL:  86400 (24h)
Fields: {state, current_node, last_updated}

# Agent session state
Key:  "agent:session:{run_id}:{agent_id}"
Type: Hash
TTL:  86400
Fields: {status, last_step, context_snapshot}

# Prompt cache (semantic dedup)
Key:  "llm:prompt_cache:{sha256_of_normalized_prompt}"
Type: String (JSON)
TTL:  3600 (1h)
Value: {response, model, tokens, cached_at}

# Embedding cache
Key:  "embed:cache:{sha256_of_text}:{model}"
Type: String (JSON)
TTL:  86400
Value: {embedding: float[], dim: int}

# Task priority queue
Key:  "queue:tasks:{pillar}"
Type: Sorted Set
Score: priority_score (higher = more urgent)
Member: {run_id, step_id, tenant_tier, enqueued_at}

# Per-tenant cost accumulator (sliding window)
Key:  "cost:{tenant_id}:{YYYY-MM}"
Type: Hash
TTL:  end of month + 7d
Fields: {total_usd, llm_usd, infra_usd, tool_usd}

# Rate limit counters (per tenant, per tool)
Key:  "ratelimit:{tenant_id}:{tool_name}:{minute_bucket}"
Type: String (integer)
TTL:  120
```

---

## 3. API Contracts

### 3.1 REST API — FastAPI (`apps/api`)

#### `POST /v1/ideas`
```
Request headers:
  Authorization: Bearer <jwt>
  Content-Type: application/json

Request body:
  {
    "idea_text": "string (required, 10–5000 chars)",
    "attachments": [          // optional
      {"kind": "pdf"|"image"|"audio"|"url", "uri": "string"}
    ],
    "locale": "string (default: en)",
    "target_market": "string (optional)"
  }

Response 201:
  {
    "run_id": "uuid",
    "status": "queued",
    "created_at": "ISO 8601",
    "stream_url": "/v1/runs/{run_id}/stream"
  }

Response 400: validation error (idea_text too short/long, unknown attachment kind)
Response 402: tenant cost cap exceeded
Response 429: tenant rate limit exceeded
```

#### `GET /v1/runs/{id}`
```
Response 200:
  {
    "id": "uuid",
    "status": "queued"|"running"|"paused"|"completed"|"failed"|"cancelled",
    "pillar": "1"–"7",
    "current_step": "string|null",
    "cost_usd": 0.00,
    "active_gates": [
      {
        "id": "uuid",
        "kind": "validation_approve"|...,
        "state": "pending",
        "payload": {},
        "created_at": "ISO 8601"
      }
    ],
    "artifacts": [
      {"id": "uuid", "kind": "lean_canvas", "uri": "s3://...", "created_at": "..."}
    ],
    "plan": { /* PlanDAG */ },
    "created_at": "ISO 8601",
    "completed_at": "ISO 8601|null"
  }

Response 404: run not found (or belongs to different tenant)
```

#### `POST /v1/runs/{id}/gates/{gate_id}`
```
Request body:
  {
    "decision": "approved"|"rejected",
    "note": "string (optional)",
    "pivot_option": { /* StrategyOutput.pivot_options[i] — only for validation gate */ }
  }

Response 200:
  {
    "gate_id": "uuid",
    "state": "approved"|"rejected",
    "decided_at": "ISO 8601",
    "next_step": "string"    // what the orchestrator will do next
  }

Response 409: gate already decided
Response 404: gate not found
```

#### `GET /v1/runs/{id}/artifacts`
```
Response 200:
  {
    "artifacts": [
      {
        "id": "uuid",
        "kind": "string",
        "uri": "string",
        "size_bytes": 0,
        "metadata": {},
        "created_at": "ISO 8601"
      }
    ]
  }
```

#### `GET /v1/runs/{id}/stream` (WebSocket upgrade)
```
Upgrade: websocket
Protocol: wss://

Server → Client messages (JSON-LD frames):
  {"type": "step.started",    "step_id": "...", "agent_id": "...", "at": "..."}
  {"type": "token",           "content": "...", "step_id": "..."}
  {"type": "tool.call",       "tool": "...", "args": {...}, "step_id": "..."}
  {"type": "tool.result",     "tool": "...", "result": {...}, "step_id": "..."}
  {"type": "step.completed",  "step_id": "...", "at": "..."}
  {"type": "gate.required",   "gate_id": "...", "kind": "...", "payload": {...}}
  {"type": "run.completed",   "run_id": "...", "cost_usd": 0.00}
  {"type": "run.failed",      "run_id": "...", "error": "..."}

Client → Server:
  {"type": "ping"}
  (gate decisions are made via REST POST, not WebSocket)
```

#### `POST /v1/feedback`
```
Request body:
  {
    "run_id": "uuid",
    "step_id": "string",
    "signal": "accept"|"reject"|"edit",
    "original": "string (the agent output)",
    "edited": "string (only if signal=edit)",
    "comment": "string (optional)"
  }

Response 202: accepted for async LLMOps processing
```

#### `GET /v1/llmops/cost`
```
Query params: tenant_id, from (ISO date), to (ISO date)

Response 200:
  {
    "tenant_id": "uuid",
    "period": {"from": "...", "to": "..."},
    "total_usd": 0.00,
    "by_model": [{"model_id": "...", "usd": 0.00, "tokens": 0}],
    "by_pillar": [{"pillar": "1", "usd": 0.00}],
    "by_run":    [{"run_id": "...", "usd": 0.00}]
  }
```

### 3.2 gRPC Proto Definitions

```protobuf
// proto/orchestrator.proto
syntax = "proto3";
package autofounder.orchestrator.v1;

service OrchestratorService {
  rpc CreateRun(CreateRunRequest)       returns (CreateRunResponse);
  rpc GetRunState(GetRunStateRequest)   returns (RunState);
  rpc DecideGate(DecideGateRequest)     returns (DecideGateResponse);
  rpc CancelRun(CancelRunRequest)       returns (CancelRunResponse);
}

message CreateRunRequest {
  string tenant_id  = 1;
  string idea_text  = 2;
  bytes  idea_meta  = 3; // JSON-encoded IdeaMeta
  string created_by = 4;
}

message CreateRunResponse {
  string run_id     = 1;
  string status     = 2;
}

message GetRunStateRequest {
  string tenant_id = 1;
  string run_id    = 2;
}

message RunState {
  string run_id      = 1;
  string status      = 2;
  string current_step = 3;
  bytes  plan        = 4; // JSON-encoded PlanDAG
  double cost_usd    = 5;
}

message DecideGateRequest {
  string tenant_id = 1;
  string run_id    = 2;
  string gate_id   = 3;
  string decision  = 4; // "approved" | "rejected"
  string note      = 5;
  bytes  payload   = 6; // extra data (pivot choice etc.)
}

message DecideGateResponse {
  string gate_id    = 1;
  string new_state  = 2;
}

message CancelRunRequest {
  string tenant_id = 1;
  string run_id    = 2;
  string reason    = 3;
}

message CancelRunResponse {
  bool success = 1;
}

// proto/agent_worker.proto
service AgentWorkerService {
  rpc DispatchStep(DispatchStepRequest) returns (stream StepEventProto);
  rpc HealthCheck(HealthCheckRequest)  returns (HealthCheckResponse);
}

message DispatchStepRequest {
  string run_id    = 1;
  string step_id   = 2;
  string agent_id  = 3;
  string tenant_id = 4;
  bytes  input     = 5; // JSON-encoded agent-specific input
}

message StepEventProto {
  string step_id    = 1;
  string event_type = 2;
  bytes  payload    = 3; // JSON
  int64  timestamp  = 4; // Unix millis
}
```

### 3.3 EventBridge Event Schema

```json
// Envelope (all platform events)
{
  "version": "0",
  "id": "<uuid>",
  "source": "autofounder.platform",
  "detail-type": "<EventType>",
  "detail": {
    "schema_version": "1.0",
    "tenant_id": "<uuid>",
    "run_id": "<uuid>",
    "pillar": "1",
    "agent_id": "strategy.v1",
    "model": "gemini-1.5-flash-002",
    "env": "production",
    "payload": { /* event-specific data */ },
    "emitted_at": "2026-05-19T10:00:00Z"
  }
}

// gate.required payload
{
  "gate_id": "<uuid>",
  "kind": "validation_approve",
  "display_data": {
    "lean_canvas": { /* LeanCanvas */ },
    "viability_score": 78,
    "pivot_options": [...]
  },
  "timeout_at": "2026-05-19T11:00:00Z"
}

// pillar.completed payload
{
  "pillar": "1",
  "duration_ms": 1245000,
  "artifacts": [
    {"kind": "lean_canvas", "uri": "s3://..."},
    {"kind": "market_analysis", "uri": "s3://..."}
  ],
  "cost_usd": 0.38
}

// agent.failed payload
{
  "agent_id": "engineering.reviewer.v2",
  "step_id": "self_heal_cycle_4",
  "error_class": "MaxRetriesExceeded",
  "error_message": "...",
  "retry_count": 5,
  "escalated_to_human": true
}
```

---

## 4. Component Interfaces

### 4.1 Agent Base Interface (TypeScript)

```typescript
// packages/shared/types/agent.ts

export interface Agent<TInput, TOutput> {
  readonly id: string;           // e.g. "strategy.v3"
  readonly tenantId: string;
  readonly capabilities: Capability[];
  readonly tools: ToolSpec[];

  understand(input: TInput): Promise<Intent>;
  plan(intent: Intent): Promise<Plan>;
  execute(plan: Plan): AsyncIterable<StepEvent>;
  verify(output: TOutput): Promise<VerifyResult>;
  learn(trace: ExecutionTrace): Promise<void>;
}

// packages/shared/types/udal.ts

export interface UDAL {
  relational<T>(
    query: RelationalQuery
  ): Promise<T[]>;

  vector(
    collection: VectorCollection,
    query: VectorQuery
  ): Promise<VectorSearchResult[]>;

  graph(
    cypher: string,
    params?: Record<string, unknown>
  ): Promise<unknown[]>;

  object: {
    put(key: string, body: Buffer, contentType: string): Promise<string>;
    get(key: string): Promise<Buffer>;
    delete(key: string): Promise<void>;
    presignedUrl(key: string, expiresIn: number): Promise<string>;
  };
}

export interface RelationalQuery {
  schema: string;          // "platform" or "tenant_<uuid>"
  table: string;
  operation: 'select' | 'insert' | 'update' | 'delete';
  data?: Record<string, unknown>;
  where?: Record<string, unknown>;
  returning?: string[];
  limit?: number;
  offset?: number;
  orderBy?: { column: string; direction: 'asc' | 'desc' }[];
}

export type VectorCollection =
  | 'market_intelligence' | 'competitor_features'
  | 'code_patterns'       | 'architecture_decisions'
  | 'brand_voice_examples'| 'prompt_library'
  | 'user_preferences';

export interface VectorQuery {
  embedding?: number[];      // dense query vector
  text?: string;             // will be embedded if embedding omitted
  filter?: Record<string, unknown>;
  topK: number;
  includeEmbeddings?: boolean;
}

export interface VectorSearchResult {
  id: string;
  score: number;
  document: Record<string, unknown>;
}
```

### 4.2 Guardrails Pipeline Interface (Python)

```python
# packages/guardrails/pipeline.py

from dataclasses import dataclass
from enum import Enum
from typing import Any


class GuardrailAction(str, Enum):
    ALLOW  = "allow"
    BLOCK  = "block"
    MODIFY = "modify"
    FLAG   = "flag"


@dataclass
class GuardrailContext:
    tenant_id: str
    run_id: str
    agent_id: str
    pillar: str
    user_input: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None
    llm_output: str | None = None
    cost_so_far_usd: float = 0.0


@dataclass
class GuardrailResult:
    stage: int           # 1–6
    passed: bool
    action: GuardrailAction
    reason: str | None = None
    modified_content: Any = None  # only when action=MODIFY


class GuardrailsPipeline:
    """
    Wraps every agent invocation.
    Raises GuardrailBlockError on action=BLOCK.
    Returns (content, list[GuardrailResult]) on success.
    """

    async def run_input(
        self, content: str, ctx: GuardrailContext
    ) -> tuple[str, list[GuardrailResult]]:
        """Stages 1–3: policy, input guard, instruction guard."""
        ...

    async def run_execution(
        self, tool_name: str, tool_args: dict, ctx: GuardrailContext
    ) -> tuple[dict, list[GuardrailResult]]:
        """Stage 4: execution guard before tool call."""
        ...

    async def run_output(
        self, content: str, ctx: GuardrailContext
    ) -> tuple[str, list[GuardrailResult]]:
        """Stage 5: output guard after LLM response."""
        ...

    async def run_monitoring(
        self, trace: dict, ctx: GuardrailContext
    ) -> list[GuardrailResult]:
        """Stage 6: async post-hoc monitoring (does not block)."""
        ...
```

### 4.3 Tool Registry Interface (Python)

```python
# packages/tools/registry.py

from pydantic import BaseModel
from typing import Any, Callable, Awaitable


class ToolSpec(BaseModel):
    name: str
    description: str
    args_schema: dict          # JSON Schema
    auth_scope: str
    cost_class: str            # "free"|"low"|"medium"|"high"
    rate_limit: dict           # {requests_per_min, tokens_per_day}


class BaseTool:
    spec: ToolSpec

    async def call(self, args: dict) -> Any: ...
    async def validate_args(self, args: dict) -> None: ...


class ToolRegistry:
    """Singleton. Agents must access tools through this — never directly."""

    def get(self, name: str) -> BaseTool: ...
    def register(self, tool: BaseTool) -> None: ...
    def list_by_scope(self, scope: str) -> list[ToolSpec]: ...
```

### 4.4 Prompt Registry Interface (Python)

```python
# packages/prompts/registry.py

from pydantic import BaseModel


class PromptVersion(BaseModel):
    id: str
    name: str
    version: str
    agent: str
    template_s3: str
    variables: dict            # {var_name: {type, required, description}}
    status: str                # "draft"|"canary"|"active"|"deprecated"
    eval_score: float | None


class PromptRegistry:
    """
    Always returns the 'active' version unless tenant is in a canary bucket.
    Falls back to previous active version on eval regression.
    """

    async def get(
        self,
        name: str,
        tenant_id: str,
        variables: dict
    ) -> str:
        """Resolve, render (Jinja2), and validate prompt. Returns final string."""
        ...

    async def register(self, prompt: PromptVersion) -> None: ...
    async def promote(self, name: str, version: str) -> None: ...
    async def rollback(self, name: str) -> PromptVersion: ...
```

---

## 5. Sequence Diagrams

### 5.1 Idea Submission and Run Creation

```
Founder              Next.js Portal          FastAPI API GW         LangGraph Orch         PostgreSQL (platform)
  |                       |                        |                       |                        |
  |-- POST /v1/ideas ----->|                        |                       |                        |
  |   {idea_text, ...}     |                        |                       |                        |
  |                        |-- POST /v1/ideas ----->|                       |                        |
  |                        |   Authorization: Bearer <jwt>                  |                        |
  |                        |                        |                       |                        |
  |                        |                        |-- validateJWT()        |                        |
  |                        |                        |-- extractTenantId()    |                        |
  |                        |                        |-- OPA.check(policy)    |                        |
  |                        |                        |-- checkCostCap()  ---->|                        |
  |                        |                        |                        |-- GET cost:{tenant_id} |
  |                        |                        |                        |<-- {total_usd}         |
  |                        |                        |                        |                        |
  |                        |                        |-- gRPC CreateRun() --->|                        |
  |                        |                        |   {tenant_id, idea}    |                        |
  |                        |                        |                        |-- INSERT runs -------->|
  |                        |                        |                        |<-- {run_id}            |
  |                        |                        |                        |-- enqueue SQS pillar-1 |
  |                        |                        |<-- {run_id, "queued"} -|                        |
  |                        |<-- 201 {run_id} -------|                        |                        |
  |<-- 201 {run_id} -------|                        |                        |                        |
  |                        |                        |                        |                        |
  |-- WS connect ---------->-- WS upgrade -------->|                        |                        |
  |   /v1/runs/{id}/stream  |                        |-- auth WS token -----> |                        |
  |                        |                        |-- Supabase Realtime channel subscribed [run_id]  |
```

### 5.2 Pillar 1 — Strategy Agent Execution

```
Orchestrator       SQS (pillar-1)      AI Services        Strategy Agent      Guardrails       UDAL           LLM (Gemini)      EventBridge
     |                   |                   |                    |                  |             |                 |                |
     |-- poll() -------->|                   |                    |                  |             |                 |                |
     |<-- {run_id, step} |                   |                    |                  |             |                 |                |
     |                   |                   |                    |                  |             |                 |                |
     |-- gRPC DispatchStep(run_id, "strategy.understand") ------->|                  |             |                 |                |
     |                   |                   |                    |                  |             |                 |                |
     |                   |                   |                    |-- run_input() -->|             |                 |                |
     |                   |                   |                    |   Stage 1: OPA check           |                 |                |
     |                   |                   |                    |   Stage 2: PII redact,         |                 |                |
     |                   |                   |                    |            injection scan       |                 |                |
     |                   |                   |                    |   Stage 3: prompt constraints  |                 |                |
     |                   |                   |                    |<-- (clean_input, results) ---  |                 |                |
     |                   |                   |                    |                  |             |                 |                |
     |                   |                   |                    |-- udal.vector("market_intel") ->|                |                |
     |                   |                   |                    |                  |-- query Supabase pgvector ----> |                |
     |                   |                   |                    |                  |<-- top_k docs              -- |                |
     |                   |                   |                    |<-- {context docs}|             |                 |                |
     |                   |                   |                    |                  |             |                 |                |
     |                   |                   |                    |-- tool: tavily.search() ------> (Execution Guard, then call)      |
     |                   |                   |                    |-- tool: serpapi.search() -----> (parallel)                        |
     |                   |                   |                    |<-- {search results} ----------                                     |
     |                   |                   |                    |                  |             |                 |                |
     |                   |                   |                    |-- prompt_registry.get("strategy.canvas") ------> (Jinja2 render)  |
     |                   |                   |                    |-- llm.complete(prompt) ------------------------------------------>|
     |                   |                   |                    |<-- {lean_canvas_json, viability_score} --------------------------  |
     |                   |                   |                    |                  |             |                 |                |
     |                   |                   |                    |-- run_output() ->|             |                 |                |
     |                   |                   |                    |   Stage 5: hallucination check                  |                |
     |                   |                   |                    |   (viability claims vs search evidence)         |                |
     |                   |                   |                    |<-- (verified_output) --------  |                |                |
     |                   |                   |                    |                  |             |                 |                |
     |                   |                   |                    |-- udal.object.put("lean_canvas.json") --------> |                |
     |                   |                   |                    |-- udal.relational INSERT artifacts              |                |
     |                   |                   |                    |-- learn(trace) -- EventBridge emit "agent.trace"--------------->  |
     |                   |                   |                    |                  |             |                 |                |
     |<-- StepEvent("step.completed") -------|                    |                  |             |                 |                |
     |-- UPDATE runs SET status='paused' (gate required)          |                  |             |                 |                |
     |-- INSERT gates(kind='validation_approve', state='pending')  |                |             |                 |                |
     |-- emit gate.required ------------------------------------------------------------------>  |                |                |
```

### 5.3 HITL Gate — Founder Approves Architecture

```
Founder        Portal (Next.js)       FastAPI API GW        Orchestrator         PostgreSQL
  |                  |                      |                      |                   |
  | (sees gate UI)   |                      |                      |                   |
  |                  |                      |                      |                   |
  |-- click Approve->|                      |                      |                   |
  |                  |-- POST /v1/runs/{id}/gates/{gate_id} ------>|                   |
  |                  |   {"decision":"approved"}                    |                   |
  |                  |                      |-- validateJWT() ----  |                   |
  |                  |                      |-- gRPC DecideGate() ->|                   |
  |                  |                      |                        |-- UPDATE gates   |
  |                  |                      |                        |   SET state='approved'
  |                  |                      |                        |-- UPDATE runs    |
  |                  |                      |                        |   SET status='running'
  |                  |                      |                        |-- enqueue SQS pillar-3
  |                  |                      |                        |-- emit gate.approved -> EventBridge
  |                  |                      |<-- {gate_id, "approved", next_step} -----|
  |                  |<-- 200 {state:approved, next_step} ------   |                   |
  |<-- WS gate.resolved + step.started -----|                      |                   |
```

### 5.4 Pillar 3 — Parallel Frontend + Backend Code Generation

```
Orchestrator         AI Services         Coder Agent            Frontend Spec      Backend Spec
     |                    |                    |                       |                  |
     |-- DispatchStep("coder.scaffold") ------>|                       |                  |
     |                    |                    |-- plan() generates 3 parallel branches   |
     |                    |                    |                       |                  |
     |                    |         ┌──────────┴──────────┐            |                  |
     |                    |         |          |           |           |                  |
     |                    |  [FE branch]  [BE branch]  [DB branch]    |                  |
     |                    |         |          |           |           |                  |
     |                    |  frontend_specialist.run()    |           |                  |
     |                    |  (Next.js 14, Tailwind,       |           |                  |
     |                    |   shadcn/ui, Zustand)         |           |                  |
     |                    |         |                     |           |                  |
     |                    |                  backend_specialist.run() |                  |
     |                    |                  (FastAPI,               |                  |
     |                    |                   SQLAlchemy + Supabase migrations,          |
     |                    |                   OAuth/JWT, Stripe)      |                  |
     |                    |         |          |                      |                  |
     |                    |                               db_agent.run()                 |
     |                    |                               (ERD → SQLAlchemy models,      |
     |                    |                                migrations, seeds)            |
     |                    |         |          |           |                             |
     |                    |         └──────────┴───────────┘                            |
     |                    |                    |                                         |
     |                    |                    |-- repo_manager.create_repo() [GitHub]   |
     |                    |                    |-- repo_manager.push_branches()          |
     |                    |                    |-- repo_manager.open_pr()               |
     |                    |                    |-- emit step.completed {repo_url, pr_url}|
     |<-- CoderOutput {repo_url, pr_url} ----  |                                         |
     |-- enqueue pillar-4 (Reviewer)           |                                         |
```

### 5.5 Pillar 4 — Self-Heal Loop

```
Orchestrator         Reviewer Agent          Self-Healer          Sandbox Runner       Quality Gate
     |                     |                      |                     |                   |
     |-- DispatchStep("reviewer.run_full") ------->|                     |                   |
     |                     |                      |                     |                   |
     |                     |-- static_analysis() (Semgrep, ESLint, mypy)                   |
     |                     |-- run_unit_tests()  ─────────────────────> sandbox.exec()     |
     |                     |<── {results: [PASS/FAIL], coverage: 76%} ─ |                   |
     |                     |                      |                     |                   |
     |                     |  [coverage < 80% OR test failures]         |                   |
     |                     |-- self_healer.fix(failures) -------------> |                   |
     |                     |   attempt 1 of 5                          |                   |
     |                     |   [AST-aware patch via LLM]                |                   |
     |                     |   [push patch to PR branch]                |                   |
     |                     |                      |                     |                   |
     |                     |-- rerun_tests() ──────────────────────────>|                   |
     |                     |<── {coverage: 82%, all PASS} ─────────────|                   |
     |                     |                      |                     |                   |
     |                     |-- security_scan() (Trivy, Snyk, Gitleaks, OWASP ZAP)         |
     |                     |-- llm_as_judge_review() [Gemini 3.5 Flash]                    |
     |                     |<── {judge_score: 0.91, issues: []}         |                   |
     |                     |                      |                     |                   |
     |                     |-- quality_gate.evaluate()  ──────────────────────────────────>|
     |                     |   checks: coverage≥80, no critical vulns,  |                  |
     |                     |           judge_score≥0.85, zero lint errors                  |
     |                     |<── {passed: true} ──────────────────────────────────────────  |
     |<── ReviewerOutput{passed:true, pr_url} ──  |                     |                   |
     |-- enqueue pillar-5                          |                     |                   |
     |                     |                      |                     |                   |
     |   [IF all 5 retries exhausted and still failing]                 |                   |
     |-- INSERT gates(kind='escalation', state='pending')               |                   |
     |-- emit gate.required                        |                     |                   |
```

### 5.6 Pillar 5 — ECS Deployment

```
Orchestrator       DevOps Agent        Infra Provisioner      AWS APIs              DNS+SSL Agent
     |                  |                     |                    |                      |
     |-- DispatchStep("devops.deploy") ------->|                    |                      |
     |                  |                     |                    |                      |
     |                  |-- build_docker_image()                    |                      |
     |                  |   (multi-stage, generated Dockerfile)     |                      |
     |                  |-- ecr.push_image() ──────────────────────>| ECR.push            |
     |                  |                     |                    |                      |
     |                  |-- infra_provisioner.apply() ─────────────>|                      |
     |                  |                     |-- terraform init    |                      |
     |                  |                     |-- terraform plan    |                      |
     |                  |                     |-- [cost > threshold]→ infra_spend gate     |
     |                  |                     |-- terraform apply   |                      |
     |                  |                     |   ECS task def, service, ElastiCache (Supabase DB is managed)  |
     |                  |                     |<── {service_arn, alb_dns} ───────────────  |
     |                  |                     |                    |                      |
     |                  |-- dns_ssl_agent.configure() ─────────────────────────────────> |
     |                  |                     |                    |  Route53 record      |
     |                  |                     |                    |  ACM cert request    |
     |                  |                     |                    |  cert validated      |
     |                  |                     |                    |<── {live_url} ─────  |
     |                  |                     |                    |                      |
     |                  |-- smoke_test(live_url) (HTTP + auth check)                       |
     |                  |<── {status: 200, latency_ms: 180}         |                      |
     |                  |                     |                    |                      |
     |                  |-- setup_monitoring()                      |                      |
     |                  |   (CloudWatch dashboards, Grafana datasource, Sentry DSN)        |
     |                  |                     |                    |                      |
     |<── {live_url, service_arn, rollback_fn} |                    |                      |
     |-- UPDATE artifacts(kind='live_url')    |                    |                      |
```

### 5.7 Pillar 6 — Launch Control Center Gate

```
Orchestrator       Marketing Agent       Launch Coordinator    Founder Portal      External Platforms
     |                   |                      |                    |                     |
     |-- DispatchStep("marketing.generate") ---->|                    |                    |
     |                   |-- brand_gen (DALL-E 3, brand kit)         |                    |
     |                   |-- landing_page_build()                    |                    |
     |                   |-- seo_content_engine() (10 blog drafts)   |                    |
     |                   |-- email_drip_gen()                        |                    |
     |                   |-- social_post_gen()                       |                    |
     |                   |                      |                    |                    |
     |                   |-- output_guard.marketing_check()          |                    |
     |                   |   [cross-ref every claim vs               |                    |
     |                   |    architect_output.feature_list]         |                    |
     |                   |<── (verified_assets)                      |                    |
     |                   |                      |                    |                    |
     |<── MarketingOutput |                      |                    |                    |
     |-- INSERT gate(kind='launch_approve')      |                    |                    |
     |-- emit gate.required ──────────────────────────────────────> WS push to portal    |
     |                   |                      |                    |                    |
     |                   |    [Founder reviews landing page, posts, email sequences]      |
     |                   |                      |                    |                    |
     |                   |                      | POST /gates/{id}  <─ Founder clicks Approve
     |<── gate.approved  |                      |                    |                    |
     |-- DispatchStep("launch_coordinator.publish")                  |                    |
     |                   |-- post ProductHunt ────────────────────────────────────────> PH API
     |                   |-- post HN story ──────────────────────────────────────────> HN API
     |                   |-- publish X threads ──────────────────────────────────────> X API
     |                   |-- schedule LinkedIn ──────────────────────────────────────> LinkedIn
     |                   |-- activate email drip ─────────────────────────────────── > Resend
     |<── {launch_report, post_urls}             |                    |                    |
```

### 5.8 Pillar 7 — LLMOps Weekly Optimization Cycle

```
Step Functions          LLMOps Agent        LangSmith          Prompt Optimizer     Model Router
  (weekly trigger)           |                   |                    |                  |
       |                     |                   |                    |                  |
       |-- invoke() -------> |                   |                    |                  |
       |                     |-- fetch_traces(last_7d) ──────────────>|                  |
       |                     |<── {traces, eval_scores, acceptance_rates} ──────────── |  |
       |                     |                   |                    |                  |
       |                     |-- drift_monitor.check()                |                  |
       |                     |   (LangSmith evals)                    |                  |
       |                     |   [if drift detected → alert]          |                  |
       |                     |                   |                    |                  |
       |                     |-- prompt_optimizer.run(DSPy) ──────────────────────────> |
       |                     |   (bootstrap few-shot from RLHF data)  |                  |
       |                     |   (Promptfoo regression suite gates)   |                  |
       |                     |<── {new_prompt_versions, eval_deltas}  |                  |
       |                     |                   |                    |                  |
       |                     |   [if eval_delta > +2% AND no regression]                |
       |                     |-- prompt_registry.promote(name, version, "canary")       |
       |                     |                   |                    |                  |
       |                     |-- model_router.update_rules() ─────────────────────────> |
       |                     |   (update cost/quality routing weights) |                  |
       |                     |                   |                    |                  |
       |                     |-- cost_report.generate()               |                  |
       |                     |   (per-tenant attribution, FinOps insights)               |
       |                     |-- emit llmops.cycle_completed ─────────> EventBridge      |
       |<── {cycle_report}   |                   |                    |                  |
```

### 5.9 JWT Auth & Tenant Resolution

```
Request               JWT Guard           Supabase Auth        OPA Engine            UDAL
  |                       |                    |                     |                  |
  |-- Authorization: Bearer <token> ─────────>|                     |                  |
  |                       |-- JWT.verify() --->|                     |                  |
  |                       |<── {valid, claims} |                     |                  |
  |                       |                    |                     |                  |
  |                       |   claims: {sub, tenant_id, role, scopes, exp}               |
  |                       |                    |                     |                  |
  |                       |-- OPA.check({input: {tenant_id, role,  ->|                  |
  |                       |              scopes, resource, action}}) |                  |
  |                       |<── {allow: true/false, reason} ─────── |                  |
  |                       |                    |                     |                  |
  |                       |   [if allow=false → 403]                 |                  |
  |                       |                    |                     |                  |
  |                       |-- inject TenantContext into request       |                  |
  |                       |   (available to all downstream handlers) |                  |
  |                       |                    |                     |                  |
  |   [downstream service calls UDAL]          |                     |                  |
  |                       |                    |                     |-- UDAL resolves  |
  |                       |                    |                     |  tenant_id from  |
  |                       |                    |                     |  TenantContext   |
  |                       |                    |                     |-- routes to      |
  |                       |                    |                     |  schema tenant_X |
```

### 5.10 RAG Pipeline (Detailed)

```
Agent                Query Rewriter        Retriever            Reranker          LLM              Output Guard
  |                       |                    |                    |               |                   |
  |-- rag.query(text, collection) ─────────>  |                    |               |                   |
  |                       |-- llm.rewrite()   |                    |               |                   |
  |                       |   (expand, clarify, add context)        |               |                   |
  |                       |<── {rewritten_query, sub_queries[]}    |               |                   |
  |                       |                    |                    |               |                   |
  |                       |-- retriever.search(rewritten_query) --->|               |                   |
  |                       |   BM25 lexical search (Mongo Atlas)     |               |                   |
  |                       |   + ANN dense search (cosine, top_k=20) |               |                   |
  |                       |   merge + deduplicate                   |               |                   |
  |                       |<── {candidates: [{doc, bm25_score,      |               |                   |
  |                       |                   dense_score}]}        |               |                   |
  |                       |                    |                    |               |                   |
  |                       |-- reranker.score(query, candidates) ─────────────────> |                   |
  |                       |   (Cohere Rerank or BGE cross-encoder)  |               |                   |
  |                       |<── {top_5_docs with cross_scores} ────────────────── |                   |
  |                       |                    |                    |               |                   |
  |                       |-- compress_context(top_5_docs) (LLM context compression)|               |
  |                       |<── {compressed_context, citation_map}   |               |                   |
  |                       |                    |                    |               |                   |
  |                       |-- llm.complete(prompt + compressed_context) ─────────> |                   |
  |                       |<── {answer}                             |               |                   |
  |                       |                    |                    |               |                   |
  |                       |-- output_guard.check_citations(answer, citation_map) ─────────────────────>|
  |                       |   (every factual claim must have a source doc)         |                   |
  |                       |<── {verified_answer, citation_ids} ────────────────────────────────────  |
  |                       |                    |                    |               |                   |
  |                       |-- langsmith.log(query, docs, answer, citation_scores)  |                   |
  |<── {answer, citations} |                   |                    |               |                   |
```

### 5.11 Guardrails Pipeline (per agent invocation)

```
Agent Call           Stage 1 Policy       Stage 2 Input        Stage 3 Instruction  Stage 4 Execution
    |                   (OPA)               (Llama Guard)           (validators)        (tool router)
    |-- run_input(text) |                    |                         |                   |
    |                   |-- OPA.check()     |                         |                   |
    |                   |   {tenant, agent, |                         |                   |
    |                   |    action, scopes}|                         |                   |
    |                   |<── {allow:true}   |                         |                   |
    |                   |                   |-- presidio.redact_pii() |                   |
    |                   |                   |-- llama_guard.classify()|                   |
    |                   |                   |   (safe / unsafe categories)                |
    |                   |                   |<── {safe:true, clean_text}                  |
    |                   |                   |                         |                   |
    |                   |                   |                         |-- validate_system_prompt()
    |                   |                   |                         |-- check_constraints()
    |                   |                   |                         |<── {passed:true}  |
    |<── (clean_input)  |                   |                         |                   |
    |                                                                                     |
    |-- run_execution(tool_name, args)                                                   |
    |                   |-- OPA.check({tool, agent, scope}) ─────────> Stage 4           |
    |                   |                                              |-- schema_validate(args)
    |                   |                                              |-- check_allow_list(tool)
    |                   |                                              |-- check_rate_limit(tenant, tool)
    |                   |                                              |-- check_cost_cap(run_id)
    |                   |                                              |<── {allow:true, clean_args}
    |<── (clean_args)   |                                              |                   |
    |                                                                                     |
    |   [LLM call happens here]
    |
    |-- run_output(llm_response)     Stage 5 Output (TruLens + Llama Guard + citation)
    |                                  |-- truelens.check_groundedness()
    |                                  |-- llama_guard.classify(output)
    |                                  |-- [Marketing only] feature_list_crossref()
    |                                  |-- toxicity_check()
    |<── (verified_output)           |
    |                                                  Stage 6 (async, non-blocking)
    |-- run_monitoring(trace) ──────────────────────────────────────────────────────────>
    |   (Evidently AI anomaly, PostHog abuse, cost regression)
    |-- audit_log.write(ctx, result)  [immutable, every stage]
```

---

## 6. Service-Level Component Breakdown

### 6.1 `apps/api` — FastAPI API Gateway

**Responsibilities**: JWT validation (Supabase Auth), tenant resolution, rate-limiting, OPA policy check, request routing to Orchestrator via gRPC. Realtime streaming handled by Supabase Realtime.

**Internal modules**:

| Router | Key functions | Deps |
|---|---|---|
| `auth/jwt.py` | `verify_token()`, `get_tenant_context()` | Supabase JWT, OPA sidecar |
| `routers/ideas.py` | `POST /v1/ideas` | Orchestrator gRPC client, Guardrails Stage 1 |
| `routers/runs.py` | `GET /v1/runs/{id}`, artifacts | UDAL (read-only), Orchestrator gRPC |
| `routers/gates.py` | `POST /v1/runs/{id}/gates/{gate_id}` | Orchestrator gRPC |
| `routers/llmops.py` | `GET /v1/llmops/cost` | UDAL (cost_ledger) |
| `routers/feedback.py` | `POST /v1/feedback` | Kafka producer (→ LLMOps topic) |
| `health.py` | `GET /health`, `/ready` | Supabase ping, Redis ping, Orchestrator gRPC ping |

**Rate limiting**: `slowapi` backed by Redis; per-tenant sliding window (1 min). Limits by tier: Solo=10/min, Startup=60/min, Enterprise=unlimited.

**Error response format**:
```json
{
  "statusCode": 400,
  "error": "ValidationError",
  "message": "idea_text must be at least 10 characters",
  "requestId": "<uuid>",
  "timestamp": "ISO 8601"
}
```

### 6.2 `apps/orchestrator` — LangGraph Engine

**Responsibilities**: Build and execute the per-run LangGraph StateGraph, manage checkpoints, handle HITL gate state machine, dispatch steps to AI Services, publish events.

**LangGraph state (`RunState` TypedDict)**:
```python
class RunState(TypedDict):
    run_id:          str
    tenant_id:       str
    pillar:          str
    idea_text:       str
    idea_meta:       dict
    plan:            dict              # serialized PlanDAG
    current_step:    str | None
    step_outputs:    dict[str, Any]   # step_id → output
    artifacts:       list[dict]
    active_gate:     dict | None
    retry_count:     int
    cost_usd:        float
    error:           str | None
```

**Node naming convention**: `{pillar}_{agent}_{action}` — e.g. `p1_strategy_understand`, `p2_architect_design`, `p4_reviewer_self_heal_1`.

**Checkpoint strategy**: After every node completion, state is checkpointed to:
1. Redis (`orch:checkpoint:{run_id}`) — hot restore (< 1ms)
2. PostgreSQL `orchestrator.checkpoints` — durable (crash-safe)

Resumption on failure: LangGraph's `interrupt_after` + Redis hot-restore within 30s; fall back to Postgres if Redis miss.

### 6.3 `apps/ai-services` — FastAPI Agent Workers

**Responsibilities**: Host agent execution workers, LLM clients, RAG pipeline, sandbox launcher. Receives steps from Orchestrator via gRPC streaming.

**Startup**: On boot, each worker registers itself in Redis (`workers:{agent_class}:{instance_id}`) with a 30s TTL; heartbeat refreshes every 10s. Orchestrator router skips stale workers.

**Worker concurrency**: Each Fargate task runs a single `asyncio` event loop; multiple tasks per ECS service. Each task handles one step at a time (no cross-step state in memory).

**LLM client (`llm/router.py`)**:
```python
class ModelRouter:
    def route(self, task_class: str, tenant_id: str) -> str:
        """
        Returns model_id for the given task class.
        Checks: A/B bucket assignment, cost cap headroom, model health.
        Falls back to previous tier if primary unavailable.
        """
        ...
    
    async def complete(
        self,
        model_id: str,
        messages: list[dict],
        tools: list[dict] | None,
        max_tokens: int,
    ) -> CompletionResult:
        """
        Wraps LiteLLM. Injects traceparent header.
        Checks semantic cache before calling API.
        Records token usage to cost_ledger.
        """
        ...
```

### 6.4 Supabase Realtime — WebSocket Fan-out (Managed)

**Responsibilities**: Accept WebSocket connections from the Founder Portal, fan out step events to the correct channel for a given `run_id`. This is a **managed service** — no `apps/realtime` app service is deployed.

**How it works**:
- Orchestrator writes step events to the `step_events` table in Supabase (PostgreSQL NOTIFY via `pg_notify`).
- Supabase Realtime listens on PostgreSQL replication and broadcasts row-level changes to subscribed clients.
- The Founder Portal subscribes via the Supabase JS client:
```javascript
supabase
  .channel(`run:${runId}`)
  .on('postgres_changes', { event: 'INSERT', schema: 'tenant_x', table: 'step_events', filter: `run_id=eq.${runId}` }, handleEvent)
  .subscribe()
```

**Backpressure**: Supabase Realtime handles backpressure internally. Portal replays missed events by querying `step_events` table on reconnect.

### 6.5 `apps/web` — Next.js Founder Portal

**Key patterns**:

- **`useRun(runId)` hook**: React Query for initial fetch + WebSocket for incremental updates. Merges WS events into React Query cache using `queryClient.setQueryData` with optimistic reconciliation.
- **Gate surface**: `useGate(gateId)` polls `/v1/runs/{id}/gates/{gateId}` every 5s when state=pending; renders gate-specific UI (e.g. `<LeanCanvasReview />`, `<ArchitectureReview />`).
- **Monaco diff viewer**: displays Reviewer Agent's code patches side-by-side with original; founder can comment before approving.
- **Auth**: Supabase Auth (`@supabase/ssr`); session stored in HttpOnly cookie; `tenant_id` extracted from Supabase JWT on every API call.
- **Error boundary**: per-surface React error boundary; Sentry `captureException` on unhandled errors.

### 6.6 `packages/db` — UDAL

**Invariant**: no code outside this package may import `pg`, `pymongo`, `neo4j`, `boto3.s3`, or `ioredis` directly.

**UDAL request lifecycle** (Python primary; TypeScript client for frontend read-only queries):
```
1. Extract tenant_id from AsyncLocalStorage (set by AuthMiddleware)
2. Validate tenant_id present (throws UDALError.NoTenantContext if missing)
3. Determine schema: "platform" for platform tables, "tenant_{id}" for tenant tables
4. Execute query with schema search_path or collection namespace
5. Emit lineage event to audit_log
6. Return result
```

**Python UDAL** mirrors the same lifecycle using `contextvars.ContextVar` for tenant propagation across async tasks.

### 6.7 `packages/agents` — Agent Implementations

**All agents extend `BaseAgent`**. Key overrides per agent:

| Agent | `understand` | `plan` | `execute` | `verify` |
|---|---|---|---|---|
| `StrategyAgent` | Parse idea + attachments; extract market intent | TAM/SAM/SOM → Competitor → Canvas → Viability DAG | Parallelises research tools; assembles canvas | LLM-as-judge on canvas completeness |
| `ResearchAgent` | Identifies research dimensions from strategy intent | Sequential: primary sources → secondary → synthesis | Tool fan-out (Tavily, SerpAPI, Crunchbase) | Citation groundedness check |
| `ArchitectAgent` | Extract FRs/NFRs from PRD | ERD → API Contract → Stack → Cost Forecast DAG | Generates ERD JSON, OpenAPI YAML, Mermaid diagrams | Schema validation + cost sanity check |
| `CoderAgent` | Parse arch spec → code tasks | FE ∥ BE ∥ DB parallel branches | LLM code gen per file, lint/typecheck in-loop | ESLint + mypy clean check |
| `ReviewerAgent` | Parse failing tests + lint output | Static → Unit → Integration → Security → Judge DAG | Run tests in sandbox, call self-healer on failures | Coverage ≥ 80% + judge ≥ 0.85 |
| `DevOpsAgent` | Parse arch + repo → infra requirements | Dockerfile → Terraform → ECS → DNS DAG | terraform apply + smoke test | HTTP 200 + latency < 2s |
| `MarketingAgent` | Extract brand/audience from strategy output | Brand → Page → SEO → Email → Social DAG | Parallel content gen; hallucination check per asset | Feature-list cross-reference |

### 6.8 `packages/guardrails`

**Stage 1 OPA call** (`stages/policy.py`):
```python
# OPA input shape
{
  "tenant_id": "...",
  "agent_id": "...",
  "action": "invoke_agent"|"call_tool"|"write_artifact",
  "resource": {"type": "...", "id": "..."},
  "context": {"tier": "startup", "cost_so_far": 0.42}
}
# OPA policy file: packages/guardrails/opa/policies/agent_policy.rego
```

**Stage 5 output guardrail — Marketing Agent special case**:
Every marketing asset goes through `feature_list_crossref()`:
- Extracts all factual claims (product capabilities, metrics) from the asset text via LLM extraction prompt.
- For each claim, checks if it appears in `architect_output.feature_list`.
- Claims without a matching feature are flagged; agent is asked to revise (up to 3 strikes).

**Audit log writes** are synchronous and happen after every stage regardless of outcome. The audit record is written by `audit.py` directly to PostgreSQL `platform.audit_log`, then asynchronously exported to S3 Object Lock by a nightly Lambda.

### 6.9 `packages/tools` — MCP Tool Registry

**Tool call lifecycle**:
```
1. Agent calls tool_registry.get("tavily.search")
2. UDAL.relational(platform, tool_registry, select, {name: "tavily.search"}) → ToolSpec
3. Execution Guard validates:
   a. Schema: args match args_schema (jsonschema.validate)
   b. Allow-list: tool in agent's declared tools list
   c. Rate limit: INCR + TTL on Redis ratelimit key
   d. Cost cap: run cost_so_far + estimated_tool_cost < tenant cap
4. Tool executes in Fargate task (strict egress to specific external IP)
5. Result returned; tool.call record appended to step_events
6. On failure: typed ToolError raised, caught by BaseAgent.execute()
             → re-plan via reflection or escalate
```

**Egress allow-list** (managed in Terraform Security Group egress rules):
- Research tools: Tavily API IP ranges, SerpAPI, Crunchbase
- Social tools: Twitter API, LinkedIn API, Reddit API
- Deploy tools: GitHub API, AWS service endpoints only
- All other outbound: denied

### 6.10 `packages/prompts` — Prompt Registry

**Jinja2 template rendering** with strict variable validation:
```python
# Before rendering, validator checks:
# 1. All `{{ required_var }}` are present in variables dict
# 2. No extra variables provided (strict mode)
# 3. Template renders without errors in a sandboxed Jinja2 env
#    (no exec, no import, autoescape=True for HTML contexts)

# Anti-pattern (forbidden by semgrep rule):
# prompt = f"Analyze {user_input}"  # ← direct string concat, blocked

# Correct:
# template = prompt_registry.get("strategy.market_sizing.v3", tenant_id, vars)
```

**Canary traffic split**: LLMOps Agent assigns tenants to A/B buckets using a deterministic hash: `bucket = hash(tenant_id + experiment_id) % 100`. If `bucket < canary_pct` (default 5), the canary prompt version is served.

---

## 7. Key Design Decisions & Trade-offs

### 7.1 LangGraph over plain task queue

| Aspect | LangGraph | Plain SQS task queue |
|---|---|---|
| Conditional branching | First-class (edge conditions) | Manual routing logic |
| Checkpoint / resume | Built-in (Postgres + Redis) | Must implement manually |
| HITL gates | Native `interrupt_after` | Polling + state machine in app code |
| Observability | Built-in trace nodes | Manual span injection |
| Complexity | Higher initial setup | Simpler, less opinionated |

**Decision**: LangGraph for its deterministic checkpointing and native HITL — critical when a run can span days and must survive restarts. AutoGen kept as fallback for ad-hoc multi-agent reasoning patterns (e.g., self-critique loops).

### 7.2 Schema-per-tenant vs row-level security only

| Aspect | Schema-per-tenant | Shared schema + RLS |
|---|---|---|
| Isolation guarantee | Physical; DDL separation | Logical; policy-enforced |
| Cross-tenant query risk | Zero (different schemas) | RLS bug = data leak |
| Migration complexity | Run per tenant (parallelisable) | Single migration, simpler |
| Postgres connection limit | PgBouncer per schema increases count | Fewer connections |
| Right to erasure | `DROP SCHEMA tenant_X CASCADE` | Partial deletes, complex |

**Decision**: Schema-per-tenant as the primary isolation mechanism. RLS added as defense-in-depth only. UDAL enforces `search_path` at query time — not configurable by callers. GDPR erasure becomes a clean `DROP SCHEMA`.

### 7.3 UDAL as mandatory data access layer

**Trade-off**: adds one indirection hop (~0.1ms) and a code convention to enforce.  
**Why it's worth it**: Without UDAL, a single misplaced `db.query("SELECT * FROM runs WHERE ...")` without a `tenant_id` filter leaks cross-tenant data. UDAL makes the unsafe operation structurally impossible. The audit lineage benefit (every data access is logged) is a requirement for SOC 2 Type II evidence.

### 7.4 Cheapest-capable model routing (LiteLLM)

The model router runs a rule table evaluated left-to-right:

```
task_class == "complex_reasoning"                              → gemini-1.5-flash-002
task_class == "code_gen"                                       → gemini-1.5-flash-002
task_class == "classification"                                 → gemini-1.5-flash-002
task_class == "embedding"                                      → gemini-embedding-002
task_class == "image_gen"                                      → dall-e-3
task_class == "speech"                                         → whisper-1
task_class == "safety_classifier"                              → llama-guard-3
```

**Risk**: routing to a cheaper model may degrade quality. Mitigation: LLM-as-judge score checked on output; if score < threshold, re-route to the next tier and increment `retry_count`.

### 7.5 Max 5 self-heal retries in Pillar 4

**Reasoning**: empirical — 90%+ of generated code errors are fixed within 3 cycles (syntax, logic, test mock). Cycles 4–5 catch edge cases. Beyond 5: the LLM is likely stuck in a local minimum; human review yields better ROI than further automated attempts.

**Implementation**: `self_heal_cycle` counter stored in `RunState.step_outputs`. On cycle 5 failure: insert `escalation` gate, pause run, emit `gate.required` to portal.

### 7.6 Supabase Realtime over custom WebSocket service

Supabase Realtime provides PostgreSQL-native change data capture broadcast over WebSocket. This eliminates the Go service (~400 LoC) and a separate SQS realtime-events queue. The trade-off is coupling the real-time layer to Supabase; mitigated by the fact that Supabase is already the primary data store. Portal reconnection and event replay are handled by the Supabase JS client and `step_events` table query on reconnect.

### 7.7 Supabase pgvector as primary vector store

**Decision factors**: pgvector runs inside the same Supabase PostgreSQL instance — no separate vector DB deployment, no cross-service network calls. HNSW indexing in pgvector provides recall@10 ~95% on 768-dim gemini-embedding-2 vectors, sufficient for RAG use cases. Schema-per-tenant isolation carries through naturally (each tenant schema has its own vector tables). UDAL vector calls become simple parameterized SQL — no MongoDB driver.

**Risk**: pgvector query latency is higher than dedicated vector DBs at very large scale (>10M vectors). Mitigated by: embedding cache (Redis), reranker compensating for recall gap, and horizontal Supabase read replicas if needed.

### 7.8 Jinja2 over f-strings for prompts

All prompts are Jinja2 templates stored in the prompt registry, never Python f-strings or string concatenation. Reasons:
- Prevents accidental prompt injection via `{user_input}` with unescaped braces.
- Enables version-controlled prompt artifacts (S3-immutable).
- Strict variable validation prevents silently missing context.
- Allows DSPy/Promptfoo to diff and optimize templates independently of code.

---

## 8. Dependency Matrix

```
Service / Package          Direct Dependencies
─────────────────────────────────────────────────────────────────────────────
apps/api                   packages/shared, packages/db (Python + TS read-only)
                           Supabase Auth (JWT) (external)
                           OPA sidecar (gRPC localhost:8181)
                           apps/orchestrator (gRPC)
                           Kafka producer (feedback topic publish)

apps/orchestrator          packages/shared, packages/db (Python)
                           apps/ai-services (gRPC)
                           Amazon EventBridge (publish)
                           Amazon SQS (pillar queues — consume + publish)
                           Redis (checkpoint hot cache)
                           PostgreSQL (checkpoint durable, runs, gates CRUD)

apps/ai-services           packages/agents, packages/guardrails
                           packages/tools, packages/prompts
                           packages/db (Python)
                           Google AI API (Gemini)
                           Supabase (pgvector + Storage)
                           Amazon ECR (sandbox image pull)
                           Amazon ECS (sandbox task launch)
                           Amazon EventBridge (publish traces)

apps/web                   apps/api (REST)
                           Supabase JS client (Realtime + Auth)
                           Sentry browser SDK

packages/agents            packages/db (Python), packages/tools
                           packages/prompts, packages/guardrails
                           packages/shared

packages/guardrails        OPA (HTTP policy evaluation)
                           Llama Guard 3 (Bedrock or self-hosted)
                           Microsoft Presidio (PII)
                           TruLens (output eval)
                           PostgreSQL (audit_log — via UDAL)

packages/db                Supabase PostgreSQL (pgvector + Storage)
                           Redis (ElastiCache)
                           Neo4j / Amazon Neptune
                           Amazon S3 (data lake / audit)

packages/tools             External tool APIs (scoped egress per tool)
                           packages/db (tool_registry read via UDAL)

packages/prompts           PostgreSQL (prompt_registry via UDAL)
                           Amazon S3 (template artifacts)

infra/terraform            AWS provider (~30 resources)
```

**Circular dependency rule**: `packages/db` must not import `packages/agents`, `packages/guardrails`, or `packages/tools`. Enforced by `depcheck`/`pylint` in CI.

---

## 9. Error Handling Specifications

### 9.1 Typed error hierarchy (Python)

```python
class AutoFounderError(Exception):
    """Base for all platform errors."""
    code: str
    retryable: bool = False

class UDALError(AutoFounderError):
    class NoTenantContext(UDALError):
        code = "UDAL_NO_TENANT_CONTEXT"
    class CrossTenantAccess(UDALError):
        code = "UDAL_CROSS_TENANT_ACCESS"  # SEV-1 alert

class GuardrailError(AutoFounderError):
    class Blocked(GuardrailError):
        code = "GUARDRAIL_BLOCKED"
        retryable = False
    class PIIDetected(GuardrailError):
        code = "GUARDRAIL_PII_DETECTED"
        retryable = False  # human review required

class ToolError(AutoFounderError):
    class RateLimit(ToolError):
        code = "TOOL_RATE_LIMIT"
        retryable = True
    class Auth(ToolError):
        code = "TOOL_AUTH_FAILURE"
        retryable = False
    class Schema(ToolError):
        code = "TOOL_SCHEMA_INVALID"
        retryable = False
    class Timeout(ToolError):
        code = "TOOL_TIMEOUT"
        retryable = True

class LLMError(AutoFounderError):
    class RateLimit(LLMError):
        code = "LLM_RATE_LIMIT"
        retryable = True
    class ContextTooLong(LLMError):
        code = "LLM_CONTEXT_TOO_LONG"
        retryable = False  # needs context compression
    class ProviderError(LLMError):
        code = "LLM_PROVIDER_5XX"
        retryable = True

class MaxRetriesExceeded(AutoFounderError):
    code = "MAX_RETRIES_EXCEEDED"
    retryable = False  # triggers HITL escalation
```

### 9.2 Retry backoff parameters

| Error type | Max retries | Initial backoff | Multiplier | Cap |
|---|---|---|---|---|
| `LLMError.RateLimit` | 5 | 2s | 2× | 60s |
| `LLMError.ProviderError` | 3 | 5s | 2× | 30s |
| `ToolError.RateLimit` | 3 | 1s | 2× | 30s |
| `ToolError.Timeout` | 2 | 3s | 1.5× | 10s |
| SQS message visibility | — | 30s | — | 900s (DLQ after 5 nacks) |
| Self-heal cycle (Pillar 4) | 5 | 0s | 0× | — (immediate retry with patch) |

All retries add ±20% jitter to the backoff value to prevent thundering-herd on shared LLM endpoints.

### 9.3 Circuit breaker configuration

Each external integration (Google AI, Tavily, GitHub, etc.) has a per-process circuit breaker:

```
State:     CLOSED → OPEN → HALF_OPEN → CLOSED
Open when: failure_rate > 50% over last 10 calls
           OR consecutive_failures >= 5
Half-open: allow 1 probe request every 30s
Close when: 2 consecutive successes in HALF_OPEN

On OPEN: raise CircuitOpenError (not retried; LLM router falls back to alternate provider)
```

### 9.4 SEV classification

| SEV | Condition | Response |
|---|---|---|
| SEV-1 | `UDALError.CrossTenantAccess` | PagerDuty immediate; auto-pause affected tenant; security team notified |
| SEV-1 | Audit log write failure | PagerDuty immediate; block all writes until resolved |
| SEV-2 | > 10% of runs failing in 5 min | PagerDuty within 5 min; on-call investigates |
| SEV-3 | Single run stuck > SLA | Async alert; LLMOps drift detection flags for review |
| SEV-4 | Prompt eval regression | LLMOps ticket created; next weekly cycle re-evaluates |

---

## 10. Configuration & Environment Variables

All non-secret config lives in AWS SSM Parameter Store (`/{env}/autofounder/{service}/{key}`).  
All secrets live in AWS Secrets Manager (`/{env}/autofounder/{service}/{secret_name}`).  
**No `.env` files in the repository** (enforced by Gitleaks + semgrep rule `no-dotenv-in-repo`).

### 10.1 `apps/api` (FastAPI)

| Variable | Source | Example |
|---|---|---|
| `SUPABASE_URL` | SSM | `https://<project>.supabase.co` |
| `SUPABASE_JWT_SECRET` | Secrets Mgr | `<supabase-jwt-secret>` |
| `OPA_ENDPOINT` | SSM | `http://localhost:8181` |
| `ORCHESTRATOR_GRPC_HOST` | SSM | `orchestrator.internal:50051` |
| `REDIS_URL` | Secrets Mgr | `rediss://...` |
| `THROTTLE_TTL` | SSM | `60` |
| `THROTTLE_LIMIT_SOLO` | SSM | `10` |
| `SENTRY_DSN` | Secrets Mgr | `https://...@sentry.io/...` |

### 10.2 `apps/orchestrator` (Python)

| Variable | Source | Example |
|---|---|---|
| `DATABASE_URL` | Secrets Mgr | `postgresql+asyncpg://...` |
| `REDIS_URL` | Secrets Mgr | `rediss://...` |
| `EVENTBRIDGE_BUS_NAME` | SSM | `autofounder-platform-prod` |
| `SQS_PILLAR_QUEUES` | SSM | `{"1": "...", "2": "...", ...}` (JSON) |
| `AI_SERVICES_GRPC_HOST` | SSM | `ai-services.internal:50052` |
| `LANGSMITH_API_KEY` | Secrets Mgr | `lsv2_...` |
| `LANGSMITH_PROJECT` | SSM | `autofounder-prod` |

### 10.3 `apps/ai-services` (Python)

| Variable | Source | Example |
|---|---|---|
| `GOOGLE_AI_API_KEY` | Secrets Mgr | `AIza...` |
| `SUPABASE_URL` | SSM | `https://<project>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Secrets Mgr | `<supabase-service-role-key>` |
| `S3_ARTIFACTS_BUCKET` | SSM | `autofounder-artifacts-prod` |
| `ECS_CLUSTER_ARN` | SSM | `arn:aws:ecs:ap-south-1:...` |
| `ECS_SANDBOX_TASK_DEF` | SSM | `autofounder-sandbox:12` |
| `TAVILY_API_KEY` | Secrets Mgr | `tvly-...` |
| `SERPAPI_KEY` | Secrets Mgr | `...` |
| `MODEL_ROUTING_CONFIG` | SSM | JSON routing table (see §7.4) |
| `COST_CAP_SOLO_USD` | SSM | `25` |
| `COST_CAP_STARTUP_USD` | SSM | `200` |

### 10.4 Supabase Realtime (Managed — no env config required)

Supabase Realtime is configured via the Supabase project dashboard and inherits the project's JWT secret. No separate service deployment or environment variables are needed beyond `SUPABASE_URL` and `SUPABASE_ANON_KEY` (already in `apps/web`).

### 10.5 Feature flags (GrowthBook / Statsig)

| Flag | Default | Used by |
|---|---|---|
| `enable_autogen_fallback` | `false` | Orchestrator |
| `marketing_hallucination_strict` | `true` | Guardrails Stage 5 |
| `canary_prompt_pct` | `5` | Prompt Registry |
| `enable_neo4j_graph` | `false` (pending benchmark) | UDAL graph layer |
| `devops_spend_gate_threshold_usd` | `50` | Gates (Pillar 5) |
| `llmops_cycle_day` | `"sunday"` | Step Functions schedule |

---

*Generated from CLAUDE.md v1.0 — 2026-05-19*  
*Companion document: `docs/HLD.md`*
