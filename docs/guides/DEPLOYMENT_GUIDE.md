# Railway + Supabase Deployment Guide

This guide migrates Pulse production deployment from Render to Railway (app hosting) and Supabase (Postgres).

## Architecture

- `backend` service runs on Railway using `backend/Dockerfile` and `backend/railway.toml`.
- `frontend` service runs on Railway using Nixpacks and `frontend/railway.toml`.
- Database is Supabase Postgres with an app-specific schema + runtime role.

Use the schema isolation standard in `docs/guides/SUPABASE_SCHEMA_ISOLATION_PORTABLE_GUIDE.md`.

## Prerequisites

1. Railway account and project.
2. Supabase project.
3. GitHub repo connected to Railway.
4. Secrets ready:
   - `SECRET_KEY`
   - `OPENAI_API_KEY`
   - `RESEND_API_KEY`
   - optional Google fact-check/search keys

## Step 1: Configure Supabase Isolation

Follow `docs/guides/SUPABASE_SCHEMA_ISOLATION_PORTABLE_GUIDE.md` and create:

- Schema: `proj_pulse`
- Runtime role: `app_pulse_rw`

Set backend DB URL in this format:

```bash
DATABASE_URL=postgresql://app_pulse_rw:<PASSWORD>@db.<SUPABASE_PROJECT_REF>.supabase.co:5432/postgres?sslmode=require&schema=proj_pulse
```

Important:
- Do not use `service_role` for request-path database access.
- Keep schema-qualified migrations and app access scoped to `proj_pulse`.

## Step 2: Create Railway Backend Service

1. In Railway, create a service from this repo.
2. Set **Root Directory** to `backend`.
3. Railway uses `backend/railway.toml` and `backend/Dockerfile`.
4. Add environment variables:

### Required backend variables

- `DATABASE_URL` (Supabase URL with `schema=proj_pulse`)
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

## Step 3: Create Railway Frontend Service

1. Create a second service from the same repo.
2. Set **Root Directory** to `frontend`.
3. Railway uses `frontend/railway.toml`.
4. Set frontend environment variable:

```bash
VITE_API_URL=https://<your-backend-service>.up.railway.app
```

If you attach a custom domain, update both:
- `VITE_API_URL` (frontend service)
- `FRONTEND_URL` (backend service)

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
3. Frontend:
   - open `https://<frontend-domain>`
4. Auth/API smoke test:
   - login and load feed/article detail/analytics paths

## Operational Notes

- Railway replaces Render Blueprint automation; deploy behavior is controlled by each service's settings plus `railway.toml`.
- Keep secrets in Railway environment variables (never commit them).
- For rollbacks, use Railway Deployments history per service.
- Scheduler/background jobs are in the backend process; monitor backend logs to confirm job execution.

## Migration Checklist (Render -> Railway)

- [ ] Create Supabase schema-scoped runtime role.
- [ ] Set `DATABASE_URL` with `schema=proj_pulse`.
- [ ] Create Railway `backend` service (root `backend`).
- [ ] Create Railway `frontend` service (root `frontend`).
- [ ] Set `VITE_API_URL`, `FRONTEND_URL`, `BACKEND_URL`.
- [ ] Run `alembic upgrade head`.
- [ ] Verify `/health`, login flow, feed, and admin jobs.
- [ ] Decommission Render services after Railway is stable.

---

Last updated: 2026-04-23
