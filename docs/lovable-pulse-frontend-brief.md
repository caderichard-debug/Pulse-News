# Pulse — Project overview for frontend generation (Lovable)

Use this document as the product + API contract brief. **The backend already exists** (FastAPI). Generate a **new frontend** that talks to it over HTTPS. Do not invent endpoints; match the paths below unless you coordinate a backend change.

---

## One-sentence pitch

**Pulse** is an AI-assisted news platform: it aggregates articles from trusted RSS sources, analyzes each story (summary, sentiment, political lean, bias signals), maps content to **ethical frameworks** (“lens on discourse”), optionally **verifies statistics** with a multi-stage pipeline, clusters related coverage, and supports **personalized feeds**, **dashboards**, **favorites**, **URL analysis**, and a **weekly challenge** system. Users get **JWT auth**, **topic/source preferences**, and **newsletter**-related settings via the API.

---

## Brand & UX direction

- **Name:** Pulse. **Tagline (current):** “News aggregation with ethical clarity.”
- **Tone:** Calm, credible, editorial—not sensational. Emphasize transparency (how analysis works, uncertainty, source quality).
- **Visual:** Modern web app; support **light and dark** themes. Prefer semantic tokens (CSS variables / design tokens), not hardcoded light-only palettes.
- **Accessibility:** Sensible focus states, labels on forms, chart data not color-only.

---

## Technical constraints (must follow)

| Topic | Rule |
|--------|------|
| **API base URL** | Single env var: `NEXT_PUBLIC_API_URL` (e.g. `https://api.yourdomain.com`). All REST calls: `{NEXT_PUBLIC_API_URL}{path}`. |
| **Auth** | `POST /auth/login` and `POST /auth/register` return `access_token` (JWT). Send `Authorization: Bearer <token>` on protected routes. Persist token client-side (existing app used `localStorage` key **`token`**). |
| **CORS** | Backend allows configured frontend origins; set real production URLs in backend env (`FRONTEND_URL`, `FRONTEND_CUSTOM_URL`). |
| **OAuth (optional)** | Google OAuth flows may use a dedicated auth domain (e.g. `https://auth.pulsenews.app`); callback routes exist—coordinate redirect URIs with backend config. |
| **Errors** | API errors are typically JSON `{ "detail": "..." }`. Handle `401`/`403` by clearing session and redirecting to login for protected areas. |
| **Docs** | Interactive OpenAPI: `{API_BASE}/docs` — use for exact schemas when in doubt. |

---

## Information architecture (pages to support)

Mirror this **route map** so users and bookmarks stay coherent:

| Route | Purpose |
|--------|---------|
| `/` | Landing; if session valid, redirect to `/feed`. |
| `/login`, `/signup` | Email/password auth; signup may include topic selection. |
| `/welcome` | Post-signup onboarding. |
| `/verify-email` | Email verification UI. |
| `/forgot-password`, `/reset-password` | Password reset flow. |
| `/feed` | Main article feed: filters, pagination, cards with summary/sentiment/lean/framework hints, favorites toggle. |
| `/article/[id]` | Deep article view: full analysis, frameworks axis, statistic verification rows, related articles, context blocks, favorite. |
| `/preferences` | Tabs: topics, sources, settings (newsletter, theme, etc.). |
| `/dashboard` or `/analytics` | Analytics dashboard (charts: sentiment over time, bias distribution, framework heatmap). **Current codebase uses `/analytics`.** |
| `/sources` | Browse/manage news sources (list, bias, trust, user-submitted source flows if exposed). |
| `/analyze` | Submit arbitrary article URL for on-demand extraction + analysis. |
| `/how-it-works` | Educational page explaining pipeline (RSS → extract → AI → verification → newsletter). |
| `/insights` | Insights / lens-on-discourse style content (align with API if present). |
| `/privacy-policy` | Static policy. |
| `/challenge/[date]` | Weekly challenge: claims, responses, feedback (dated challenges). |
| `/admin`, `/admin/*` | Admin panel (jobs, users, sources, articles, DB tools, audit). Usually **admin token + JWT**—treat as restricted internal UI. |
| `/login/callback` | OAuth return handler (if using OAuth). |

---

## Core API surface (REST, relative to API base)

> **Method:** Paths below are from the production **Next.js client** that ships with the repo (`frontend/src/lib/api.ts`). Prefer matching these exactly.

### Public / auth

- `GET /health` — Liveness (`{ "status": "healthy" }` in app; older docs may say `"ok"`).
- `POST /auth/register` — Body: `name`, `email`, `password`, optional `topic_ids[]`.
- `POST /auth/login` — Body: `email`, `password` → `{ access_token, token_type, user }`.
- `GET /auth/me` — Current user (requires JWT).
- `POST /auth/logout`
- Password / email verification: `/auth/request-password-reset`, `/auth/reset-password`, `/auth/verify-reset-token/{token}`, `/auth/verify-email`, `/auth/resend-verification-email`
- Account: multipart or JSON per backend for `PATCH`/`DELETE` patterns—see `/docs`.

### Preferences (authenticated)

- `GET /preferences/topics` — Available topics.
- `GET /preferences`, `PUT /preferences` — User preferences payload.
- `POST /preferences/topics/{id}/subscribe`, `POST .../unsubscribe`
- `GET /preferences/sources`, `PUT /preferences/sources`
- `GET /preferences/settings`, `PUT /preferences/settings`

### Feed & articles

- `GET /feed/articles` — Query params include: `page`, `page_size`, `search`, repeated `topics`, `source_ids`, `political_leans`, `date_range`, `date_from`, `date_to`, `sort_by`, `only_analyzed`, `only_verified_stats`, `favorites_only`, `has_opposing_viewpoints`. Returns paginated list + `total_count`.
- `GET /feed/topics`, `GET /feed/sources` — Filter metadata.
- `GET /articles/{id}` — Rich article detail: analysis, frameworks, statistics verification, related articles, optional context object, `is_favorited`.

### Sources

- `GET /sources` — Query: `bias`, `active_only`, `sort_by`; returns sources + `total_count`.
- `POST /sources` — Create source (admin or permitted roles per backend).
- Additional URL-based source creation endpoints exist—see OpenAPI.

### Analytics

- `GET /analytics/user-stats`
- `GET /analytics/sentiment-over-time` — time range query params.
- `GET /analytics/bias-distribution?weeks=`
- `GET /analytics/framework-heatmap?framework1_id=&framework2_id=&days=`
- `GET /analytics/frameworks/available`

### Favorites

- `POST /favorites/articles/{articleId}`, `DELETE /favorites/articles/{articleId}`
- `GET /favorites?limit=&offset=`
- `GET /favorites/check/{articleId}`

### Analyze (on-demand URL)

- `POST /analyze/url` — JSON `{ "url": "https://..." }` — returns analysis payload (article fields, frameworks, statistics, context, optional `article_id`).

### Challenge system

- Endpoints under `/challenge/...` include: current challenge, responses, feedback, analytics aggregates, performance by `challengeId`, trends. **Inspect OpenAPI** for exact paths and bodies; the client includes helpers for feedback, participation, and analytics.

### Subscriptions / Stripe (if enabled on deployment)

- Prefix `/api/subscriptions` and `/api/webhooks` may exist for billing—optional for v1 UI unless backend has paywall flags exposed.

---

## Domain concepts (for copy & UI labels)

- **Article:** From RSS; full text extracted; may be “processed” with AI analysis.
- **Sentiment / political lean:** Numeric or categorical signals for tone and ideological positioning (treat as **model-assisted**, not ground truth).
- **Frameworks:** Named ethical lenses (e.g. liberty vs welfare); each article can sit on an axis with explanation and relevance.
- **Statistic verification:** Claims in text traced to sources, credibility, optional fact-check metadata.
- **Clusters / related articles:** Similar coverage across outlets.
- **Challenge:** Time-bound engagement (claims, user responses, lightweight analytics).

---

## What to ship first (suggested MVP for Lovable)

1. Auth: login, register, logout, session restore via `/auth/me`.
2. Feed + article detail + favorites.
3. Preferences (topics, sources, core settings).
4. Analytics dashboard (charts from analytics endpoints).
5. Static pages: landing, how-it-works, privacy.
6. Analyze URL page.

Defer **admin** and **challenge** to phase 2 unless you need them on day one.

---

## Out of scope for the frontend generator

- Scrapers, schedulers, OpenAI calls, Postgres schema, Alembic migrations, Resend email sending—the **backend** owns these.
- Do not duplicate business rules client-side except for UX validation; **trust API responses** for entitlements and limits.

---

## Reference files in this repository (for humans, not Lovable)

- API shapes and client: `frontend/src/lib/api.ts`
- REST reference: `docs/api/API.md`
- Architecture: `docs/architecture/ARCHITECTURE.md`

---

## Checklist before going live

- [ ] `NEXT_PUBLIC_API_URL` points to the **browser-accessible** API (correct scheme, host, port).
- [ ] Backend CORS includes your frontend origin.
- [ ] OAuth redirect URIs registered (if using Google login).
- [ ] Error and empty states for feed, article, and analytics.
- [ ] Dark mode tested on primary surfaces.

---

*Generated as a handoff brief for Pulse; align with `http://<API_HOST>/docs` for authoritative request/response schemas.*
