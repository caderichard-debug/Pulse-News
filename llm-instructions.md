# Pulse News Aggregator - AI Assistant Instructions

> **This file provides comprehensive context for AI assistants working on the Pulse project.** It combines and refactors content from `claude.md` and `copilot-plan.md` to provide complete project navigation, development guidelines, and behavioral instructions.

**Last Updated:** October 24, 2025
**Project Status:** Phase 3 Complete ✅ (234/234 tests passing)

---

## 🚀 Quick Start for AI Assistants

### What is Pulse?

**Pulse** is an AI-powered news aggregation platform that:
- Scrapes articles from 8+ trusted news sources via RSS feeds
- Uses OpenAI GPT-4o-mini to analyze sentiment, bias, and ethical frameworks
- Verifies statistics with 3-stage pipeline (source tracing, credibility, fact-checking)
- Generates personalized daily newsletters
- Maps articles to ethical frameworks for deeper context understanding
- Provides visualizations showing how news shapes discourse ("Lens on Discourse")

### Project Architecture

**Backend (Python/FastAPI):**
- **FastAPI** - REST API framework
- **SQLModel** - ORM with validation
- **PostgreSQL** - Primary database
- **Alembic** - Database migrations
- **APScheduler** - Background jobs
- **OpenAI GPT-4o-mini** - AI analysis

**Frontend (TanStack Router + Vite):**
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TanStack Router** - File-based routing
- **Tailwind CSS** - Utility-first styling
- **React** - UI framework
- **Recharts** - Data visualizations

**Key Status:** 127 backend tests + 107 frontend tests = 234 total (100% passing)

---

## 🗂️ Project Structure Navigator

This section helps you quickly find relevant files for any task.

### 📁 Backend Structure (`/backend/app/`)

#### Core Configuration
- **[models.py](backend/app/models.py)** - SQLModel database schemas (all tables)
- **[config.py](backend/app/config.py)** - Environment settings and configuration
- **[database.py](backend/app/database.py)** - Database session management
- **[main.py](backend/app/main.py)** - FastAPI app entry point & router registration

#### API Routes (`/backend/app/routes/`)
- **[auth.py](backend/app/routes/auth.py)** - User registration, login (JWT)
- **[preferences.py](backend/app/routes/preferences.py)** - User preferences (topics, sources, settings)
- **[analytics.py](backend/app/routes/analytics.py)** - Dashboard analytics endpoints (5 endpoints)
- **[feed.py](backend/app/routes/feed.py)** - Article feed with filtering (3 endpoints)
- **[articles.py](backend/app/routes/articles.py)** - Article listing and detail (merged router, 2 endpoints)
- **[admin.py](backend/app/routes/admin.py)** - Admin controls & job triggers
- **[test_email.py](backend/app/routes/test_email.py)** - Email testing endpoints

#### Services (`/backend/app/services/`)
**Core Article Pipeline:**
- **[rss_scraper.py](backend/app/services/rss_scraper.py)** - Fetch articles from RSS feeds
- **[article_extractor.py](backend/app/services/article_extractor.py)** - Extract full content (trafilatura + readability)
- **[ai_analyzer.py](backend/app/services/ai_analyzer.py)** - AI analysis (summary, sentiment, bias)
- **[framework_generator.py](backend/app/services/framework_generator.py)** - Map articles to ethical frameworks

**Statistics Verification (V2 - 3-stage pipeline):**
- **[statistics_verifier.py](backend/app/services/statistics_verifier.py)** - Main orchestrator
- **[source_tracer.py](backend/app/services/source_tracer.py)** - Extract source URLs/names
- **[credibility_rater.py](backend/app/services/credibility_rater.py)** - Rate source credibility
- **[fact_check_integrator.py](backend/app/services/fact_check_integrator.py)** - External fact-checking APIs

**Enhancement Services:**
- **[article_clusterer.py](backend/app/services/article_clusterer.py)** - Group similar articles
- **[context_generator.py](backend/app/services/context_generator.py)** - Generate article context
- **[newsletter_service.py](backend/app/services/newsletter_service.py)** - Build & send newsletters
- **[url_analyzer.py](backend/app/services/url_analyzer.py)** - On-demand article URL analysis

#### Background Jobs (`/backend/app/jobs/`)
- **[scheduler.py](backend/app/jobs/scheduler.py)** - APScheduler configuration
- **[tasks.py](backend/app/jobs/tasks.py)** - Job definitions (scraping, analysis, newsletters)

#### Testing (`/backend/tests/`)
127 tests passing - Key test files:
- `test_analytics.py` - Analytics endpoints
- `test_feed.py` - Feed filtering/pagination
- `test_article_detail.py` - Article detail endpoint
- `test_source_preferences.py` - Source management
- `test_newsletter_preferences.py` - Newsletter filtering
- `test_statistics_verifier.py` - V2 verification pipeline

### 📁 Frontend Structure (`/frontend/src/`)

> NOTE: The frontend is route-driven via TanStack Router (`/frontend/src/routes/`) and generated route tree (`/frontend/src/routeTree.gen.ts`), not Next.js App Router.

#### Pages (`/frontend/src/app/`)
- **[page.tsx](frontend/src/app/page.tsx)** - Landing page (hero, features)
- **[login/](frontend/src/app/login/)** - Login page
- **[signup/](frontend/src/app/signup/)** - 2-step registration (user details → topic selection)
- **[preferences/](frontend/src/app/preferences/)** - Topic/source/settings management (3-tab interface)
- **[dashboard/](frontend/src/app/dashboard/)** - Analytics dashboard with visualizations
- **[feed/](frontend/src/app/feed/)** - Article feed with filtering & pagination
- **[article/[id]/](frontend/src/app/article/[id]/)** - Article detail with full analysis
- **[analyze/](frontend/src/app/analyze/)** - Article URL analysis page
- **[how-it-works/](frontend/src/app/how-it-works/)** - Educational page explaining data pipeline

#### Components (`/frontend/src/components/`)
- **[Navbar.tsx](frontend/src/components/Navbar.tsx)** - Global navigation bar

#### API Client (`/frontend/src/lib/`)
- **[api.ts](frontend/src/lib/api.ts)** - Centralized API client with all endpoints

#### Testing (`/frontend/src/`)
107 tests passing - Key test suites:
- `lib/__tests__/api.test.ts` - API client tests
- `app/dashboard/__tests__/page.test.tsx` - Dashboard tests
- `app/preferences/__tests__/page.test.tsx` - Preferences tests
- `app/feed/__tests__/page.test.tsx` - Feed tests
- `app/article/__tests__/page.test.tsx` - Article detail tests

---

## 📚 Documentation Navigation

### 📖 Complete Documentation Structure
All documentation is organized in `/docs/` with the following structure:

#### 📋 Documentation Index
- **[docs/README.md](docs/README.md)** - Main documentation navigation page

#### 🏗️ Architecture & System Design
- **[docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)** - Complete system architecture, data flow, deployment
- **[docs/architecture/STATISTICS_VERIFICATION_V2_PLAN.md](docs/architecture/STATISTICS_VERIFICATION_V2_PLAN.md)** - Statistics verification V2 design

#### 📡 API Documentation
- **[docs/api/API.md](docs/api/API.md)** - Complete REST API reference with examples
- Interactive docs: http://localhost:8000/docs

#### 🧪 Testing Documentation
- **[docs/testing/TESTING.md](docs/testing/TESTING.md)** - Comprehensive testing guide
- **[docs/testing/HOW_TO_RUN_TESTS.md](docs/testing/HOW_TO_RUN_TESTS.md)** - Quick test commands reference
- **[docs/testing/E2E_TESTING_METHODOLOGY.md](docs/testing/E2E_TESTING_METHODOLOGY.md)** - End-to-end testing approach
- **[docs/testing/TESTING_STRATEGY.md](docs/testing/TESTING_STRATEGY.md)** - Testing strategy and best practices

#### 🔧 Development Guides
- **[docs/development/SETUP.md](docs/development/SETUP.md)** - Installation & configuration
- **[docs/development/DEVELOPMENT_GUIDE.md](docs/development/DEVELOPMENT_GUIDE.md)** - Development workflows
- **[docs/development/GIT_WORKFLOW_CHEATSHEET.md](docs/development/GIT_WORKFLOW_CHEATSHEET.md)** - Git commands reference
- **[docs/development/MIGRATION_GUIDE.md](docs/development/MIGRATION_GUIDE.md)** - Database migration guide

#### 📖 How-to Guides
- **[docs/guides/DEPLOYMENT_GUIDE.md](docs/guides/DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[docs/guides/HOW_TO_SEND_TEST_EMAIL.md](docs/guides/HOW_TO_SEND_TEST_EMAIL.md)** - Email testing guide
- **[docs/guides/ADMIN_PANEL_QUICK_START.md](docs/guides/ADMIN_PANEL_QUICK_START.md)** - Admin panel reference

#### 📋 Planning & Future Work
- **[docs/planning/ADMIN_PANEL_PLAN.md](docs/planning/ADMIN_PANEL_PLAN.md)** - Complete admin panel plan
- **[docs/planning/FRONTEND_ARCHITECTURE_PLAN.md](docs/planning/FRONTEND_ARCHITECTURE_PLAN.md)** - 16-week frontend roadmap
- **[docs/planning/features/](docs/planning/features/)** - Individual feature plans

---

## 🎯 Finding Code by Feature

### Authentication & Users
- **Models**: `User` in [models.py](backend/app/models.py:30)
- **Routes**: [auth.py](backend/app/routes/auth.py)
- **Frontend**: [login/](frontend/src/app/login/), [signup/](frontend/src/app/signup/)

### Article Scraping & Extraction
- **Scraper**: [rss_scraper.py](backend/app/services/rss_scraper.py)
- **Extractor**: [article_extractor.py](backend/app/services/article_extractor.py)
- **Models**: `Article` in [models.py](backend/app/models.py:80)
- **Jobs**: [tasks.py](backend/app/jobs/tasks.py) - `scrape_rss_feeds()`, `extract_articles()`

### AI Analysis & Frameworks
- **Analyzer**: [ai_analyzer.py](backend/app/services/ai_analyzer.py)
- **Framework Generator**: [framework_generator.py](backend/app/services/framework_generator.py)
- **Models**: `ArticleAnalysis`, `Framework`, `ArticleFrameworkLink` in [models.py](backend/app/models.py)

### Statistics Verification
- **Orchestrator**: [statistics_verifier.py](backend/app/services/statistics_verifier.py)
- **Stage 1 (Tracing)**: [source_tracer.py](backend/app/services/source_tracer.py)
- **Stage 2 (Credibility)**: [credibility_rater.py](backend/app/services/credibility_rater.py)
- **Stage 3 (Fact-checking)**: [fact_check_integrator.py](backend/app/services/fact_check_integrator.py)

### User Preferences
- **Backend**: [preferences.py](backend/app/routes/preferences.py) - topics, sources, settings
- **Frontend**: [preferences/](frontend/src/app/preferences/)
- **Models**: `UserTopicPreference`, `UserSourceSubscription` in [models.py](backend/app/models.py)

### Analytics & Dashboard
- **Backend**: [analytics.py](backend/app/routes/analytics.py) - sentiment, bias, heatmaps
- **Frontend**: [dashboard/](frontend/src/app/dashboard/)
- **Visualizations**: Recharts (sentiment line chart, bias stacked area)

### Article Feed
- **Backend**: [feed.py](backend/app/routes/feed.py) - filtering, pagination
- **Frontend**: [feed/](frontend/src/app/feed/)

### Article URL Analysis (On-Demand)
- **Service**: [url_analyzer.py](backend/app/services/url_analyzer.py)
- **API Route**: [analyze.py](backend/app/routes/analyze.py) - `/analyze/url` POST endpoint
- **Frontend**: [analyze/](frontend/src/app/analyze/)

### Newsletters
- **Service**: [newsletter_service.py](backend/app/services/newsletter_service.py)
- **Template**: [newsletter.html](backend/app/templates/newsletter.html)
- **Models**: `Newsletter` in [models.py](backend/app/models.py)

### Background Jobs
- **Scheduler**: [scheduler.py](backend/app/jobs/scheduler.py)
- **Tasks**: [tasks.py](backend/app/jobs/tasks.py)
- **Admin Triggers**: [admin.py](backend/app/routes/admin.py)

---

## 🔧 Common Development Tasks

### Running Tests
```bash
# Backend (all tests)
docker-compose exec backend pytest

# Backend (specific file)
docker-compose exec backend pytest tests/test_analytics.py -v

# Frontend (all tests)
cd frontend && npm test

# Frontend (watch mode)
cd frontend && npm run test:watch
```

### Database Operations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1

# Critical: Always sync migrations between container and local!
docker cp news_backend:/app/alembic/versions/[NEW_FILE].py backend/alembic/versions/
```

### Manual Job Triggers
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

# Trigger jobs
curl -X POST http://localhost:8000/admin/jobs/scrape
curl -X POST http://localhost:8000/admin/jobs/analyze
```

### Docker Operations
```bash
# Start all services
docker-compose up --build

# Restart backend
docker-compose restart backend

# View logs
docker logs news_backend -f

# Stop all
docker-compose down
```

---

## 🚨 Critical Behavioral Instructions

### ✅ DO - Always Follow These Rules

1. **Maintain Local-Container Parity**
   - ALWAYS run `./scripts/sync-local-container.sh` after migrations or dependency changes
   - NEVER let container and local filesystem diverge
   - This ensures zero-overhead deployments

2. **Organized Commits**
   - Stage changes and prepare commits with clear, logical grouping
   - Use descriptive commit messages: `feat: add dark mode support`
   - Include file references and why changes were made
   - **NEVER push commits** - wait for explicit user approval

3. **Dark Mode Implementation**
   - ALWAYS implement dark mode support when creating new components
   - Use semantic CSS classes from `globals.css` instead of hardcoded colors
   - Test in both light and dark modes before considering complete
   - **Never** use hardcoded colors like `bg-blue-50` without dark variants

4. **Security Best Practices**
   - NEVER commit real secrets, API keys, or passwords
   - Use placeholder values in documentation
   - Run security audits before major releases

### ❌ DON'T - Avoid These Common Mistakes

1. **Don't Push Without Approval**
   - Commit locally but wait for user to push explicitly
   - Ask before making any destructive operations

2. **Don't Break Container Parity**
   - Don't update container without updating local files
   - Don't forget to copy migration files both directions

3. **Don't Skip Testing**
   - Don't commit without running tests: `npm test` and `pytest`
   - Don't ignore test failures or warnings

4. **Don't Use Hardcoded Colors**
   - Don't use `bg-blue-50`, `text-yellow-900` without dark mode
   - Don't assume light mode only for any UI component

---

## 🔄 Local-Container Parity (CRITICAL)

**The local filesystem must ALWAYS match the Docker container state.**

### Quick Sync Script
```bash
./scripts/sync-local-container.sh
./scripts/sync-local-container.sh --help  # Show options
```

### Migration Sync Rules
1. **After creating migration in container:**
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "description"
   # IMMEDIATELY copy to local:
   docker cp news_backend:/app/alembic/versions/[NEW_FILE].py backend/alembic/versions/
   ```

2. **After editing migration locally:**
   ```bash
   # Edit file locally
   vim backend/alembic/versions/XXXXX_description.py
   # IMMEDIATELY copy to container:
   docker cp backend/alembic/versions/XXXXX_description.py news_backend:/app/alembic/versions/
   ```

### Pre-Deployment Checklist
- [ ] All migrations synced between container and local
- [ ] `requirements.txt` matches installed packages
- [ ] All tests passing: `pytest` + `npm test`
- [ ] No hardcoded secrets anywhere in codebase
- [ ] Dark mode tested for new UI components

---

## 📊 Database Schema Quick Reference

### Core Tables
```
users
├── UserTopicPreference (topics subscribed, priority)
└── UserSourceSubscription (sources subscribed)

sources
├── Articles
│   ├── ArticleAnalysis (AI summary, sentiment, bias)
│   ├── ArticleFrameworkLink → Frameworks
│   ├── StatisticVerification (V2 with source tracing)
│   ├── ArticleClusterMember → ArticleCluster
│   └── ArticleContext (background, timeline, significance)
└── SourceCredibilityRating (cached credibility scores)

topics
└── UserTopicPreference

newsletters
```

---

## 🎯 Current Implementation Status

### ✅ Completed (Phase 3)
- **Backend**: All core services operational (127 tests passing)
- **Frontend**: Phases 1-3 complete (107 tests passing)
  - Enhanced preferences (topics, sources, settings)
  - Dashboard with analytics visualizations
  - Article feed with filtering and detail pages
  - Article URL analysis (on-demand analysis)
  - Comprehensive test coverage

### 🔨 Next (Phase 4)
- **Challenge System** - Weekly viewpoint engagement tracking

### 📋 In Planning
- **Admin Panel** - Complete implementation plan ready
  - Database management (view, edit, delete all tables)
  - Job monitoring and triggering
  - User management and permissions
  - Full React/Next.js UI with secure authentication

---

## 🔐 Environment Variables

Required in `backend/.env`:
```bash
# Database
DATABASE_URL=postgresql://postgres:password@db:5432/news_db

# AI (OpenAI)
OPENAI_API_KEY=sk-proj-...
AI_MODEL=gpt-4o-mini

# Email (Resend)
RESEND_API_KEY=re_...
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=Pulse News

# Auth
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Optional fact-checking
GOOGLE_FACT_CHECK_API_KEY=...
CLAIMBUSTER_API_KEY=...

# Documentation Links
DOCUMENTATION_URL=https://docs.pulsenews.app
```

### 🔄 Environment Variable Updates
**CRITICAL**: When updating any environment variables:
1. **Update both** `.env` (local) AND `render.yaml` (production)
2. **Restart services** after changes: `docker-compose restart`
3. **Verify variables loaded** by checking logs
4. **For production deployment**: Update render.yaml environment section

### 🚨 Render Frontend Asset Guardrail
Current direction is TanStack Start **SPA mode** + Render static hosting.

Migration notes:
- `frontend/vite.config.ts` now sets:
  - `cloudflare: false`
  - `tanstackStart.spa.enabled: true`
- `frontend/postbuild.mjs` creates compatibility outputs:
  - `dist/server/index.js` (copied from `dist/server/server.js`)
  - `dist/client/index.html` (copied from `dist/client/_shell.html`)

Why compatibility exists:
- The live Render frontend service is still configured as a web service in dashboard settings.
- It currently runs:
  `mkdir -p public && rm -rf public/assets && cp -R dist/client/assets public/assets && npx srvx serve --entry dist/server/index.js --port $PORT --prod`
- The postbuild shim keeps this command working during migration.

Target end state:
- Convert `pulse-frontend` to a Render static site using `frontend/dist/client`.
- Keep SPA fallback rewrite to `/_shell.html` (or `/index.html` if using the copied compatibility file).

After deploy, always verify in logs:
- `HEAD /` or `GET /` returns `200`
- `GET /assets/*.css` and `GET /assets/*.js` return `200` (not `404`)

### 🧭 Mandatory Agent Protocol (Render frontend)
For any agent modifying frontend build/deploy behavior, treat this as required policy:

1. **Do not trust config files alone**
   - Treat live Render dashboard service settings as runtime truth.
   - `render.yaml` can drift; sync validated runtime values back to git.

2. **Do not claim "fixed" without runtime evidence**
   - Required proof in this order:
     - Latest deploy status is `live`
     - Runtime logs show successful startup
     - Runtime logs show `/assets/*` requests returning `200` (not `404`)
     - At least one direct asset URL check returns `200` for JS and CSS

3. **Preserve compatibility during migration**
   - Until the service is fully converted to Render static site:
     - Keep `frontend/postbuild.mjs` compatibility outputs in place
     - Ensure assets are available for whichever static root `srvx` resolves (`public` vs `dist/server/public`)

4. **Failure signature to recognize immediately**
   - App route requests return `200` but `/assets/*.js` and `/assets/*.css` return `404`
   - This means HTML is served but client bundle is missing from the active static root

5. **Definition of done (frontend deploy changes)**
   - Deploy is live
   - Homepage renders styled UI
   - Asset requests are `200`
   - Guardrail docs are updated if deployment behavior changed

---

## 📞 Quick References

- **Interactive API Docs**: http://localhost:8000/docs
- **Frontend Dev Server**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Backend Container**: `news_backend`
- **Database Container**: `news_db`
- **Main Documentation**: [docs/](docs/)
- **Security Audit**: [secrets-compromise-report.md](secrets-compromise-report.md)

---

## 🛠️ Tech Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | FastAPI | Latest |
| **ORM** | SQLModel | 0.0.16 |
| **Database** | PostgreSQL | 16 |
| **Migrations** | Alembic | Latest |
| **Jobs** | APScheduler | Latest |
| **AI** | OpenAI GPT-4o-mini | Latest |
| **Email** | Resend API | Latest |
| **Frontend** | Next.js | 15.5.4 |
| **UI** | React | 19.1.0 |
| **Styling** | Tailwind CSS | 4 |
| **Charts** | Recharts | Latest |
| **Testing (BE)** | pytest | Latest |
| **Testing (FE)** | Jest + RTL | Latest |

---

## 🚨 Important Conventions

### Frontend Route + Admin Guardrails (Anti-Regression)
- Frontend routing is **TanStack Router file routes** under `frontend/src/routes/`.
- The user-facing dashboard route is **`/analytics`** (not `/dashboard`).
- Keep the legacy alias route **`/dashboard -> /analytics`** in place to prevent broken CTA/bookmark links.
- Admin UI route is **`/admin`** (`frontend/src/routes/_app.admin.tsx`).
- Show admin nav only for users with `user.is_admin === true` (with temporary fallback for `cade.richard@gmail.com` while role data is reconciled).
- Backend admin dashboard data source is `GET /admin-panel/dashboard`; if this endpoint contract changes, update `frontend/src/routes/_app.admin.tsx` in the same PR.
- Job operations in admin panel now include:
  - `GET /admin-panel/jobs/scheduler` (scheduled job state)
  - `POST /admin-panel/jobs/control/{job_id}?action=pause|resume|stop|trigger`
  - `GET /admin-panel/jobs/history/{execution_id}` (single execution log payload)
  - `POST /admin-panel/jobs/trigger/reanalyze_unanalyzed_failed` (manual recovery)
- Admin jobs list entries should deep-link to `/admin?tab=jobs&logId=<execution_id>` and display execution `error_message` / `result_data`.
- Admin article list titles should link to `/article/$id` for direct inspection.
- Before declaring dashboard/admin fixes complete, verify all of:
  - `/analytics` loads
  - `/dashboard` redirects to `/analytics`
  - admin user can open `/admin` without 404

### Code Organization
- **Services**: Pure business logic, no FastAPI dependencies
- **Routes**: API endpoints only, delegate to services
- **Models**: SQLModel schemas with validation
- **Tests**: One test file per service/route

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`

### Git Workflow
- **Main branch**: Always stable, CI must pass
- **Feature branches**: `feature/description` or `fix/description`
- **Commits**: Descriptive messages, reference issues if applicable

### Testing Standards
- **Backend**: Aim for 100% coverage on services
- **Frontend**: Test user interactions, not implementation details
- **Fixtures**: Reuse test data across files
- **IMPORTANT**: Do NOT automatically run tests unless explicitly requested

---

**Maintained by:** AI assistants working on Pulse
**Last Updated:** October 24, 2025
**Status:** Version 1.0 Complete + Production Ready (234 tests passing)