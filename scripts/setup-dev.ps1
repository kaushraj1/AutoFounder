# One-command local dev setup (Windows PowerShell). Requires: Node 20+, pnpm, Docker, uv.
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> AutoFounder AI dev setup"

# 1. Environment files (never overwrite an existing one)
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "created .env" }
if (-not (Test-Path "backend/.env")) {
    Copy-Item "backend/.env.example" "backend/.env"
    Write-Host "created backend/.env"
}

# 2. JS workspaces
Write-Host "==> pnpm install"
pnpm install

# 3. Backend (Python via uv)
Write-Host "==> backend deps (uv)"
Push-Location "backend"
uv python install 3.12
uv sync
Pop-Location

# 4. Ancillary services (Redis)
Write-Host "==> docker compose up -d"
docker compose up -d

Write-Host ""
Write-Host "Done. Next:"
Write-Host "  - 'supabase start'   (Postgres + pgvector + auth + storage)"
Write-Host "  - 'make dev'         (run the apps)"
Write-Host "  - backend only: cd backend; uv run uvicorn app.main:app --reload"
