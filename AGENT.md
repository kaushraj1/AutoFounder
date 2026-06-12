# AutoFounder AI — Agent Reference Map

Welcome, Agent! This repository is organized as a modular monolith transitioning to microservices. To ensure consistency and safety, follow the rules and architecture definitions mapped below.

---

## 🏛️ Architecture & System Rules (Located in `.claude/`)

All core specifications, system rules, database designs, and development plans are stored in the [.claude](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/) directory.

### Core Specifications
* 📋 **[Product Requirements & Roadmap](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/specs/product.md):** Feature requirements and milestones.
* 🏗️ **[System Architecture](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/specs/architecture.md):** Overall system design, orchestration flow, and modules.
* 💾 **[Database Design](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/specs/database.md):** Database schemas, multi-tenant isolation layout, and Alembic practices.
* 📡 **[API Design](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/specs/api-design.md):** REST and WebSocket endpoints, JSON envelopes, and pagination cursors.
* 🤖 **[Agent Framework Spec](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/specs/agents.md):** Base agent contract, LLM routers, and tools.
* ⚙️ **[Operations & Observability](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/specs/operations.md):** Logs, metrics (Prometheus), and OpenTelemetry.
* 🔒 **[Governance & Security](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/specs/governance.md):** RLS policies, OPA, JWT, and compliance audits.

### Active Developer Plans
Individual task implementations and sprint checklists are located in the [developer-plans](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/developer-plans/) directory. Refer to these to check complete task details:
* 🎯 **[Pillar 1 Strategy & Research Plan](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/developer-plans/02-somesh-pillar-1-strategy-research-plan.md)**
* 🧱 **[Pillar 2 Architecture Plan](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/developer-plans/03-kaushlendra-pillar-2-architecture-plan.md)**
* 💻 **[Pillar 3 Code Generation Plan](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/developer-plans/04-kartik-pillar-3-codegen-plan.md)**
* 🛡️ **[Guardrails Pipeline Plan](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.claude/developer-plans/11-asit-guardrails-pipeline-plan.md)**

---

## 📂 Project Documentation (Located in `docs/`)

All general usage guidelines, user guides, setup scripts, and secondary documentation are located in the [docs](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/docs/) directory.
Refer to this folder for:
* Local development setup guides.
* Deployment runbooks.
* Package dependencies and integration tutorials.

---

## 🛠️ Key Coding & Directory Rules
* **Code Integrity:** Maintain existing comments, type hints, and docstrings.
* **Tenant Scoping:** All relational writes must go through the tenant-scoped Unified Data Access Layer (UDAL) using the session variable transaction scopes defined in [relational.py](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/backend/app/db/relational.py).
* **Secrets:** Never commit `.env` or credential files (which are ignored in [.gitignore](file:///Users/rishitasrivastava/somesh/PROJECT-1-AutoFounder-AI/.gitignore)).
