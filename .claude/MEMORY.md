# AutoFounder AI — Claude Memory

> **AutoFounder AI** is a multi-tenant agentic AI SaaS that converts a single text idea into a
> fully validated, built, deployed, and marketed software business autonomously — cutting the
> traditional 4–7 month, $20–60K founder journey down to ~7 days at $200–700.

---

## Product Identity

| Field | Value |
|-------|-------|
| **Name** | AutoFounder AI |
| **Type** | Multi-tenant agentic AI SaaS |
| **Target users** | Solo founders, product managers, startup teams |
| **Core promise** | Idea → live MVP in ~7 days without a dev team |
| **Tiers** | Solopreneur (₹10k/mo · 1 build), Startup (₹50k/mo · 5 builds), Enterprise (custom) |
| **MVP scope** | Phase 1–3: Strategy agent + Architect agent + Coder agent → deployed MVP |
| **Out of scope (v1)** | Mobile app generation, HFT, regulated medical software |

**7-pillar pipeline**: Strategy & Ideation → Architecture → Code Gen → Testing & Self-Healing → Deploy → Marketing & Launch → LLMOps

HITL gates required at: Pillar 1 (validation), Pillar 2 (architecture), Pillar 5 (infra spend), Pillar 6 (launch).

---

## Tech Stack Decisions

### Backend
| Concern | Choice | Why |
|---------|--------|-----|
| Language | Python 3.12 | Agent/ML ecosystem, type hints enforced |
| Framework | FastAPI | Async-native, OpenAPI 3.1 auto-gen, fast iteration |
| Package manager | `uv` | Deterministic, fast, replaces pip + venv |
| Linting/format | Ruff + `ruff format` | Single tool replacing Flake8 + isort + Black |
| Orchestration | LangGraph | Stateful DAGs, native HITL gates, deterministic checkpoints |

### Frontend / Clients
| Concern | Choice | Why |
|---------|--------|-----|
| Web portal | React + TypeScript (Next.js 14 App Router) | SSR + RSC, Tailwind + shadcn/ui |
| Mobile | Expo (React Native) | Cross-platform iOS/Android, EAS Build pipeline |
| VS Code extension | TypeScript + VS Code API | In-editor HITL approvals + code gen commands |
| Monorepo | pnpm + Turborepo | Workspace caching, parallel task execution |

### Infrastructure
| Concern | Choice |
|---------|--------|
| Cloud | GCP + Terraform |
| Databases | PostgreSQL 16 (primary), Redis 7 (cache + queues) |
| Local dev | Docker Compose (Postgres + Redis) |
| Auth | Auth0 — OAuth 2.0 + SAML 2.0, MFA enforced |
| CI/CD | GitHub Actions → GCP Cloud Deploy |

---

## Directory Layout

```
autofounder-ai/
├── backend/               FastAPI service (Python 3.12, uv)
│   ├── src/autofounder-ai/   application source
│   ├── pyproject.toml        uv + Ruff config
│   └── Dockerfile
├── frontend-web/          Next.js 14 Founder Portal (pnpm workspace)
│   └── src/
├── mobile-app/            Expo React Native (pnpm workspace)
│   └── src/
├── vscode-extension/      VS Code Extension (pnpm workspace)
│   └── src/
├── infra/                 Terraform modules (GCP) — not yet created
├── docs/
│   └── architecture/      HLD.md · LLD.md · architecture.md
├── scripts/
│   ├── dev-setup.sh
│   └── dev-setup.ps1
├── .claude/
│   ├── MEMORY.md          ← this file
│   ├── TASKS.md
│   └── settings.local.json
├── docker-compose.yml     PostgreSQL 16 + Redis 7 (local dev only)
├── Makefile               canonical task runner
├── turbo.json             Turborepo pipeline config
├── pnpm-workspace.yaml
├── CLAUDE.md              full architecture reference
└── TASKS.md               phase-by-phase task tracker (AF-001 … AF-078)
```

---

## Key Commands

```bash
# One-time setup
make install          # pnpm install + uv sync --all-groups

# Local databases (PostgreSQL 16 + Redis 7)
make stack            # docker compose up -d
make stack-down       # docker compose down

# Run everything (Turborepo parallel)
make dev              # pnpm dev  →  turbo dev

# Quality gates (run before every PR)
make quality          # backend-lint + js-lint (must both pass)
make backend-lint     # uv run ruff check src + ruff format --check src
make backend-format   # uv run ruff format src + ruff check --fix src
make js-lint          # pnpm lint  →  turbo lint
make js-format        # pnpm format  →  prettier --write .

# Run backend tests (once test suite exists)
cd backend && uv run pytest

# Turbo tasks directly
pnpm dev              # all workspaces in parallel
pnpm lint             # all JS/TS workspaces
pnpm build            # production builds
```

---

## Branch Strategy

```
main          production-ready, protected — no direct push
  └── testing     integration + QA — merges to main via PR
        └── development   active development — feature branches merge here
```

- Feature branches: `feature/<task-id>-<kebab-description>` (e.g. `feature/AF-037-strategy-agent`)
- Hotfixes: `hotfix/<kebab-description>` → PR directly to `main` + back-merge to `development`
- All merges via PR; CI must pass (`make quality` + tests + security scan)

---

## Coding Conventions

> **To be filled by the team.** Placeholder entries below.

- [ ] API response envelope format (e.g. `{data, error, requestId}`)
- [ ] Error code naming scheme (`AF_ERR_*` vs HTTP status only)
- [ ] Async vs sync FastAPI route conventions
- [ ] Python type hint strictness level (`strict` mypy or `basic`)
- [ ] Component naming in React (PascalCase files, named exports)
- [ ] State management split: what lives in Zustand vs React Query vs local state
- [ ] Commit message format (Conventional Commits enforced by hook?)
- [ ] Test file colocation vs `tests/` directory

---

## Things Not Yet Decided

- [ ] GCP services mapping — Cloud Run vs GKE vs Cloud Functions per workload
- [ ] Vector store — managed option on GCP or hosted MongoDB Atlas / Pinecone
- [ ] Graph DB — Neo4j AuraDB or hosted alternative
- [ ] Primary LLM for agents — Gemini (GCP-native) vs Claude Sonnet vs GPT-4o
- [ ] Feature flag service — LaunchDarkly vs GrowthBook vs home-grown
- [ ] Multi-region strategy — single GCP region (asia-south1) for v1 or multi-region from day one
- [ ] Tenant DB isolation strategy — schema-per-tenant vs RLS-only in PostgreSQL
- [ ] Mobile platforms for v1 — iOS + Android simultaneously or iOS-first

---

## Changelog

| Date | Version | Description |
|------|---------|-------------|
| 2026-05-20 | 1.0.0 | Initial MEMORY.md created — product identity, stack decisions, directory layout, commands, branch strategy |
