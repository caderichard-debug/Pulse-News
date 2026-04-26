# Pulse Project Overview

Pulse is a backend/frontend system that ingests news articles, analyzes them with AI, and enriches them with framework mapping, statistics verification, clustering, and generated context.

## Backend Pipeline
- Scheduler: `backend/app/jobs/scheduler.py`
- Task chain: `backend/app/jobs/tasks.py`
- Pipeline stages:
  - RSS scrape
  - Content extraction
  - AI article analysis
  - Post-analysis fanout (frameworks, statistics, clustering, context)
- Manual: `POST /admin/jobs/analyze-recent` (default limit 5) for newest rows missing `ArticleAnalysis`; `process_unprocessed` now runs extraction when articles are still `PENDING` before relying on “unanalyzed” counts.

## Primary Reliability Controls
- Job execution tracking in `JobExecutionHistory`
- Advisory-lock based duplicate run protection
- Shared retry/backoff utility: `backend/app/utils/resilience.py`
- Configurable retries/timeouts via `backend/app/config.py`

## Mobile App Integration (Expo)
- Mobile app root now runs from `mobile/app` (Expo Router entrypoint in root package).
- Expo runtime API base URL is configured via `EXPO_PUBLIC_API_BASE_URL`.
- Mobile API calls use generated client in `mobile/app/lib/api-client-react` with bearer token injection via `setAuthTokenGetter`.
- Key mobile-backed route families: auth, feed, articles detail + advanced coverage/viewpoints, analytics, favorites, preferences, and challenge.
- `GET /articles/{id}` uses optional JWT (`get_optional_user`): guests can open an article from the public feed; `is_favorited` is false without a session. Some sub-routes (coverage, analyze, etc.) may still require login.
- `mobile/` only contains the `app/` workspace; unused Replit scaffold packages (`artifacts/api-server`, `artifacts/mockup-sandbox`), nested `.git`, and unused `lib/db` were removed to keep the tree lean.
- Mobile `info/*` stack (`editorial-standards`, `how-we-rate-lean`, `appearance`) is registered in the root Stack as `info` for in-app help from Profile and Analytics.

## Deployment Platform (Current)
- Production hosting is standardized on Railway (backend + frontend services).
- Managed Postgres is standardized on Supabase with per-app schema isolation.
- Service deploy configs live at `backend/railway.toml` and `frontend/railway.toml`.
- Use `docs/guides/DEPLOYMENT_GUIDE.md` and `docs/guides/SUPABASE_SCHEMA_ISOLATION_PORTABLE_GUIDE.md` for deploy + DB setup.
- Frontend Railway build command was simplified to `npm run build` (Nixpacks already installs dependencies), and Node is pinned via `frontend/.node-version` to avoid Node 18 engine mismatches during deploy.
- Supabase isolation bootstrap SQL is at `backend/sql/supabase_schema_isolation.sql` (`proj_pulse` + `app_pulse_rw`).
- Production env template is `backend/.env.production`; backend settings auto-load it when `ENVIRONMENT=production` and no explicit secrets file is set.

## Web UI polish (feed parity with mobile)
- Feed and card surfaces in `frontend/src/routes/_app.feed.tsx` and `frontend/src/components/ArticleCard.tsx` were tuned for faster scanning: reduced vertical density, clearer control affordances, and stronger focus-visible states.
- Signal presentation moved to clearer hierarchy in `frontend/src/components/Signals.tsx`: lean now uses a compact pill cue, sentiment adds icon + text (not color-only), and verified badge contrast was increased.
- Feed cards now include a lightweight ethical-framework cue (`FrameworkCue`) while keeping full framework detail on article and analytics pages.
- Analytics charts in `frontend/src/routes/_app.analytics.tsx` now show explicit legends and framework glossary accordions have a visible chevron affordance.
- Reusable feed controls now live in `frontend/src/components/ui/filter-chip.tsx` and `frontend/src/components/ui/filter-select.tsx`, with adoption in feed, signup topic selection, and preferences topic subscriptions.
- CTA hierarchy was normalized on core surfaces (`feed`, `article`, `login`, `signup`, `challenge`) by reusing `frontend/src/components/ui/button.tsx` variants rather than ad-hoc route-level button classes.
- Frontend route typing was stabilized for required search params (e.g. `/feed`, `/preferences`, `/admin`) so redirects and links include explicit search payloads where required by TanStack route validation.

## Observability and Cost
- In-process pipeline metrics utility: `backend/app/utils/pipeline_metrics.py`
- Metrics endpoint: `GET /monitoring/pipeline`
- Cost tracking:
  - OpenAI token cost estimation in `backend/app/utils/openai_client.py`
  - Budget thresholds in settings (`pipeline_daily_budget_usd`, `pipeline_warn_budget_percent`)

