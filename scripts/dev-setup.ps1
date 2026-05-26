$ErrorActionPreference = "Stop"

Write-Host "AutoFounder AI Enterprise — local dev bootstrap (Phase 1)" -ForegroundColor Cyan

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
  Write-Error "pnpm is required. Install from https://pnpm.io/installation"
  exit 1
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Warning "Docker not found; skip compose until Docker Desktop (or engine) is installed."
}

if ((-not (Test-Path ".env")) -and (Test-Path ".env.example")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example" -ForegroundColor Green
}

pnpm install

Push-Location backend
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Warning "uv not found. Install: https://docs.astral.sh/uv/getting-started/`n  Then run: cd backend && uv sync --all-groups"
} else {
  uv sync --all-groups
}
Pop-Location

if (Get-Command docker -ErrorAction SilentlyContinue) {
  docker compose up -d
  Write-Host "PostgreSQL + Redis started (docker compose)." -ForegroundColor Green
}

Write-Host "Done. Next: pnpm dev  |  make quality  |  see README.md" -ForegroundColor Cyan
