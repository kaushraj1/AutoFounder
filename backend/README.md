# backend

The consolidated FastAPI backend for AutoFounder AI — API gateway, LangGraph orchestrator, and
agent workers in a single deployable service (a "modular monolith"). Internal modules are kept
cleanly separated so they can be extracted into independent services in Phase 4 when scale demands.

> **Stack:** Python 3.12 · FastAPI · SQLAlchemy 2 (async) + Alembic · uv · Ruff · mypy · pytest

## Layout

```
app/
  main.py          FastAPI application factory + /health
  core/            config (env validation), structured logging, security
  api/v1/          versioned REST routes (health, ideas, runs)
  db/              async engine/session + UDAL (tenant-scoped data access)
  models/          SQLAlchemy ORM models (runs, artifacts, gates)
  schemas/         Pydantic request/response contracts
  services/        business logic
  agents/          Agent base contract + Strategy / Research / Product-Planner (Phase 1)
  orchestrator/    LangGraph engine (stub — Sprint 1)
  guardrails/      6-stage guardrail pipeline (stub — Sprint 1)
  workers/         async/queue consumers (stub)
alembic/           database migrations
tests/             pytest unit tests
```

## Quick start

```bash
# Install deps (core + dev groups) into a managed venv
uv sync

# Run the API with hot reload
uv run uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/health   ·   http://localhost:8000/docs

# Apply database migrations (needs Postgres — `docker compose up -d` + Supabase, see root README)
uv run alembic upgrade head

# Quality gates
uv run ruff check app tests
uv run mypy app
uv run pytest
```

## What is real vs. stubbed in Phase 1

| Real & runnable | Stubbed (raises `NotImplementedError`, wired in Sprint 1) |
|---|---|
| `/health`, app factory, config, logging | `agents/*` execution logic |
| ORM models + `0001` migration | `orchestrator/engine.py` (LangGraph) |
| `run_service` (in-memory store) + `/v1/ideas`, `/v1/runs` | `guardrails/pipeline.py`, `db/udal.py` write paths |

Optional integration deps (Gemini, LangGraph, Kafka, Supabase, OpenTelemetry) live in named
dependency groups in `pyproject.toml`; install them when the feature that needs them is built,
e.g. `uv sync --group agents`.

See the repository root `README.md` for the full local stack and quality commands.
