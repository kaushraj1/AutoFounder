#!/usr/bin/env bash
# One-command local dev setup (macOS / Linux). Requires: Node 20+, pnpm, Docker, uv.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> AutoFounder AI dev setup"

# 1. Environment files (never overwrite an existing one)
[ -f .env ] || { cp .env.example .env && echo "created .env"; }
[ -f AUTOFOUNDER-BACKEND/.env ] || { cp AUTOFOUNDER-BACKEND/.env.example AUTOFOUNDER-BACKEND/.env && echo "created AUTOFOUNDER-BACKEND/.env"; }

# 2. JS workspaces
echo "==> pnpm install"
pnpm install

# 3. Backend (Python via uv)
echo "==> backend deps (uv)"
( cd AUTOFOUNDER-BACKEND && uv python install 3.12 && uv sync )

# 4. Ancillary services (Redis)
echo "==> docker compose up -d"
docker compose up -d

echo ""
echo "Done. Next:"
echo "  - 'supabase start'   (Postgres + pgvector + auth + storage)"
echo "  - 'make dev'         (run the apps)"
echo "  - backend only: cd AUTOFOUNDER-BACKEND && uv run uvicorn app.main:app --reload"
