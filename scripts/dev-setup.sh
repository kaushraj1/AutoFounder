#!/usr/bin/env bash
set -euo pipefail

echo "AutoFounder-AI Enterprise — local dev bootstrap (Phase 1)"

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm is required. Install from https://pnpm.io/installation" >&2
  exit 1
fi

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

pnpm install

if command -v uv >/dev/null 2>&1; then
  (cd backend && uv sync --all-groups)
else
  echo "Warning: uv not found. Install https://docs.astral.sh/uv/getting-started/ then: cd backend && uv sync --all-groups" >&2
fi

if command -v docker >/dev/null 2>&1; then
  docker compose up -d
  echo "PostgreSQL + Redis started (docker compose)."
else
  echo "Warning: Docker not found; start Postgres/Redis manually when ready." >&2
fi

echo "Done. Next: pnpm dev | make quality | see README.md"
