.PHONY: install dev stack stack-down backend-lint backend-format backend-typecheck backend-test js-lint js-format quality

# Install JS workspaces (pnpm) and backend Python deps (uv)
install:
	pnpm install
	cd AUTOFOUNDER-BACKEND && uv sync

# Start local ancillary services (Redis). Run `supabase start` separately for Postgres + pgvector.
stack:
	docker compose up -d

stack-down:
	docker compose down

dev:
	pnpm dev

backend-lint:
	cd AUTOFOUNDER-BACKEND && uv run ruff check app tests
	cd AUTOFOUNDER-BACKEND && uv run ruff format --check app tests

backend-format:
	cd AUTOFOUNDER-BACKEND && uv run ruff format app tests
	cd AUTOFOUNDER-BACKEND && uv run ruff check --fix app tests

backend-typecheck:
	cd AUTOFOUNDER-BACKEND && uv run mypy app

backend-test:
	cd AUTOFOUNDER-BACKEND && uv run pytest

js-lint:
	pnpm lint

js-format:
	pnpm format

# Run all quality gates locally (mirrors CI)
quality: backend-lint backend-typecheck backend-test js-lint
