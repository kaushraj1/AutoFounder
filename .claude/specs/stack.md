# Tech Stack Spec — AutoFounder AI

> Decisions made, the reasoning behind them, and the constraints they impose.
> Update this file when a decision changes — record the old choice and why it changed.

---

## Backend

### Language — Python 3.12

**Why**: The entire agent/ML ecosystem (LangGraph, LangChain, LlamaIndex, DSPy, TruLens,
Evidently, Promptfoo bindings) is Python-native. Calling these from any other language
requires subprocess bridging or HTTP round-trips, both of which add latency and operational
complexity on the hot agent execution path.

**Constraints**:
- All public functions must have type hints. `mypy` (or Pyright) runs in CI.
- Python version is pinned in `pyproject.toml` (`requires-python = ">=3.12"`). Do not widen without a team decision.

### Framework — FastAPI

**Why**: Async-native (ASGI), Pydantic v2 request/response validation built in, OpenAPI 3.1
spec auto-generated from code, excellent integration with `asyncio`-based agent executors.

**Constraints**:
- Every route is `async def`. Sync blocking calls (file I/O, heavy CPU) go into `asyncio.to_thread`.
- Pydantic models use `model_config = ConfigDict(strict=True)` — no implicit coercion.
- OpenAPI spec (`openapi.yaml`) stays in sync. CI lints the spec against route definitions.

### Package Manager — uv

**Why**: Drops pip + venv + pip-tools into a single binary. Deterministic lockfile (`uv.lock`).
10–100× faster than pip. Integrates with `pyproject.toml` — no separate `requirements.txt`.

**Commands**:
```bash
uv sync --all-groups       # install all deps including dev
uv add <package>           # add runtime dep
uv add --dev <package>     # add dev dep
uv run pytest              # run in managed venv
```

### Linting & Formatting — Ruff

**Why**: Single binary replacing Flake8 + isort + pyupgrade + pydocstyle + Black. Same
line-length, same import sorting, zero config drift between tools.

**Config** (`pyproject.toml`):
- `line-length = 100`
- `select = ["E", "F", "I", "UP", "B"]` — errors, Pyflakes, isort, upgrades, bugbear
- CI fails on any lint or format violation. Auto-fix with `make backend-format`.

### LLM Orchestration — LangGraph

**Why**: Stateful DAGs with native HITL interrupt support, Postgres + Redis checkpointing out of the box,
and first-class streaming. The alternative (Celery task graphs) lacks native state, requires custom
checkpointing, and has no concept of human-in-the-loop pausing.

**Constraints**:
- Every `StateGraph` node must call `learn(trace)` at exit — traces feed LLMOps.
- Checkpoints are written to Postgres (`orchestrator.checkpoints`) AND Redis (hot cache).
- AutoGen is the fallback for free-form multi-agent chat steps only; LangGraph is the orchestrator for structured pillar execution.

---

## Frontend — Web

### Framework — React + TypeScript + Vite

**Why**: React for component model; Vite for fast HMR and native ESM dev server; TypeScript strict
mode catches prop/state bugs at build time.

**Constraints**:
- `"strict": true` in `tsconfig.json` — no implicit `any`.
- Components are named exports in PascalCase files.
- No default exports for components (makes refactoring and tree-shaking predictable).

### Styling — Tailwind CSS + shadcn/ui

**Why**: Tailwind eliminates dead CSS; shadcn/ui provides accessible, unstyled primitives that
compose into the design system without a runtime CSS-in-JS penalty.

**Constraints**:
- No inline `style={{}}` except for values computed at runtime (e.g. dynamic widths from data).
- No custom re-implementations of shadcn/ui primitives (Button, Input, Modal, etc.).
- Design tokens live in `tailwind.config.ts` — not hardcoded hex values in class names.

### State — React Query + Zustand

| Concern | Tool |
|---------|------|
| Server data (API responses, caching, refetch) | React Query |
| UI-only state (open/close, active tab, theme) | Zustand |
| Real-time updates (run logs, gate events) | WebSocket hook merged into React Query cache |

### Build Tool — Turborepo (monorepo orchestration)

**Why**: Turborepo caches task outputs across packages. `turbo lint` on a PR only re-lints packages
that changed. `turbo build` parallelises across `frontend-web`, `mobile-app`, `vscode-extension`.

---

## Mobile — Expo (React Native)

**Why**: Single TypeScript codebase compiles to iOS + Android. EAS Build provides managed cloud
builds without macOS CI runners for Android. EAS Submit automates App Store and Play Store delivery.
Expo modules (Camera, AV, Notifications, SecureStore) cover all AutoFounder AI mobile use cases.

**Constraints**:
- Expo SDK version is pinned. Do not upgrade mid-sprint.
- All secrets stored in `expo-secure-store` — never `AsyncStorage` for tokens.
- OTA updates (Expo Updates) for JS-only changes; new native modules require a full EAS build.

---

## VS Code Extension — TypeScript + VS Code API

**Why**: Direct VS Code extension API access (SecretStorage, TreeView, WebviewPanel, commands,
notifications). TypeScript gives type safety for the API surface.

**Constraints**:
- Activation events must be specific — not `onStartupFinished` for the whole extension.
- Long-running operations use `vscode.window.withProgress`.
- Auth tokens stored in `vscode.SecretStorage`, never `globalState`.

---

## Infrastructure

### Cloud — GCP + Terraform

**Why**: GCP's managed services (Cloud SQL, Memorystore, Cloud Run, Pub/Sub, Artifact Registry,
Secret Manager) map cleanly to every AutoFounder AI workload. Terraform provides provider-agnostic
IaC syntax and a mature GCP provider.

**Constraints**:
- No AWS or Azure SDKs. If a library hard-requires AWS, find a GCP alternative or wrap it.
- Every GCP resource is tagged with `env`, `project`, `managed-by = "terraform"`.
- Terraform state lives in a GCS backend bucket — never committed to git.

### Compute — Cloud Run (primary)

**Why**: Fully managed, scales to zero, supports HTTP/2 (gRPC), and handles container concurrency
natively. No cluster management overhead. Agent worker tasks that need ephemeral sandboxes use
Cloud Run Jobs (one-off invocations).

**Trade-off**: Cold start latency (~1–3 s) is acceptable for the agent pipeline; unacceptable for
the FastAPI gateway. The gateway service uses `min-instances = 1` to keep one warm instance.

### Databases — PostgreSQL 16 + Redis 7

**Why**:
- PostgreSQL: ACID, JSONB for plan DAGs, Alembic migrations, schema-per-tenant isolation, RLS.
- Redis: sub-millisecond cache, LangGraph checkpoint hot path, Pub/Sub for gate events, rate-limit counters.

**GCP services**: Cloud SQL (PostgreSQL 16, HA replica), Memorystore for Redis.

**Local dev**: Docker Compose (`make stack`) — same major versions as production.

### Monorepo — pnpm + Turborepo

**Workspace packages** (from `pnpm-workspace.yaml`):
- `frontend-web`
- `mobile-app`
- `vscode-extension`

Backend (`backend/`) is **not** a pnpm workspace — it is a Python project managed by `uv`.
Turborepo orchestrates JS/TS tasks only; backend tasks run via `Makefile`.

---

## Decisions Still Open

| Decision | Options | Blocker |
|----------|---------|---------|
| Vector store | Vertex AI Vector Search vs Pinecone vs MongoDB Atlas | GCP-native preference but cost model unclear |
| Graph DB | Neo4j AuraDB vs AlloyDB Graph vs self-managed | Benchmark needed |
| Primary LLM | Gemini (GCP-native, lower egress cost) vs Claude Sonnet vs GPT-4o | Eval results pending |
| Feature flags | GrowthBook (self-hosted) vs LaunchDarkly vs Statsig | Budget |
| GCP region | `asia-south1` (Mumbai) only vs multi-region from day one | Traffic distribution data needed |
