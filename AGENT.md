# AutoFounder AI — Agent Reference Map

Welcome, Agent! This repository is organized as a modular monolith transitioning to microservices. To ensure consistency and safety, follow the rules, architecture specs, and individual agent designs mapped below.

---

## 🏛️ System Rules, Checklists & Specs (Located in `.claude/`)

All core checklists, project build sequences, configuration variables, developer tasks, and architectural specification files are stored in the [`.claude/`](.claude/) directory.

### 📋 Core Context, Roadmaps & Status
* 📜 **[CLAUDE.md](.claude/CLAUDE.md):** Main developer/agent rules, CLI commands, stack overview, and development conventions.
* 🚦 **[CURRENT-STATUS.md](.claude/CURRENT-STATUS.md):** Current active development phase, completed features, and blocking/next items.
* 📋 **[PLAN-BUILD-SEQUENCE.md](.claude/PLAN-BUILD-SEQUENCE.md):** The step-by-step master sequence for building the 7 pillars of the platform.
* 💾 **[MEMORY.md](.claude/MEMORY.md):** Contextual memory patterns, RAG retrieval mechanics, and episodic memory guidelines for agents.
* 🛠️ **[SKILL.md](.claude/SKILL.md):** Defines standard agent skills, interfaces, and expected runtime behaviors.
* 📝 **[SUMMARY.md](.claude/SUMMARY.md):** High-level summary mapping the workspace directories and file organization.
* 📅 **[PLAN.md](.claude/PLAN.md):** The overall development plan and timeline for project phases.
* 🗓️ **[PLAN_PHASE.md](.claude/PLAN_PHASE.md):** Granular milestones and release goals for the active phase.
* 🗳️ **[TASKS.md](.claude/TASKS.md):** Central task checklist covering frontend, backend, infrastructure, and agent behaviors.
* 🏷️ **[task_assigned.md](.claude/task_assigned.md):** Assigns specific tasks to individual agent/developer roles with detailed instructions.
* ⚙️ **[settings.local.json](.claude/settings.local.json):** Local workspace configuration and tool behaviors for the development environment.

### 📡 Specification Manifests (Located in [`.claude/specs/`](.claude/specs/))
* 🏗️ **[Orchestrator Architecture (`architecture.md`)](.claude/specs/architecture.md):** Detailed design of the LangGraph engine, StateGraph transitions, HITL gates, and asynchronous checkpoints.
* 🤖 **[Base Agent System Rules (`agents.md`)](.claude/specs/agents.md):** Base agent contract, LLM API budgets, circuit breakers, self-healing loop count limits, and base prompts.
* 📡 **[API Design Spec (`api-design.md`)](.claude/specs/api-design.md):** REST and WebSocket endpoints, request/response envelopes, error states, and pagination specs.
* 💾 **[Database Spec (`database.md`)](.claude/specs/database.md):** Relational tables, Supabase schemas, pgvector details (HNSW indices), and multi-tenant RLS policies.
* 🔒 **[Governance Spec (`governance.md`)](.claude/specs/governance.md):** Security guardrails, OPA/Cedar policy queries, JWT validation, and input/output filters (Llama Guard 3).
* 🎛️ **[Operations Spec (`operations.md`)](.claude/specs/operations.md):** OpenTelemetry tracing/spans, LangSmith evaluation setups, Prometheus metrics, and cost accumulation logic.
* 📦 **[Deployment Spec (`deployment.md`)](.claude/specs/deployment.md):** Docker orchestration, Terraform variables, AWS ECS Fargate configurations, and SQS queue definitions.
* 💻 **[Tech Stack Spec (`stack.md`)](.claude/specs/stack.md):** Authoritative technologies used in backend (FastAPI, uv), frontend (Next.js 14), mobile, and databases.
* 🔌 **[Integrations Spec (`integrations.md`)](.claude/specs/integrations.md):** Third-party APIs, LLM provider settings (LiteLLM router), fallback schemes, and API keys.
* 📱 **[Mobile Spec (`mobile.md`)](.claude/specs/mobile.md):** Conventions and architecture rules for the React Native/Expo mobile app.
* 📈 **[Product Spec (`product.md`)](.claude/specs/product.md):** Business objectives, feature roadmap, pricing tiers, and risk matrices.
* ⚖️ **[Decisions Log (`decisions.md`)](.claude/specs/decisions.md):** Record of architecture reconciliations, design changes, and authoritative decisions.
* 🧪 **[Pillar 5 Mock Input (`pillar5-dummy-input.json`)](.claude/specs/pillar5-dummy-input.json):** Sample input JSON structure for testing DevOps and provisioning code.

---

## 🎯 Active Developer Plans (Located in [`.claude/developer-plans/`](.claude/developer-plans/))

Detailed feature plans, implementation tasks, and tracking indices for the team:
* 📇 **[00-INDEX.md](.claude/developer-plans/00-INDEX.md):** Index of all developer plans, assignments, status, and PR links.
* ⚙️ **[01-asit-platform-foundation-plan.md](.claude/developer-plans/01-asit-platform-foundation-plan.md):** Core workspace setup, Supabase connection, and base API structures.
* 🎯 **[02-somesh-pillar-1-strategy-research-plan.md](.claude/developer-plans/02-somesh-pillar-1-strategy-research-plan.md):** Strategy & Research Agent, Tavily searches, SWOT generation, and idea viability.
* 🧱 **[03-kaushlendra-pillar-2-architecture-plan.md](.claude/developer-plans/03-kaushlendra-pillar-2-architecture-plan.md):** System HLD/LLD creation, ERD mapping, and database migrations generation.
* 💻 **[04-kartik-pillar-3-codegen-plan.md](.claude/developer-plans/04-kartik-pillar-3-codegen-plan.md):** Code generation agents (FastAPI backend + Next.js frontend scaffolding).
* 🧪 **[05-vishal-pillar-4-testing-plan.md](.claude/developer-plans/05-vishal-pillar-4-testing-plan.md):** Automated self-healing tests, static checks, coverage checks, and LLM-as-judge code reviews.
* ☁️ **[06-prasenjit-pillar-5-deployment-plan.md](.claude/developer-plans/06-prasenjit-pillar-5-deployment-plan.md):** Terraform templates, ECS Fargate deployments, SSL setup, and domain registration.
* 📣 **[07-pallavi-pillar-6-marketing-plan.md](.claude/developer-plans/07-pallavi-pillar-6-marketing-plan.md):** Brand voice, landing pages, SEO blog generator, social schedulers, and launch kits.
* 📊 **[08-purnima-pillar-7-llmops-plan.md](.claude/developer-plans/08-purnima-pillar-7-llmops-plan.md):** Cost tracking, A/B model testing, evaluators, and automatic prompt optimization.
* 🖥️ **[09-raunak-web-frontend-plan.md](.claude/developer-plans/09-raunak-web-frontend-plan.md):** Founder dashboard portal layout, billing gates, and deployment monitors.
* 📱 **[10-yogesh-mobile-plan.md](.claude/developer-plans/10-yogesh-mobile-plan.md):** Expo application flow, notifications, and mobile monitoring screens.
* 🛡️ **[11-asit-guardrails-pipeline-plan.md](.claude/developer-plans/11-asit-guardrails-pipeline-plan.md):** Cedar/OPA policies execution, Llama Guard safety integration, and PII redaction pipeline.
* 🔌 **[12-asit-vscode-extension-plan.md](.claude/developer-plans/12-asit-vscode-extension-plan.md):** Code generation integration into VSCode IDE extensions.
* 💼 **[13-asit-finance-ops-risk-plan.md](.claude/developer-plans/13-asit-finance-ops-risk-plan.md):** Cost limits, billing limits, multi-tenant billing, and subscription gate configurations.

---

## 📂 System Design Specifications (Located in `docs/`)

Architectural designs, developer learning logs, and PRDs:
* 📜 **[learning-log.md](docs/learning-log.md):** General developer logging notes, troubleshooting guidelines, and lessons learned.

### High & Low Level Designs (Located in [`docs/architecture/`](docs/architecture/))
* 📐 **[HLD.md (High-Level Design)](docs/architecture/HLD.md):** Global platform boundaries, microservices communication schema, and deployment boundaries.
* 🔍 **[LLD.md (Low-Level Design)](docs/architecture/LLD.md):** Deep-dive specs on LangGraph execution steps, DB schemas, database access layer, and API contracts.
* 🏗️ **[architecture.md](docs/architecture/architecture.md):** Mermaid diagrams displaying system flow, database relationships, and 7-pillar step sequences.
* 📄 **[AutoFounder_AI_PRD.docx](docs/architecture/AutoFounder_AI_PRD.docx):** Word document containing the product requirements and business logic specifications.

### Individual Agent Specifications (Located in [`docs/architecture/Agents-Architecture/`](docs/architecture/Agents-Architecture/))
* 🎯 **[Strategist Agent Spec (`strategist-agent.md`)](docs/architecture/Agents-Architecture/strategist-agent.md):** Pillar 1 agent logic. Conducts research via APIs, performs competitor SWOT, generates business canvas, and yields final viability scores.
* 🧱 **[Architect Agent Spec (`architect-agent.md`)](docs/architecture/Agents-Architecture/architect-agent.md):** Pillar 2 agent logic. Translates PRD into microservices boundaries, visualizes ERDs, writes OpenAPI contracts, and defines DB models.
* 💻 **[Coder Agent Spec (`coder-agent.md`)](docs/architecture/Agents-Architecture/coder-agent.md):** Pillar 3 agent logic. Generates production-ready backend code (SQLAlchemy/FastAPI) and frontend pages (React/Next.js).
* 🛡️ **[Reviewer Agent Spec (`reviewer-agent.md`)](docs/architecture/Agents-Architecture/reviewer-agent.md):** Pillar 4 agent logic. Runs lint checks, validates types, writes unit/integration tests, and repairs broken code in a self-healing loop.
* ☁️ **[DevOps Agent Spec (`devops-agent.md`)](docs/architecture/Agents-Architecture/devops-agent.md):** Pillar 5 agent logic. Writes Dockerfiles, configures GitHub Actions pipelines, provisions cloud infra via Terraform, and manages DNS/SSL.
* 📣 **[Marketer Agent Spec (`marketer-agent.md`)](docs/architecture/Agents-Architecture/marketer-agent.md):** Pillar 6 agent logic. Creates marketing kits, writes SEO-optimized content, schedules launches, and drafts email campaigns.
* 📊 **[LLMOps Agent Spec (`llmops-agent.md`)](docs/architecture/Agents-Architecture/llmops-agent.md):** Pillar 7 agent logic. Tracks cost, schedules prompt tuning cycles, detects model drift, and updates model routing.
