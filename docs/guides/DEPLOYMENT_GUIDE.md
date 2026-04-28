# Railway Backend + Vercel Frontend + Neon DB

This guide deploys Pulse with Railway (backend API), Vercel (frontend SPA), and Neon (Postgres).

## Architecture

- `backend` service runs on Railway using `backend/Dockerfile` and `backend/railway.toml`.
- `frontend` service runs on Vercel using `frontend/vercel.json`.
- Database is Neon Postgres.

## Prerequisites

1. Railway account and project.
2. Vercel account.
3. Neon project.
4. GitHub repo connected to Railway and Vercel.
4. Secrets ready:
   - `SECRET_KEY`
   - `OPENAI_API_KEY`
   - `RESEND_API_KEY`
   - optional Google fact-check/search keys

## Step 1: Configure Neon

Set backend DB URL using Neon connection details from the Neon project dashboard:

```bash
DATABASE_URL=postgresql://<ROLE>:<PASSWORD>@<ENDPOINT>-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

Optional isolation settings (provider-agnostic, only if you intentionally use a non-public schema):

```bash
APP_DB_SCHEMA=<schema_name>
APP_DB_ROLE=<role_name>
```

## Step 2: Create Railway Backend Service

1. In Railway, create a service from this repo.
2. Set **Root Directory** to `backend`.
3. Railway uses `backend/railway.toml` and `backend/Dockerfile`.
4. Add environment variables:

### Required backend variables

- `DATABASE_URL` (Neon URL; use pooler endpoint for Railway)
- `SECRET_KEY`
- `OPENAI_API_KEY`
- `ENVIRONMENT=production`
- `DEBUG=false`
- `FRONTEND_URL` (your frontend Railway public URL)
- `BACKEND_URL` (your backend Railway public URL)

### Optional backend variables

- `RESEND_API_KEY`
- `GOOGLE_FACT_CHECK_API_KEY`
- `GOOGLE_SEARCH_ENGINE_ID`
- `FROM_EMAIL`
- `FROM_NAME`
- any tuning vars from `backend/.env.example`

## Step 3: Create Vercel Frontend Project

1. Import the same GitHub repo in Vercel.
2. Set **Root Directory** to `frontend`.
3. Vercel uses `frontend/vercel.json`:
   - build command: `npm run build`
   - output directory: `dist/client`
   - SPA rewrite: `/(.*) -> /index.html`
4. Set frontend environment variable:

```bash
VITE_API_URL=https://<your-backend-service>.up.railway.app
```

If you attach a custom domain, update both:
- `VITE_API_URL` (Vercel project env)
- `FRONTEND_URL` (Railway backend env)

## Step 4: Deploy + Migrate

1. Deploy backend service.
2. Run migrations in backend shell:

```bash
alembic upgrade head
```

The backend container startup already runs migration/init helpers; running `alembic upgrade head` manually is still the safest explicit post-deploy check during migration.

## Step 5: Verify

1. Backend health:
   - `GET https://<backend-domain>/health`
2. Backend docs:
   - `GET https://<backend-domain>/docs`
3. Frontend (Vercel):
   - open `https://<frontend-domain>`
4. Auth/API smoke test:
   - login and load feed/article detail/analytics paths

## Operational Notes

- Railway replaces Render Blueprint automation; deploy behavior is controlled by each service's settings plus `railway.toml`.
- Keep secrets in Railway environment variables (never commit them).
- For rollbacks, use Railway Deployments history per service.
- Scheduler/background jobs are in the backend process; monitor backend logs to confirm job execution.

## Migration Checklist (Render -> Railway)

- [ ] Create Neon database role/credentials for app runtime.
- [ ] Set `DATABASE_URL` using Neon pooler URL on Railway.
- [ ] Create Railway `backend` service (root `backend`).
- [ ] Create Vercel frontend project (root `frontend`).
- [ ] Set `VITE_API_URL`, `FRONTEND_URL`, `BACKEND_URL`.
- [ ] Run `alembic upgrade head`.
- [ ] Verify `/health`, login flow, feed, and admin jobs.
- [ ] Decommission Render services after Railway is stable.

---

Last updated: 2026-04-26
