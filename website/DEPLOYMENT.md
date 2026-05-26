# Deployment Guide — AutoFounder AI Landing Page

This document explains how to connect the `website/` folder to Vercel and wire up the GitHub Actions CI/CD pipeline.

---

## 1. Connect the Repo to Vercel

### Option A — Vercel Dashboard (recommended for first-time setup)

1. Go to [vercel.com/new](https://vercel.com/new) and sign in.
2. Click **"Import Git Repository"** and select this repo.
3. Set the **Root Directory** to `website`.
4. Vercel auto-detects Vite. The `vercel.json` in `website/` confirms the settings:
   - Build command: `pnpm build`
   - Output directory: `dist`
   - Framework: Vite
5. Click **Deploy**. Vercel runs the first build.

### Option B — Vercel CLI

```bash
cd website
npx vercel link      # follow the prompts to link to your Vercel project
npx vercel deploy --prod
```

---

## 2. Obtain VERCEL_TOKEN, ORG_ID, and PROJECT_ID

### VERCEL_TOKEN

1. Open [vercel.com/account/tokens](https://vercel.com/account/tokens).
2. Click **"Create"**, give it a name (e.g. `github-actions-autofounder`), set expiry.
3. Copy the token — it is shown **once only**.

### VERCEL_ORG_ID

After running `vercel link` inside `website/`, Vercel creates `.vercel/project.json`.  
Open it and copy the `orgId` field:

```json
{ "orgId": "team_xxxxxxxxxxxx", "projectId": "prj_xxxxxxxxxxxx" }
```

Alternatively, find it in **Vercel Dashboard → Settings → General → Team ID**.

### VERCEL_PROJECT_ID

Same file (`.vercel/project.json`) — copy the `projectId` field.  
Or: **Vercel Dashboard → your project → Settings → General → Project ID**.

> The `.vercel/` directory is git-ignored. These IDs are not secrets on their own,  
> but the token is — never commit it.

---

## 3. Add Secrets to GitHub

1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**.
2. Click **"New repository secret"** for each of the three values:

| Secret name | Value |
|---|---|
| `VERCEL_TOKEN` | The token from step 2 |
| `VERCEL_ORG_ID` | `orgId` from `.vercel/project.json` |
| `VERCEL_PROJECT_ID` | `projectId` from `.vercel/project.json` |

---

## 4. Set Environment Variables in the Vercel Dashboard

For any runtime env vars your app needs (e.g. API URLs, public keys):

1. Go to **Vercel Dashboard → your project → Settings → Environment Variables**.
2. Add each variable, choose which environments it applies to (Production / Preview / Development).
3. Redeploy for changes to take effect.

Variables prefixed with `VITE_` are inlined at build time by Vite and exposed to the browser. Never put secrets in `VITE_` variables.

---

## 5. How the CI/CD Pipeline Works

The workflow at `.github/workflows/deploy-frontend.yml` triggers on:
- Every push to `main` that touches `website/**`
- Manual run via **Actions → "Run workflow"**

Pipeline steps:
1. Checkout code
2. Install Node 20 + `npm ci`
3. Type-check (`tsc --noEmit`)
4. Build (`npm run build` → `website/dist/`)
5. Install Vercel CLI
6. Pull Vercel project config
7. Deploy prebuilt output to Vercel production

---

## 6. Preview Deployments

Vercel automatically creates preview deployments for every pull request when the repo is connected via the Vercel Dashboard (Option A above). No extra workflow configuration is needed.
