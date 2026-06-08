# AutoFounder AI — VS Code Extension

Your in-IDE AI co-founder. Monitor runs, approve HITL gates, generate code, and
open artifacts without leaving the editor — the third client surface alongside the
Founder Portal (web) and the mobile app.

> **Phase 6 (AF-072 → AF-078).** Built against the AF-030 REST + AF-031 Realtime +
> AF-034 HITL contract in [`.claude/specs/api-design.md`](../.claude/specs/api-design.md).
> Where an upstream dependency is still landing (AF-031 Realtime, AF-041 Coder
> Agent), the extension degrades gracefully per the plan's fallback matrix.

## Features

| Capability | Task | What it does |
|---|---|---|
| Activation core + auth | AF-072 | Supabase Auth **PKCE** sign-in; the JWT is stored in VS Code **SecretStorage** (never settings, never logs). |
| Runs sidebar | AF-073 | A tree of your runs with status icons, pillar progress, and a live cost badge. |
| Gate notifications | AF-074 | A banner the moment a run needs a human decision — **Approve / Reject** inline. |
| Code generation | AF-075 | `Generate Component` / `Generate API Endpoint` stream the Coder Agent's output into a new editor tab. |
| Live stream panel | AF-076 | A webview that follows a run's live token/step stream over WebSocket (with polling fallback). |
| Artifact quick-open | AF-077 | `Open Lean Canvas / ERD / OpenAPI Spec` preview generated artifacts in the editor. |
| Marketplace publish | AF-078 | `vsce package` / `publish` via GitHub Actions, with automatic version bump on merge to `main`. |

## Getting started

1. **Configure the backend** in Settings (`Ctrl/Cmd+,` → search "AutoFounder"):
   - `autofounder.apiBaseUrl` — backend base URL (e.g. `http://localhost:8000`).
   - `autofounder.supabaseUrl` / `autofounder.supabaseAnonKey` — for the hosted PKCE sign-in.
2. **Sign in** — open the **AutoFounder AI** activity-bar view and click **Sign In**.
   - No hosted Supabase project yet? Use **Sign In with Token (dev)** and paste a JWT.
3. **Submit an idea** (`+` on the Runs view) and watch it run — click a run to open the
   live stream; approve gates from the banner; open artifacts from the command palette.

## Commands

`AutoFounder: Sign In` · `Sign In with Token (dev)` · `Sign Out` · `Submit New Idea` ·
`Refresh Runs` · `Open Live Stream` · `Approve / Reject Gate` · `Cancel Run` ·
`Generate Component` · `Generate API Endpoint` · `Open Lean Canvas` · `Open ERD` ·
`Open OpenAPI Spec` · `Open Artifact`

## Development

```bash
pnpm install                                   # from the repo root (pnpm workspace)
pnpm --filter autofounder-ai run watch         # incremental esbuild bundle
# Press F5 in VS Code → "Run Extension" to launch an Extension Development Host.

pnpm --filter autofounder-ai run typecheck     # tsc --noEmit
pnpm --filter autofounder-ai run lint          # eslint
pnpm --filter autofounder-ai run test          # node:test unit suite
pnpm --filter autofounder-ai run package       # build a .vsix locally
```

## Architecture

A standard TypeScript VS Code extension, bundled with **esbuild** to
`dist/extension.js`. The codebase separates pure, unit-tested logic from the
`vscode`-coupled surfaces:

| Pure (no `vscode`) | `vscode`-coupled |
|---|---|
| `types`, `normalize`, `http`, `pkce`, `streamEvents`, `format`, `apiClient` | `extension`, `config`, `auth`, `runMonitor`, `runStream`, `sidebar`, `gates`, `codegen`, `streamPanel`, `artifacts` |

- **Auth** — Supabase PKCE (`auth.ts` + pure `pkce.ts`); token in `SecretStorage`.
- **Transport** — `apiClient.ts` (typed REST, envelope-aware) + `runStream.ts`
  (WebSocket `GET /v1/runs/{id}/stream`, polling fallback).
- **Security** — tokens only in `SecretStorage`; the stream webview is locked to a
  strict CSP with a per-load nonce and receives data only via `postMessage`.

## Publishing (AF-078)

`.github/workflows/vscode-publish.yml` builds, lints, tests, and packages the
extension on every PR. On push to `main` (or manual dispatch), **if the `VSCE_PAT`
repository secret is set**, it bumps the patch version, publishes to the
Marketplace, commits the bump back (`[skip ci]`), and cuts a GitHub Release.
Set the `euron-autofounder` publisher's PAT as `VSCE_PAT` to enable publishing.
