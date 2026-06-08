# Supabase project (AF-014)

AutoFounder AI uses **hosted Supabase** for Postgres + pgvector + Auth + Storage +
Realtime (no RDS — see [`.claude/specs/deployment.md`](../.claude/specs/deployment.md)).
This directory holds the Supabase CLI config; the database **schema is owned by
Alembic** (`backend/alembic`), not by `supabase/migrations`.

## What lives where

| Concern | Owner |
|---|---|
| Local dev stack (Postgres/Auth/Storage/Realtime) | `supabase start` (this `config.toml`) |
| Hosted project link | `supabase link --project-ref <ref>` |
| Schema: `platform.*`, per-tenant `org_*.*`, `orchestrator.*` | **Alembic** (`backend/alembic`, AF-025/026) |
| RLS policies + `CREATE EXTENSION vector` (pgvector) | **Alembic migrations** (AF-026) |
| JWT secret, service-role key, DB URL | AWS Secrets Manager (`autofounder-ai/{env}/supabase/*`, AF-020) |

## One-time setup

```bash
# Local dev — full stack on localhost
supabase start
cd backend && uv run alembic upgrade head      # apply platform + tenant schema

# Link to a hosted project (per environment)
supabase link --project-ref <your-project-ref>
# Push schema to hosted Postgres via Alembic (point DATABASE_URL at the hosted DB):
cd backend && DATABASE_URL=<hosted-pooler-url> uv run alembic upgrade head
```

## Notes

- **pgvector**: enabled by the Alembic tenant migration (`CREATE EXTENSION IF NOT EXISTS vector`), embeddings are `vector(768)` (gemini-embedding). No `config.toml` change needed.
- **Multi-tenant isolation**: schema-per-tenant (`org_<organization_id>`) + RLS + the UDAL cross-tenant guard. The hosted Supabase JWT (`SUPABASE_JWT_SECRET`) is validated by the backend auth middleware (AF-029).
- **Never commit** real project refs, keys, or URLs — they live in Secrets Manager / Vercel / env files (`.gitignore` blocks `*.local`, `secrets/`).
