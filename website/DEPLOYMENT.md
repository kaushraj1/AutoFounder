# Frontend Deployment — AutoFounder AI

This guide covers connecting the `frontend-web` landing page to Vercel and wiring up
the GitHub Actions auto-deploy pipeline.

---

## Overview

```
git push → main
  └── .github/workflows/deploy-frontend.yml
        ├── pnpm install + tsc + vite build  (runs in GitHub Actions)
        └── vercel deploy --prebuilt --prod   (uploads dist/ to Vercel CDN)
```

The CI builds locally (catching errors before Vercel sees the code) and then pushes
the prebuilt `dist/` to Vercel's CDN via the Vercel CLI.

---

## Step 1 — Create a Vercel Account & Import the Project

1. Go to [vercel.com](https://vercel.com) and sign up or log in.
2. Click **Add New Project → Import Git Repository**.
3. Select the `autofounder-ai` GitHub repository.
4. Set **Root Directory** to `frontend-web/`.
5. Vercel will auto-detect the framework as **Vite**. Confirm these settings
   (they are also set in `vercel.json`):

   | Setting | Value |
   |---------|-------|
   | Framework Preset | Vite |
   | Build Command | `pnpm build` |
   | Output Directory | `dist` |
   | Install Command | `pnpm install` |

6. Click **Deploy**. This first deploy runs from Vercel's UI and confirms everything works.
7. Note the auto-generated `*.vercel.app` URL — use it to preview the landing page.

---

## Step 2 — Get Your Vercel Credentials

You need three values. All are found in the Vercel dashboard.

### `VERCEL_TOKEN`

A personal access token that lets the CLI authenticate on your behalf.

1. Go to [vercel.com/account/tokens](https://vercel.com/account/tokens).
2. Click **Create Token**.
3. Name: `autofounder-ai-github-actions`.
4. Scope: **Full Account** (or restrict to the specific project if available on your plan).
5. Expiry: No expiry (or set a rotation reminder in your calendar).
6. Copy the token — it is shown only once.

### `VERCEL_ORG_ID`

1. Go to [vercel.com/account](https://vercel.com/account) → **General** tab.
2. Find **Team ID** (for a team account) or **User ID** (for a personal account).
3. Copy the value — it looks like `team_xxxxxxxxxxxx` or `user_xxxxxxxxxxxx`.

Alternatively, run `vercel whoami --json` locally after `vercel login` to see both values.

### `VERCEL_PROJECT_ID`

1. Go to your Vercel dashboard → select the `autofounder-ai` project.
2. Click **Settings** → **General**.
3. Find **Project ID** near the top of the page.
4. Copy the value — it looks like `prj_xxxxxxxxxxxx`.

---

## Step 3 — Add Secrets to GitHub

The workflow reads these as GitHub Actions secrets — never hardcode them in files.

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** for each of the three values:

   | Secret name | Value |
   |-------------|-------|
   | `VERCEL_TOKEN` | The token from Step 2 |
   | `VERCEL_ORG_ID` | The org/team ID from Step 2 |
   | `VERCEL_PROJECT_ID` | The project ID from Step 2 |

3. These are now available as `${{ secrets.VERCEL_TOKEN }}` etc. in the workflow.

---

## Step 4 — Set Environment Variables in Vercel Dashboard

If the landing page needs runtime environment variables (e.g. analytics keys, API base URL),
add them here — not in the repository.

1. Go to **Project Settings → Environment Variables** in the Vercel dashboard.
2. Add each variable and choose which environments it applies to
   (Production / Preview / Development).
3. Variables prefixed with `VITE_` are exposed to the browser bundle.
   All others are build-time only.

**Current variables needed by the frontend:**

| Variable | Environment | Notes |
|----------|-------------|-------|
| `VITE_API_URL` | Production | `https://api.autofounder.ai/v1` — set once backend is live |

> Variables that are NOT prefixed with `VITE_` are not embedded in the browser bundle
> and are only available during the Vite build step.

---

## Step 5 — Trigger the First CI Deploy

After adding the secrets, push any change to `main` that touches `frontend-web/`:

```bash
git commit --allow-empty -m "chore: trigger vercel deploy"
git push origin main
```

Or go to **GitHub → Actions → Deploy Frontend to Vercel → Run workflow** to trigger manually.

---

## Step 6 — Custom Domain (optional)

1. In the Vercel dashboard → **Project Settings → Domains**.
2. Add your domain (e.g. `autofounder.ai` or `www.autofounder.ai`).
3. Vercel provides DNS records to add to your domain registrar.
4. Once propagated, Vercel automatically provisions and renews TLS via Let's Encrypt.

---

## Workflow Triggers

The deploy pipeline (`.github/workflows/deploy-frontend.yml`) runs:

- **Automatically** on every push to `main` that changes files inside `frontend-web/`
  or the workflow file itself.
- **Manually** via GitHub Actions UI (`workflow_dispatch`).

It does **not** run on pull requests — PRs only get Vercel preview deployments
if you enable the **Vercel GitHub Integration** (separate from this workflow).
To enable previews on PRs, install the integration at
[vercel.com/integrations/github](https://vercel.com/integrations/github).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Error: No token found` | Check `VERCEL_TOKEN` secret is set in GitHub |
| `Error: Project not found` | Verify `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` match the Vercel dashboard |
| Build fails on `tsc --noEmit` | Fix TypeScript errors in `frontend-web/src/` before pushing |
| `pnpm: command not found` | The `pnpm/action-setup@v4` step must run before any `pnpm` commands |
| Deploy succeeds but site shows old version | Vercel CDN may take 1–2 min to propagate; hard refresh with Ctrl+Shift+R |
| `vercel pull` fails with 401 | Token has expired or been revoked — create a new one in Vercel dashboard |
