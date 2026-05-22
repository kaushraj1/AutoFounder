# Deploying the AutoFounder AI Landing Page to Vercel

This guide covers how to connect the `website/` folder to Vercel and set up
automatic deployments via GitHub Actions on every push to `main`.

---

## 1. Connect the repository to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in (or create a free account).
2. Click **Add New → Project**.
3. Import your GitHub repository (`Auto-Founder-AI/CodeBase` or equivalent).
4. When prompted for the **Root Directory**, set it to `website`.
5. Vercel will auto-detect the framework as **Vite**. Confirm the following settings:
   - **Build Command:** `pnpm build`
   - **Output Directory:** `dist`
   - **Install Command:** `pnpm install`
6. Click **Deploy**. Vercel will build and serve the site immediately.

---

## 2. Obtain your Vercel credentials

You need three values for the GitHub Actions workflow:

### `VERCEL_TOKEN`
1. Go to [vercel.com/account/tokens](https://vercel.com/account/tokens).
2. Click **Create Token**, give it a name (e.g. `github-actions`), and set the scope to your team/personal account.
3. Copy the token — it is shown only once.

### `VERCEL_ORG_ID`
1. Go to your Vercel **Team Settings** (or Personal Account Settings if no team).
2. The **Team ID** shown there is your `VERCEL_ORG_ID`.
   - Alternatively run `vercel whoami` with the Vercel CLI after logging in.

### `VERCEL_PROJECT_ID`
1. Open the project you created in step 1 on the Vercel dashboard.
2. Go to **Settings → General**.
3. The **Project ID** is listed near the top of the page.

---

## 3. Add secrets to GitHub

1. In your GitHub repository, go to **Settings → Secrets and variables → Actions**.
2. Click **New repository secret** for each of the following:

| Secret name          | Value                          |
|----------------------|--------------------------------|
| `VERCEL_TOKEN`       | Token from step 2              |
| `VERCEL_ORG_ID`      | Team/Account ID from step 2    |
| `VERCEL_PROJECT_ID`  | Project ID from step 2         |

---

## 4. How automatic deployments work

The workflow file at `.github/workflows/deploy-frontend.yml`:

- Triggers on every push to `main` that changes any file inside `website/`.
- Installs dependencies with `pnpm`, runs `pnpm build`, then calls the Vercel API to push the `dist/` output as a **production deployment**.
- No manual action is required after the initial setup.

---

## 5. Set environment variables in the Vercel dashboard

If the landing page ever needs runtime environment variables (e.g. a future API endpoint):

1. Open the project on [vercel.com](https://vercel.com).
2. Go to **Settings → Environment Variables**.
3. Add key-value pairs and choose which environments they apply to (Production / Preview / Development).
4. Redeploy for changes to take effect.

---

## 6. Custom domain (optional)

1. In the Vercel project, go to **Settings → Domains**.
2. Add your domain (e.g. `autofounder.ai`) and follow the DNS instructions.
3. Vercel provisions an SSL certificate automatically via Let's Encrypt.
