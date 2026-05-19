.PHONY: install dev stack stack-down backend-lint backend-format js-lint js-format quality

# Install JS workspaces (pnpm) and Python dev tools (uv + Ruff) in backend/
install:
	pnpm install
	cd backend && uv sync --all-groups

# Start local databases (PostgreSQL + Redis)
stack:
	docker compose up -d

stack-down:
	docker compose down

dev:
	pnpm dev

backend-lint:
	cd backend && uv run ruff check src
	cd backend && uv run ruff format --check src

backend-format:
	cd backend && uv run ruff format src
	cd backend && uv run ruff check --fix src

js-lint:
	pnpm lint

js-format:
	pnpm format

quality: backend-lint js-lint
