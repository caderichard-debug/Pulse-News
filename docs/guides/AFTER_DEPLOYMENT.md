# After Deployment (Railway + Supabase)

Use this checklist right after a production deploy.

## 1) Health + Logs

- Backend health endpoint returns 200:
  - `GET /health`
- Backend startup logs show migration/init completed.
- Frontend returns 200 and loads JS/CSS assets successfully.

## 2) Database State

- Confirm Alembic is at head:
  - `alembic current`
- Confirm Supabase runtime role is schema-scoped as expected (see isolation guide).
- Confirm baseline data exists (topics/sources/framework seeds).

## 3) Functional Smoke Tests

- Login/signup works.
- Feed, article detail, analytics routes load.
- Admin-only actions are restricted to admin users.
- Optional newsletter/send flows work if `RESEND_API_KEY` is configured.

## 4) Jobs + Monitoring

- Check backend logs for scheduler registration.
- Trigger one admin job manually to verify:
  - scrape
  - analyze
- Check monitoring endpoint:
  - `GET /monitoring/pipeline`

## 5) Config Drift Prevention

- Keep Railway service env vars aligned with documented values.
- Update docs when changing deploy commands, domains, or env requirements.
- Never store secrets in repo files.

## 6) Rollback Readiness

- Verify prior Railway deployment is available in history.
- Keep a tested rollback path for backend and frontend separately.

---

Related docs:
- `docs/guides/DEPLOYMENT_GUIDE.md`
- `docs/guides/SUPABASE_SCHEMA_ISOLATION_PORTABLE_GUIDE.md`
