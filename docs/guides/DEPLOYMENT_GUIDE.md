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

Set backend DB URL in one of these formats:

**Direct host** (works when your runtime has IPv6 to Supabase, or the host resolves to reachable IPv4):

```bash
DATABASE_URL=postgresql://app_pulse_rw:<PASSWORD>@db.<SUPABASE_PROJECT_REF>.supabase.co:5432/postgres?sslmode=require&schema=proj_pulse
```

**Session pooler (recommended for Railway / IPv4-only egress)** — use the region from Supabase **Connect** → **Session pooler**:

```bash
DATABASE_URL=postgresql://app_pulse_rw.<SUPABASE_PROJECT_REF>:<PASSWORD>@aws-0-<REGION>.pooler.supabase.com:5432/postgres?sslmode=require&schema=proj_pulse
```

Also set (so SQLModel binds to `proj_pulse`, Alembic stores `alembic_version` there, `/health` pings DB, and connect-time isolation checks run):

```bash
SUPABASE_DB_SCHEMA=proj_pulse
SUPABASE_DB_ROLE=app_pulse_rw
```

Important:
- Do not use `service_role` for request-path database access.
- Keep schema-qualified migrations and app access scoped to `proj_pulse`.
- Use pooler **port 5432** (session mode), not **6543** (transaction mode), unless you know you need transaction pooling.

## Step 2: Create Railway Backend Service

1. In Railway, create a service from this repo.
2. Set **Root Directory** to `backend`.
3. Railway uses `backend/railway.toml` and `backend/Dockerfile`.
4. Add environment variables:

### Required backend variables

- `DATABASE_URL` (Supabase URL with `schema=proj_pulse`; prefer Session pooler on Railway)
- `SUPABASE_DB_SCHEMA=proj_pulse`
- `SUPABASE_DB_ROLE=app_pulse_rw`
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
- [ ] Set `DATABASE_URL` with `schema=proj_pulse` (Session pooler URL on Railway).
- [ ] Set `SUPABASE_DB_SCHEMA` and `SUPABASE_DB_ROLE` for runtime isolation checks and metadata.
- [ ] Create Railway `backend` service (root `backend`).
- [ ] Create Railway `frontend` service (root `frontend`).
- [ ] Set `VITE_API_URL`, `FRONTEND_URL`, `BACKEND_URL`.
- [ ] Run `alembic upgrade head`.
- [ ] Verify `/health`, login flow, feed, and admin jobs.
- [ ] Decommission Render services after Railway is stable.

---

Last updated: 2026-04-26
