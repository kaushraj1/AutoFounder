# AutoFounder-AI Enterprise — Web dashboard

React + TypeScript + Vite per `docs/architecture` / stack spec. The application shell ships in **Phase P9**.

Phase 1 exposes only workspace wiring (`pnpm` / Turborepo) and **ESLint + Prettier** baseline.

## Admin surface

The super-admin dashboard is **not** a separate package. It lives inside this app as a role-guarded `/admin` route group (`app/(admin)/` once the App Router shell lands in **Phase P9**). Only callers whose JWT carries the `admin` role reach it; founders are routed to `app/(founder)/`. One app, one deploy, one auth surface — admin powers still walled off behind a role check (RBAC, see `.claude/CLAUDE.md` §15).
