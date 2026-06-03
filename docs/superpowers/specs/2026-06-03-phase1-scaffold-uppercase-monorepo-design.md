# Design — Phase 1 Scaffold: UPPERCASE Monorepo + Consolidated Backend

**Date:** 2026-06-03
**Status:** Approved (build end-to-end)
**Author:** Claude Code (brainstormed with Vishal Prasad)
**Reference:** [euron-sudh/PROJECT-3-AgentOps-Commander](https://github.com/euron-sudh/PROJECT-3-AgentOps-Commander) — the org's Phase-1-complete scaffold we mirror.

---

## 1. Goal

Bring `PROJECT-1-AutoFounder-AI` from an empty placeholder skeleton (`.gitkeep`, `placeholder.ts`)
up to the same maturity bar as the reference repo PROJECT-3 ("Phase 1 complete"): a monorepo that
installs, runs a backend with a working `/health` endpoint, has real DB migrations, and passes its
own tests — using the org's UPPERCASE directory convention and a single consolidated backend.

## 2. Decisions (locked via brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| Build scope | Full Phase 1 scaffold (tooling + CI + real backend `app/` + Alembic + tests + `packages/api-client`) | User selection |
| Directory naming | Switch to UPPERCASE top-level dirs (`AUTOFOUNDER-BACKEND`, etc.) | Mirror PROJECT-3 org convention |
| Backend shape | **One consolidated backend** (modular monolith) | PROJECT-3 uses one backend; simpler for Phase 1; split into services in Phase 4 |
| Junk files | Delete `test.txt`, `test.py`, `test_file.py`, `projectstructure-steps.txt` | User-confirmed leftover scratch |
| Frontends/mobile/infra | Rename only, keep placeholder | Out of Phase 1 scope (§45 = Validation Engine backend) |
| Stack (unchanged, deliberate divergence from PROJECT-3) | Keep AWS, Next.js 14, pnpm | Defined in CLAUDE.md / stack.md; PROJECT-3's Azure/Vite/npm are its own choices |

## 3. Target structure

```
PROJECT-1-AutoFounder-AI/
├── AUTOFOUNDER-BACKEND/          # apps/api + orchestrator + ai-services, merged
│   ├── app/
│   │   ├── main.py               # FastAPI app + /health (real, runs)
│   │   ├── core/                 # config.py, logging.py, security.py
│   │   ├── api/v1/               # health, ideas, runs routers
│   │   ├── db/                   # base, session, udal (async SQLAlchemy)
│   │   ├── models/               # run, artifact, gate + TimestampMixin
│   │   ├── schemas/              # Pydantic request/response
│   │   ├── services/             # run_service.py
│   │   ├── agents/               # base.py (Agent ABC) + strategy/research/product_planner stubs
│   │   ├── orchestrator/         # LangGraph engine (documented stub)
│   │   ├── guardrails/           # 6-stage pipeline (documented stub)
│   │   ├── utils/  workers/
│   ├── alembic/                  # env.py + 0001 initial migration
│   ├── tests/                    # test_health, test_run_service
│   ├── Dockerfile .dockerignore .python-version .env.example
│   ├── pyproject.toml uv.lock alembic.ini README.md
├── AUTOFOUNDER-FRONTEND-WEB/     # apps/web  (placeholder)
├── AUTOFOUNDER-ADMIN/            # apps/admin (placeholder)
├── AUTOFOUNDER-MOBILE-APP/       # mobile-app (placeholder)
├── AUTOFOUNDER-INFRA/            # infra/ (terraform/ + codedeploy/)
├── packages/ shared/ + api-client/   # api-client NEW (typed stub)
├── scripts/ setup-dev.{ps1,sh}, deploy-backend-dev.{ps1,sh}
├── docs/ + docs/{api,database,deployment}
├── .github/workflows/ backend-ci.yml, lint.yml (NEW) + deploy-frontend.yml
├── .editorconfig .prettierrc .prettierignore tsconfig.base.json .pre-commit-config.yaml
├── Makefile (fixed) pnpm-workspace.yaml (fixed) package.json (updated)
└── docker-compose.yml turbo.json .env.example README.md
```

## 4. What is REAL vs STUB

- **Real (must run/pass):** `app/main.py` (`GET /health`), `core/config.py` (pydantic-settings,
  validates env at startup), `core/logging.py` (structlog JSON), `db/base.py` + `db/session.py`
  (async SQLAlchemy engine + session dependency), `models/` (runs/artifacts/gates from CLAUDE.md §19.3),
  `schemas/`, `services/run_service.py`, `api/v1/` routes, `alembic/` (env + 0001 migration),
  `tests/` (health via TestClient + service unit test).
- **Documented stub (raises NotImplementedError with TODO + phase pointer):** `agents/*`,
  `orchestrator/engine.py`, `guardrails/pipeline.py`, `db/udal.py` write paths, `packages/api-client`.

## 5. Migration mechanics

- `git mv` every rename → preserves history.
- `apps/ai-services` + `apps/orchestrator` (empty `.gitkeep`) → become `app/orchestrator/` +
  `app/workers/` inside backend; old dirs removed.
- Backend placeholder (`src/autofounder_ai/`, `docker/placeholder_http_server.py`) replaced by `app/`.

## 6. Bugs fixed in-flight

- `Makefile`: `cd backend` → `cd AUTOFOUNDER-BACKEND` (current path broken).
- `pnpm-workspace.yaml`: remove non-existent `website` / `vscode-extension`; repoint to new dirs.
- Root `package.json`: lint scripts `apps/api` → `AUTOFOUNDER-BACKEND`.
- `.gitignore`: add `.DS_Store`.

## 7. Docs updated to match

`CLAUDE.md` §13 (consolidated-backend note), §40 (tree), §42 (commands), §12.3 + §19.2 (paths);
`stack.md` Monorepo section; `README.md` (monorepo layout table).

## 8. Verification gate

`uv sync` → `ruff check` → `mypy` → `alembic upgrade head` (Docker Postgres) → `pytest` →
`pnpm install && pnpm lint`. Real output shown; no unproven success claims.

## 9. Atomic commits

1. Rename to UPPERCASE + delete junk
2. Backend app skeleton + Alembic + tests
3. Root tooling + build-config fixes
4. CI workflows + scripts + api-client
5. Docs update

All on `vishal-feature-branch`; each commit individually revertable.
