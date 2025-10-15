# Pulse - AI-Powered News Aggregator

> **Project Context for AI Assistants**
> This document helps new Claude sessions quickly understand the Pulse codebase, navigate to relevant files, and maintain documentation standards.

---

## 📋 Quick Start for New Sessions

### What is Pulse?

**Pulse** is an AI-powered news aggregation platform that:
- Scrapes articles from trusted news sources via RSS feeds
- Uses AI (OpenAI GPT-4o-mini) to analyze sentiment, bias, and ethical frameworks
- Verifies statistics with source tracing and fact-checking
- Generates personalized daily newsletters
- Provides a **"Lens on Discourse"** - helping users understand how news shapes conversation through data visualizations

### Project Status

**Current Phase**: Phase 3 Complete ✅
- ✅ Backend: All core services operational (127 backend tests passing)
- ✅ Frontend: Phase 1-3 complete (107 frontend tests passing)
  - Enhanced preferences (topics, sources, settings)
  - Dashboard with analytics visualizations
  - Article feed with filtering and detail pages
  - Comprehensive test coverage
- 🔨 Next: Phase 4 (Challenge System) - Weekly viewpoint engagement tracking

---

## 🗂️ Project Structure Navigator

### Backend (`/backend/app/`)

#### Core Configuration
- **[models.py](backend/app/models.py)** - SQLModel database schemas (all tables)
- **[config.py](backend/app/config.py)** - Environment settings
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
**Article Pipeline:**
- **[rss_scraper.py](backend/app/services/rss_scraper.py)** - Fetch articles from RSS feeds
- **[article_extractor.py](backend/app/services/article_extractor.py)** - Extract full content (trafilatura + readability)
- **[ai_analyzer.py](backend/app/services/ai_analyzer.py)** - AI analysis (summary, sentiment, bias)
- **[framework_generator.py](backend/app/services/framework_generator.py)** - Map articles to ethical frameworks

**Statistics Verification (V2 - 3-stage pipeline):**
- **[statistics_verifier.py](backend/app/services/statistics_verifier.py)** - Orchestrator
- **[source_tracer.py](backend/app/services/source_tracer.py)** - Extract source URLs/names
- **[credibility_rater.py](backend/app/services/credibility_rater.py)** - Rate source credibility
- **[fact_check_integrator.py](backend/app/services/fact_check_integrator.py)** - External fact-checking APIs

**Enhancement Services:**
- **[article_clusterer.py](backend/app/services/article_clusterer.py)** - Group similar articles
- **[context_generator.py](backend/app/services/context_generator.py)** - Generate article context
- **[newsletter_service.py](backend/app/services/newsletter_service.py)** - Build & send newsletters

#### Background Jobs (`/backend/app/jobs/`)
- **[scheduler.py](backend/app/jobs/scheduler.py)** - APScheduler configuration
- **[tasks.py](backend/app/jobs/tasks.py)** - Job definitions

#### Testing (`/backend/tests/`)
- 127 tests, 100% passing
- Key test files:
  - `test_analytics.py` - Analytics endpoints
  - `test_feed.py` - Feed filtering/pagination
  - `test_article_detail.py` - Article detail endpoint
  - `test_source_preferences.py` - Source management
  - `test_newsletter_preferences.py` - Newsletter filtering
  - `test_statistics_verifier.py` - V2 verification pipeline

### Frontend (`/frontend/src/`)

#### Pages (`/frontend/src/app/`)
- **[page.tsx](frontend/src/app/page.tsx)** - Landing page (hero, features)
- **[login/](frontend/src/app/login/)** - Login page (improved placeholder visibility)
- **[signup/](frontend/src/app/signup/)** - 2-step registration (user details → topic selection)
- **[preferences/](frontend/src/app/preferences/)** - Topic/source/settings management (3-tab interface)
- **[dashboard/](frontend/src/app/dashboard/)** - Analytics dashboard with visualizations
- **[feed/](frontend/src/app/feed/)** - Article feed with filtering & pagination
- **[article/[id]/](frontend/src/app/article/[id]/)** - Article detail with full analysis
- **[how-it-works/](frontend/src/app/how-it-works/)** - Educational page explaining data pipeline

#### Components (`/frontend/src/components/`)
- **[Navbar.tsx](frontend/src/components/Navbar.tsx)** - Global navigation bar with dynamic user name, active page highlighting, and logout

#### API Client (`/frontend/src/lib/`)
- **[api.ts](frontend/src/lib/api.ts)** - Centralized API client with all endpoints

#### Testing (`/frontend/src/`)
- 107 tests passing
- Test suites:
  - `lib/__tests__/api.test.ts` - API client tests
  - `app/dashboard/__tests__/page.test.tsx` - Dashboard tests
  - `app/preferences/__tests__/page.test.tsx` - Preferences tests
  - `app/feed/__tests__/page.test.tsx` - Feed tests
  - `app/article/__tests__/page.test.tsx` - Article detail tests

---

## 📚 Documentation Index

### Core Documentation (`/docs/`)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture, data flow, deployment
- **[API.md](docs/API.md)** - Complete API reference with examples
- **[FRONTEND_ARCHITECTURE_PLAN.md](docs/FRONTEND_ARCHITECTURE_PLAN.md)** - 16-week frontend roadmap (Phases 1-6)
- **[STATISTICS_VERIFICATION_V2_PLAN.md](docs/STATISTICS_VERIFICATION_V2_PLAN.md)** - V2 verification design

### Guides
- **[SETUP.md](docs/SETUP.md)** - Installation & configuration
- **[DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)** - Development workflows
- **[TESTING.md](docs/TESTING.md)** - Test patterns & commands
- **[HOW_TO_RUN_TESTS.md](docs/HOW_TO_RUN_TESTS.md)** - Quick test reference
- **[GIT_WORKFLOW_CHEATSHEET.md](docs/GIT_WORKFLOW_CHEATSHEET.md)** - Git commands

### Email Testing
- **[HOW_TO_SEND_TEST_EMAIL.md](docs/HOW_TO_SEND_TEST_EMAIL.md)** - Email testing guide
- **[QUICK_EMAIL_TEST.md](docs/QUICK_EMAIL_TEST.md)** - Quick email reference

### Project Context
- **[CHANGELOG.md](CHANGELOG.md)** - Complete development history (all changes)
- **[README.md](README.md)** - Project overview & quick start

---

## 🧭 Finding Code by Feature

### "I need to work on [X]"

#### Authentication & Users
- **Models**: `User` in [models.py](backend/app/models.py:30)
- **Routes**: [auth.py](backend/app/routes/auth.py)
- **Frontend**: [login/](frontend/src/app/login/), [signup/](frontend/src/app/signup/)

#### Article Scraping & Extraction
- **Scraper**: [rss_scraper.py](backend/app/services/rss_scraper.py)
- **Extractor**: [article_extractor.py](backend/app/services/article_extractor.py)
- **Models**: `Article` in [models.py](backend/app/models.py:80)
- **Jobs**: [tasks.py](backend/app/jobs/tasks.py) - `scrape_rss_feeds()`, `extract_articles()`

#### AI Analysis & Frameworks
- **Analyzer**: [ai_analyzer.py](backend/app/services/ai_analyzer.py)
- **Framework Generator**: [framework_generator.py](backend/app/services/framework_generator.py)
- **Models**: `ArticleAnalysis`, `Framework`, `ArticleFrameworkLink` in [models.py](backend/app/models.py)

#### Statistics Verification
- **Orchestrator**: [statistics_verifier.py](backend/app/services/statistics_verifier.py)
- **Stage 1 (Tracing)**: [source_tracer.py](backend/app/services/source_tracer.py)
- **Stage 2 (Credibility)**: [credibility_rater.py](backend/app/services/credibility_rater.py)
- **Stage 3 (Fact-checking)**: [fact_check_integrator.py](backend/app/services/fact_check_integrator.py)
- **Models**: `StatisticVerification`, `SourceCredibilityRating` in [models.py](backend/app/models.py)

#### User Preferences
- **Backend**: [preferences.py](backend/app/routes/preferences.py) - topics, sources, settings
- **Frontend**: [preferences/](frontend/src/app/preferences/)
- **Models**: `UserTopicPreference`, `UserSourceSubscription` in [models.py](backend/app/models.py)
- **Tests**: [test_source_preferences.py](backend/tests/test_source_preferences.py)

#### Analytics & Dashboard
- **Backend**: [analytics.py](backend/app/routes/analytics.py) - sentiment, bias, heatmaps
- **Frontend**: [dashboard/](frontend/src/app/dashboard/)
- **Visualizations**: Recharts (sentiment line chart, bias stacked area)
- **Tests**: [test_analytics.py](backend/tests/test_analytics.py)

#### Article Feed
- **Backend**: [feed.py](backend/app/routes/feed.py) - filtering, pagination
- **Frontend**: [feed/](frontend/src/app/feed/)
- **Article Detail**: [article_detail.py](backend/app/routes/article_detail.py)
- **Tests**: [test_feed.py](backend/tests/test_feed.py), [test_article_detail.py](backend/tests/test_article_detail.py)

#### Newsletters
- **Service**: [newsletter_service.py](backend/app/services/newsletter_service.py)
- **Template**: [newsletter.html](backend/app/templates/newsletter.html)
- **Models**: `Newsletter` in [models.py](backend/app/models.py)
- **Tests**: [test_newsletter_preferences.py](backend/tests/test_newsletter_preferences.py)

#### Background Jobs
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

### Sync Local & Container
```bash
# ALWAYS run after migrations or dependency changes
./scripts/sync-local-container.sh
```

### Database Migrations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# IMMEDIATELY sync to local (or use sync script above)
docker cp news_backend:/app/alembic/versions/[NEW_FILE].py backend/alembic/versions/

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

### Manual Job Triggers
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

# Trigger scraping
curl -X POST http://localhost:8000/admin/jobs/scrape

# Trigger analysis
curl -X POST http://localhost:8000/admin/jobs/analyze

# Check job status
curl http://localhost:8000/admin/scheduler/status
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

## 🔄 Local-Container Parity (CRITICAL)

**IMPORTANT**: The local filesystem must ALWAYS match the Docker container state for deployment readiness. This ensures zero-overhead deployments to production.

### Quick Sync Script

Use the automated sync script to maintain parity:

```bash
# Run full sync (checks migrations, requirements, and database state)
./scripts/sync-local-container.sh

# Show help
./scripts/sync-local-container.sh --help
```

See [scripts/README.md](scripts/README.md) for detailed documentation.

### Critical Rule: Alembic Migrations

**ALWAYS ensure migrations exist in BOTH locations:**

1. **After creating a migration in the container:**
   ```bash
   # Create migration (happens in container)
   docker-compose exec backend alembic revision --autogenerate -m "description"

   # IMMEDIATELY copy to local filesystem
   docker cp news_backend:/app/alembic/versions/[NEW_FILE].py backend/alembic/versions/
   ```

2. **After manually creating a migration locally:**
   ```bash
   # Create/edit migration file locally
   vim backend/alembic/versions/XXXXX_description.py

   # IMMEDIATELY copy to container
   docker cp backend/alembic/versions/XXXXX_description.py news_backend:/app/alembic/versions/
   ```

3. **Verify parity regularly:**
   ```bash
   # List migrations in container
   docker-compose exec backend ls -la /app/alembic/versions/

   # List migrations locally
   ls -la backend/alembic/versions/

   # Compare (should be identical except timestamps)
   diff <(docker-compose exec backend ls /app/alembic/versions/ | sort) \
        <(ls backend/alembic/versions/ | sort)
   ```

### Other Local-Container Discrepancies to Watch

1. **Python Dependencies** (`backend/requirements.txt`)
   - If you `pip install` in container, update requirements.txt locally
   - Always rebuild after requirements.txt changes: `docker-compose up --build`

2. **Environment Variables** (`backend/.env`)
   - Container reads from this file via docker-compose volume mount
   - Changes take effect after `docker-compose restart backend`

3. **Frontend Dependencies** (`frontend/package.json`)
   - If you install npm packages locally, they're reflected in container via volume mount
   - If you install in container, copy `package.json` and `package-lock.json` out

4. **Configuration Files**
   - `backend/alembic.ini` - Database migration config
   - `backend/app/config.py` - Application settings
   - `docker-compose.yml` - Service definitions
   - Always maintain locally, as these are source of truth

### Pre-Deployment Checklist

Before deploying or committing changes:

- [ ] All alembic migrations copied from container to local repo
- [ ] `requirements.txt` matches installed packages in container
- [ ] `package.json` matches installed packages
- [ ] All configuration files committed to git
- [ ] `.env` variables documented (but not committed)
- [ ] Tests pass: `docker-compose exec backend pytest` (backend) and `npm test` (frontend)
- [ ] Backend starts without errors: `docker logs news_backend --tail 50`
- [ ] Frontend builds successfully: `npm run build` (if applicable)

### Troubleshooting Parity Issues

**Problem**: Migration exists in container but not locally
```bash
# List missing migrations
docker-compose exec backend ls /app/alembic/versions/ | \
  grep -v "$(ls backend/alembic/versions/ | sed 's/^/^/' | paste -sd'|')"

# Copy all migrations from container
docker cp news_backend:/app/alembic/versions/. backend/alembic/versions/
```

**Problem**: Code changes in container not reflected locally (shouldn't happen with volumes)
```bash
# Check volume mounts
docker inspect news_backend | grep -A 10 "Mounts"

# Verify volume is mounted correctly in docker-compose.yml
grep -A 5 "volumes:" docker-compose.yml
```

**Problem**: Database schema doesn't match models
```bash
# Check current migration
docker-compose exec backend alembic current

# Check pending migrations
docker-compose exec backend alembic history

# Apply all migrations
docker-compose exec backend alembic upgrade head

# If needed, generate new migration for model changes
docker-compose exec backend alembic revision --autogenerate -m "sync_schema"
# Then IMMEDIATELY copy to local: docker cp news_backend:/app/alembic/versions/...
```

---

## 🗄️ Database Schema Quick Reference

### Key Tables
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

See [ARCHITECTURE.md](docs/ARCHITECTURE.md#database-schema) for full schema with field details.

---

## 🎯 Current Implementation Status

### ✅ Completed (Backend)
- Core article pipeline (scrape → extract → analyze → frameworks)
- Statistics verification V2 (source tracing, credibility, fact-checking)
- Article clustering & context generation
- Newsletter generation & email delivery
- User authentication & preferences
- Admin controls & job scheduling
- **All 127 backend tests passing**

### ✅ Completed (Frontend - Phases 1-3)
- **Phase 1**: Enhanced preferences (topics, sources, settings with 3-tab interface)
- **Phase 2**: Dashboard with analytics visualizations (sentiment, bias, stats)
- **Phase 3**: Article feed & detail pages (filtering, pagination, full analysis)
- Landing page with hero section
- 2-step signup flow with topic selection
- Global navigation bar (Dashboard, Feed, Preferences, How It Works)
- "How It Works" educational page
- UI polish (improved placeholder visibility on auth pages)
- **All 107 frontend tests passing**

### 🔜 Upcoming (Phase 4-6)
- **Phase 4**: Challenge system (weekly viewpoint tracking)
- **Phase 5**: Advanced analytics (claim recurrence, heatmap animations)
- **Phase 6**: Polish & optimization (React Query, virtualization, dark mode)

See [FRONTEND_ARCHITECTURE_PLAN.md](docs/FRONTEND_ARCHITECTURE_PLAN.md) for full roadmap.

---

## 📝 Documentation Workflow for AI Sessions

### When Working on Any Feature/Bug/Test:

1. **ALWAYS update [CHANGELOG.md](CHANGELOG.md)** with:
   - Timestamp (format: `## YYYY-MM-DD HH:MM`)
   - Feature/bug name with status emoji (✅ 🔨 🐞 ⚠️)
   - What was changed (bullet points)
   - Code references using markdown links: `[file.py](path/to/file.py:line)`
   - Test results if applicable

2. **ALWAYS make organized, understandable commits** if:
   - Feature/bug name prefix
   - What was changed (bullet points)
   - why it was changed if applicable

3. **Update this file (claude.md)** if:
   - Project structure changes (new folders, major refactors)
   - New major features are completed (update "Current Implementation Status")
   - Documentation references change
   - New common tasks are established

4. **Update relevant docs/** files if:
   - API endpoints change → Update [API.md](docs/API.md)
   - Architecture changes → Update [ARCHITECTURE.md](docs/ARCHITECTURE.md)
   - New setup steps → Update [SETUP.md](docs/SETUP.md)
   - Test patterns change → Update [TESTING.md](docs/TESTING.md)

### Changelog Entry Format

```markdown
## YYYY-MM-DD HH:MM

**Feature Name** ✅ / 🔨 / 🐞 / ⚠️

### What Changed
- Implemented X in [file.py](path/to/file.py:line)
- Fixed Y by modifying Z
- Added tests in [test_file.py](path/to/test_file.py)

### Test Results
- X tests passing
- Issues: [if any]

**Code References:**
- Main file: [file.py](path/to/file.py)
- Tests: [test_file.py](path/to/test_file.py)
```

### Status Emojis
- ✅ Complete
- 🔨 In Progress
- 🐞 Bug Fix
- ⚠️ Partial/Blocked

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

# Fact-checking (Optional)
GOOGLE_FACT_CHECK_API_KEY=...
CLAIMBUSTER_API_KEY=...
```

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

### AI Assistant Workflow
- **DO NOT push commits automatically** - Always wait for explicit user approval before pushing to remote
- Stage changes and prepare commits, but let the user decide when to push
- **Organize commits logically** - Group related changes into well-structured commits with clear messages
- Commit locally but never push without explicit user approval
- **ALWAYS maintain local-container parity** - See [Local-Container Parity](#-local-container-parity-critical) section for details
- **After ANY migration operation** - Immediately sync migration files between container and local filesystem

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

---

## 📞 Quick References

- **Interactive API Docs**: http://localhost:8000/docs
- **Frontend Dev Server**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Backend Container**: `news_backend`
- **Database Container**: `news_db`

---

**Last Updated**: 2025-10-08
**Status**: Phase 3 Complete + Deployment Ready (234 tests passing: 127 backend + 107 frontend ✅)
**Maintained by**: AI assistants working on Pulse
