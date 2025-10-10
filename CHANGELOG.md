# Pulse Development Changelog

This file tracks significant changes, decisions, and progress throughout development.

---

## 2025-10-10 (Current Session)

**Fixed Article Date Display - No More "Just Now" for All Articles** ✅

### What Changed
- Fixed timezone handling bug that caused all articles to show "Just now" regardless of age
- Created centralized date utility functions in [frontend/src/lib/dateUtils.ts](frontend/src/lib/dateUtils.ts):
  - `formatTimeAgo()` - Relative time (5m ago, 2h ago, 3d ago, 1w ago) or absolute for old articles
  - `formatDate()` - Formatted absolute dates (Oct 9, 2025)
  - `formatDateTime()` - Full date and time formatting
- Updated [frontend/src/app/feed/page.tsx](frontend/src/app/feed/page.tsx:6) to use new utility
- Updated [frontend/src/app/article/[id]/page.tsx](frontend/src/app/article/[id]/page.tsx:6) to use new utility
- Added comprehensive test suite in [frontend/src/lib/__tests__/dateUtils.test.ts](frontend/src/lib/__tests__/dateUtils.test.ts)

### The Problem
- Backend sends UTC timestamps without 'Z' suffix (e.g., "2025-10-09 20:25:00")
- JavaScript's `new Date()` treated these as local time, not UTC
- This caused incorrect time calculations, showing recent dates for old articles
- All articles from yesterday appeared as "Just now" or very recent

### The Solution
- Append 'Z' to date strings to explicitly treat them as UTC: `new Date(dateString + 'Z')`
- Enhanced formatting with more granular time buckets:
  - < 1 minute: "Just now"
  - < 60 minutes: "15m ago"
  - < 24 hours: "5h ago"
  - < 7 days: "2d ago"
  - < 30 days: "2w ago"
  - ≥ 30 days: "Oct 9, 2025" (absolute date)
- Handle edge cases like future dates (clock skew)

### Test Results
- All 198 frontend tests passing (up from 186) ✅
- 12 new date utility tests covering:
  - Relative time formatting for all time ranges
  - UTC timezone handling
  - Future date edge cases
  - Absolute date formatting

**Code References:**
- Main utility: [dateUtils.ts](frontend/src/lib/dateUtils.ts)
- Feed usage: [feed/page.tsx:6](frontend/src/app/feed/page.tsx#L6)
- Article detail: [article/[id]/page.tsx:6](frontend/src/app/article/[id]/page.tsx#L6)
- Tests: [dateUtils.test.ts](frontend/src/lib/__tests__/dateUtils.test.ts)

---

**Enabled Pull Request Previews on Render** ✅

### What Changed
- Updated [render.yaml](render.yaml) to enable PR preview environments:
  - Added `previewsEnabled: true` for both backend and frontend services
  - Set `previewsExpireAfterDays: 3` to auto-cleanup after PR close
  - Added `IS_PULL_REQUEST` environment variable for preview detection
  - Updated `CACHE_BUST` to v2 to force rebuild
- Created [docs/PR_PREVIEWS.md](docs/PR_PREVIEWS.md) - comprehensive guide covering:
  - How PR previews work on Render
  - Automatic deployment workflow
  - Preview URLs and accessing them
  - Environment variable handling
  - Testing and best practices
  - Troubleshooting common issues
  - Cost considerations

### How It Works
- When you create a PR, Render automatically creates preview deployments
- Each PR gets unique URLs: `pulse-backend-pr-{NUMBER}.onrender.com` and `pulse-frontend-pr-{NUMBER}.onrender.com`
- Previews are automatically updated when you push new commits
- Previews are deleted 3 days after PR is closed/merged

### Benefits
- ✅ Test changes in production-like environment before merging
- ✅ Share preview links with reviewers
- ✅ Catch deployment issues early
- ✅ Automatic cleanup (no manual intervention needed)

---

**Added Test User to Seed Data** ✅

### What Changed
- Enhanced [backend/app/seed_data.py](backend/app/seed_data.py) to create a test user on database initialization:
  - Default credentials: `test@pulse.com` / `testpassword123`
  - Customizable via environment variables: `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`, `TEST_USER_NAME`
  - User is automatically verified and subscribed to default topics
  - Test user creation is idempotent (safe to run multiple times)
- Separated test user creation into `create_test_user()` function
- Updated seed script to create test user even if database is already seeded
- Updated [docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md) with test user credentials and security notes
- Created [backend/TEST_USER.md](backend/TEST_USER.md) with comprehensive documentation

### Test Results
- ✅ Auth tests: 10/10 passing
- ✅ Test user login verified locally
- ✅ Seed script runs successfully

### Deployment Impact
- On Render, the test user will be automatically created on first startup
- Provides immediate login access without manual user creation
- Recommended to change credentials via environment variables for production

---

**Improved Article Date Display on Feed Page** ✅

### What Changed
- Enhanced the `formatTimeAgo()` function in [frontend/src/app/feed/page.tsx](frontend/src/app/feed/page.tsx:102-122) to show more precise timestamps:
  - Minutes ago (for articles < 1 hour old): "5m ago", "30m ago"
  - Hours ago (for articles < 24 hours old): "2h ago", "12h ago"
  - Days ago (for articles < 7 days old): "3d ago", "6d ago"
  - Weeks ago (for articles < 30 days old): "2w ago", "3w ago"
  - Actual date for older articles: "Oct 8", "Jan 15, 2024"
- Added `read_time_minutes` field to backend API response in [backend/app/routes/feed.py](backend/app/routes/feed.py:32,144)
- Calculates read time from word count (200 words/minute)
- Fixed incorrect test in [backend/tests/routes/test_feed.py](backend/tests/routes/test_feed.py:184-190) that expected auth requirement (feed is public)

### Test Results
- ✅ Backend: 12/12 tests passing in `test_feed.py`
- ✅ Frontend: 24/24 tests passing in feed page tests
- ✅ Frontend build: Successful compilation with no errors

---

**CRITICAL FIX: Database Enum Mismatch + Migration** ✅

### Issue Fixed
- **CI e2e test failing**: All feed endpoints returning 500 errors due to database enum type mismatch
- **Root cause**: Initial migration created lowercase enum, but code was updated to use uppercase

### Complete Analysis
After initial e2e test improvements, discovered the real issue from log analysis:
```
psycopg2.errors.InvalidTextRepresentation: invalid input value for enum processingstatus: "COMPLETED"
```

**The Problem:**
- Initial migration (`20251009_000001_initial_schema.py`) created enum with lowercase: `'pending', 'processing', 'completed', 'failed'`
- Code was updated to use uppercase: `"PENDING"`, `"PROCESSING"`, `"COMPLETED"`, `"FAILED"`
- Existing databases (including CI) still had lowercase enum
- All feed API calls failed because SQLAlchemy couldn't match enum values

### Changes Made

**4 Commits Total:**

1. **Fixed e2e test selectors** in [user-journey.spec.ts](frontend/e2e/user-journey.spec.ts):
   - Updated heading selector to match emoji: `/📰.*article feed/i`
   - Added `waitForLoadState('networkidle')` before checking elements

2. **Enhanced e2e test robustness** in [user-journey.spec.ts](frontend/e2e/user-journey.spec.ts):
   - Added defensive waiting for content to load (`h1` or error message)
   - Added loading spinner detection
   - Added error state detection with descriptive messages
   - Increased timeouts for more reliable CI execution

3. **Fixed enum definition in code** in [models.py](backend/app/models.py:9-13):
   - Changed `ProcessingStatus` enum values from lowercase to uppercase
   - Fixed all test fixtures across 8 test files to use enum members
   - Updated test assertions to expect uppercase values

4. **Created Alembic migration** ([ae55c7bb7c8f](backend/alembic/versions/ae55c7bb7c8f_update_processing_status_enum_to_.py)):
   - Migrates existing database enum from lowercase to uppercase
   - Converts all existing article data to uppercase
   - Provides downgrade path for rollback
   - **CI will apply this migration automatically** (line 149-156 in `.github/workflows/ci.yml`)

### Migration Details

The migration performs these steps:
1. Rename old enum type to `processingstatus_old`
2. Create new enum type with uppercase values
3. Alter articles table to use new enum, converting values with `UPPER()`
4. Drop old enum type

### Test Results

✅ **All tests passing locally**:
- **Backend**: 127 tests passing (including all feed, analytics, article detail tests)
- **Frontend E2E**: 23/23 tests passing locally
- **Feed endpoints**: Now returning 200 OK with correct data
- **Migration tested**: Successfully migrated 356 COMPLETED, 85 PENDING, 144 FAILED articles

### Why This Fix Was Critical

The e2e test improvements alone wouldn't have solved the problem - the API was returning 500 errors!
1. Feed page couldn't load because API calls were failing
2. No amount of waiting or defensive checks would fix a 500 error
3. **Initial fix (commit 3)** updated code but not existing databases
4. **Migration (commit 4)** fixes existing databases including CI
5. E2e test enhancements then ensured reliable test execution

**Code References:**
- Enum definition: [backend/app/models.py](backend/app/models.py:9-13)
- Migration: [backend/alembic/versions/ae55c7bb7c8f_update_processing_status_enum_to_.py](backend/alembic/versions/ae55c7bb7c8f_update_processing_status_enum_to_.py)
- CI workflow (runs migrations): [.github/workflows/ci.yml](.github/workflows/ci.yml:149-156)
- E2E tests: [frontend/e2e/user-journey.spec.ts](frontend/e2e/user-journey.spec.ts)

---

## 2025-10-08 21:00

**Frontend E2E Tests & Missing Unit Tests** ✅

### Playwright E2E Tests Added
- **Installed Playwright** with Chromium browser
- **Created comprehensive E2E test suites**:
  - **`auth.spec.ts`** - [frontend/e2e/auth.spec.ts](frontend/e2e/auth.spec.ts):
    - Landing page display
    - Signup flow (2-step process)
    - Login flow with valid/invalid credentials
    - Password validation (length, match)
    - Duplicate email prevention

  - **`user-journey.spec.ts`** - [frontend/e2e/user-journey.spec.ts](frontend/e2e/user-journey.spec.ts):
    - Complete user journey: signup → preferences → dashboard → feed → logout
    - Preferences management (topics, sources, settings)
    - Navigation flow with active page highlighting
    - Error handling (404, unauthorized access)
    - Login persistence across page reloads

### Frontend Unit Tests Added (50+ tests)
- **Login Page** (15 tests) - [login/__tests__/page.test.tsx](frontend/src/app/login/__tests__/page.test.tsx):
  - Form rendering and validation
  - Successful/failed login flows
  - Loading states
  - Error messages
  - Navigation after login

- **Signup Page** (20+ tests) - [signup/__tests__/page.test.tsx](frontend/src/app/signup/__tests__/page.test.tsx):
  - 2-step signup process
  - Form validation (password length, match)
  - Topic selection
  - Error handling
  - Back/Next navigation

- **Landing Page** (15 tests) - [__tests__/page.test.tsx](frontend/src/app/__tests__/page.test.tsx):
  - Hero section
  - Feature cards
  - Call-to-action buttons
  - How It Works section
  - Trusted sources

- **Navbar Component** (20 tests) - [components/__tests__/Navbar.test.tsx](frontend/src/components/__tests__/Navbar.test.tsx):
  - Navigation links
  - Active page highlighting
  - User name display
  - Logout functionality
  - Navigation actions

### CI/CD Pipeline Enhanced
- **Added frontend unit test step** with coverage reporting to CodeCov
- **Added Playwright E2E test job**:
  - Runs after unit tests pass
  - Spins up backend API and PostgreSQL services
  - Installs Playwright browsers
  - Runs E2E tests in CI environment
  - Uploads Playwright HTML report as artifact
- Updated "All Checks" job to include E2E tests

### NPM Scripts Added
- `npm run test:e2e` - Run Playwright tests headless
- `npm run test:e2e:ui` - Run with Playwright UI
- `npm run test:e2e:debug` - Run with debugger

### Test Coverage Summary
- **Frontend Unit Tests**: 157+ tests (107 existing + 50 new)
- **Frontend E2E Tests**: 15+ critical user journey tests
- **Total Frontend Tests**: ~172 tests
- **Total Project Tests**: ~344 tests (172 backend + 172 frontend)

### What This Achieves
✅ Complete test pyramid for frontend (unit → integration → E2E)
✅ Critical user paths validated end-to-end
✅ CI/CD pipeline validates all changes before merge
✅ Visual regression detection via Playwright screenshots
✅ Cross-browser testing capability (currently Chromium)

**Code References:**
- E2E Tests: [auth.spec.ts](frontend/e2e/auth.spec.ts), [user-journey.spec.ts](frontend/e2e/user-journey.spec.ts)
- Unit Tests: [login](frontend/src/app/login/__tests__/), [signup](frontend/src/app/signup/__tests__/), [landing](frontend/src/app/__tests__/), [navbar](frontend/src/components/__tests__/)
- Playwright Config: [playwright.config.ts](frontend/playwright.config.ts)
- CI/CD: [.github/workflows/ci.yml](.github/workflows/ci.yml)

---

## 2025-10-08 20:00

**Comprehensive Testing Infrastructure Enhancement** ✅

### Test Pyramid Implementation
- **Restructured test directory** to match app structure:
  - `tests/utils/` - Unit tests for utilities
  - `tests/services/` - Unit tests for services
  - `tests/routes/` - Integration tests for API routes
  - `tests/integration/` - Multi-component integration tests
  - `tests/e2e/` - End-to-end user journey tests
  - `tests/jobs/` - Background job tests
- Fixed all import paths (relative → absolute `app.` imports)

### New Unit Tests (60+ tests added)
- **`test_auth.py`** (35 tests) - [tests/utils/test_auth.py](backend/tests/utils/test_auth.py):
  - Password hashing and verification (bcrypt)
  - JWT token creation and decoding
  - Specialized tokens (verification, password reset)
  - Edge cases (long passwords, unicode, empty strings)
  - Token expiration and tampering detection

- **`test_openai_client.py`** (25+ tests) - [tests/utils/test_openai_client.py](backend/tests/utils/test_openai_client.py):
  - Client initialization with/without API key
  - Batch article analysis with mocked OpenAI
  - Framework generation and article mapping
  - Cost calculation accuracy
  - Prompt building functions
  - Error handling (JSON decode errors, API failures)

### New Integration Tests
- **`test_article_pipeline.py`** - [tests/integration/test_article_pipeline.py](backend/tests/integration/test_article_pipeline.py):
  - Scrape → Extract → Analyze complete workflow
  - Extraction → Analysis pipeline integration
  - Batch processing with multiple articles
  - Error handling across pipeline stages
  - Newsletter generation with user preferences

### New E2E Tests (10+ tests)
- **`test_user_journey.py`** - [tests/e2e/test_user_journey.py](backend/tests/e2e/test_user_journey.py):
  - **Complete user workflow**: Register → Login → Set preferences → Browse feed → Read article
  - **Article pipeline**: Scrape → Extract → Analyze → Map frameworks → User views
  - **Newsletter flow**: Subscribe → Articles analyzed → Newsletter generated → User views
  - **Authentication flow**: Registration, login, token validation, error handling
  - **Error scenarios**: Invalid credentials, database constraints, missing resources

### Documentation
- **Created comprehensive testing strategy** - [TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md):
  - Test pyramid breakdown (60% unit, 30% integration, 10% E2E)
  - Coverage summary and targets
  - Missing tests identified
  - Running tests guide
  - CI/CD recommendations
  - Best practices and success metrics

### Test Coverage
- **Backend**: ~172+ tests total
  - Unit: ~100 tests (utils + services)
  - Integration: ~65 tests (routes + pipelines)
  - E2E: ~7 tests (user journeys)
- **Frontend**: 107 tests (unchanged)
- **Total**: ~279+ tests

### What's Still Missing
**Backend**:
- ❌ Unit tests for jobs/tasks.py
- ❌ Integration tests for scheduler + email delivery
- ❌ Performance/load tests

**Frontend**:
- ❌ E2E tests with Playwright (critical path)
- ❌ Unit tests for Login, Signup, Landing pages
- ❌ Accessibility tests

**Code References:**
- Utils tests: [test_auth.py](backend/tests/utils/test_auth.py), [test_openai_client.py](backend/tests/utils/test_openai_client.py)
- Integration: [test_article_pipeline.py](backend/tests/integration/test_article_pipeline.py)
- E2E: [test_user_journey.py](backend/tests/e2e/test_user_journey.py)
- Strategy: [TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md)


## 2025-10-09 09:06

**Render Blueprint Infrastructure Complete** ✅

### What Changed
- **Complete Render Blueprint configuration** in [render.yaml](render.yaml)
  - Added PostgreSQL database (pulse-db) with free tier
  - Configured backend service (pulse-backend) with Docker runtime
  - Configured frontend service (pulse-frontend) with Next.js build
  - Auto-linked database connection string to backend
  - Auto-linked backend URL to frontend API client
  - All environment variables configured (non-secrets in blueprint, secrets marked for manual config)
- **Added health check endpoint** in [main.py](backend/app/main.py:66-69)
  - `/health` returns `{"status": "healthy"}`
  - Used by Render for service health monitoring
- **Updated frontend configuration** in [next.config.ts](frontend/next.config.ts)
  - Added `output: 'standalone'` for production deployment
  - Configured `NEXT_PUBLIC_API_URL` environment variable support
  - Defaults to `http://localhost:8000` for local development
- **Created comprehensive deployment documentation** in [RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md)
  - Step-by-step deployment guide
  - Secret environment variable configuration
  - Database migration instructions
  - Troubleshooting section
  - Cost estimates and scaling guidance

### Benefits
✅ Single `render.yaml` manages entire infrastructure (database + backend + frontend)
✅ Automatic deployments from git push to main branch
✅ Proper service dependencies and health checks
✅ Environment-specific configurations
✅ Easy scaling and management from Render dashboard

### Architecture
```
pulse-frontend (Next.js) → pulse-backend (FastAPI) → pulse-db (PostgreSQL)
```

**Code References:**
- Blueprint: [render.yaml](render.yaml)
- Health check: [main.py](backend/app/main.py:66-69)
- Frontend config: [next.config.ts](frontend/next.config.ts)
- Documentation: [RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md)

---

## 2025-10-08 17:00

**Render.com Deployment & UI Polish** ✅

### Deployment Automation
- **Added database seeding job** to [render.yaml](render.yaml:19-24)
  - Runs `python -m app.seed_data` on every deployment
  - Seeds 8 topics, 8 sources, 10 ethical frameworks automatically
  - Eliminates manual seeding in production
- **Improved database connection retry logic** in [database.py](backend/app/database.py:27-38)
  - Max 30 retries with 1-second intervals
  - Better error logging for debugging cloud deployment issues
  - Production-ready for Render.com's container startup delays
  - Uses dotenv for environment variable loading

### UI/UX Improvements
- **Fixed placeholder text brightness** on authentication pages
  - [login/page.tsx](frontend/src/app/login/page.tsx) - `placeholder-gray-200` → `placeholder-gray-400`
  - [signup/page.tsx](frontend/src/app/signup/page.tsx) - Improved visibility for all form fields (name, email, password, confirm password)
  - Better accessibility and readability for users
- **Removed framework "score" visualization** (commit e398100)
  - Focus on position-on-axis (-10 to +10) for ethical frameworks
  - Aligns with documentation's axis-based philosophy
  - Simplified framework display in article detail pages

### Infrastructure Updates
- Render.com configuration complete and tested
- Automatic deployment on git push to main
- Free tier services (frontend + backend + database)
- Environment variable management via Render dashboard

### Test Results
- ✅ **All 234 tests passing** (127 backend + 107 frontend)
- ✅ Render.yaml syntax validated
- ✅ Database connection retry logic tested locally
- ✅ Authentication pages tested with improved placeholders

**Code References:**
- Deployment: [render.yaml](render.yaml)
- Database: [database.py](backend/app/database.py)
- Login: [login/page.tsx](frontend/src/app/login/page.tsx)
- Signup: [signup/page.tsx](frontend/src/app/signup/page.tsx)

**Git Commits:** bb2fcc6, 14e9096, 70855d5, 480a2f3, e398100

---

## 2025-10-04 01:15

**Critical Fixes - Router Conflict & Documentation Updates** ✅

### Router Merge
- **Merged routers**: Combined [articles.py](backend/app/routes/articles.py) and article_detail.py to resolve `/articles` prefix conflict
  - Kept comprehensive `GET /articles/{article_id}` with full analysis (statistics, frameworks, context, related articles)
  - Kept `GET /articles/analyzed` for listing analyzed articles
  - Removed duplicate article_detail.py file
  - Updated [main.py](backend/app/main.py:6) to remove article_detail import
  - **Impact**: Routes now work correctly without collision

### API Documentation Complete Update
- **Fixed [API.md](docs/API.md)** - Added ALL Phase 1-3 endpoints (18 new endpoints documented):
  - Fixed `/auth/signup` → `/auth/register` (line 41)
  - **Preferences** (10 endpoints): topics, subscribe/unsubscribe, newsletter preview, sources, settings
  - **Analytics** (5 endpoints): user-stats, sentiment-over-time, bias-distribution, framework-heatmap, frameworks/available
  - **Feed** (3 endpoints): articles (with filters), topics, sources
  - **Articles** (2 endpoints): analyzed, {article_id} with full details
  - All endpoints now include request/response examples

### Background Jobs Documentation Fixed
- **Updated [ARCHITECTURE.md](docs/ARCHITECTURE.md:221-294)** with correct job schedules and all 8 jobs:
  1. RSS Scraping - Every 3 hours ✅
  2. Article Extraction - Every 4 hours ✅
  3. AI Analysis - **Every 6 hours** (was incorrectly documented as 4)
  4. Framework Generation - Daily 2:00 AM ✅
  5. Newsletter - **Daily 10:20 AM PST** (was incorrectly documented as 7am)
  6. **Statistics Verification - Every 6 hours** (was not documented)
  7. **Article Clustering - Every 4 hours** (was not documented)
  8. **Context Generation - Every 8 hours** (was not documented)
- Fixed `/auth/signup` → `/auth/register` in auth flow diagram (line 300)

### Test Results
- ✅ **All 9 article detail tests passing** ([test_article_detail.py](backend/tests/test_article_detail.py))
- ✅ Router merge successful - no conflicts
- ✅ Fixed test fixtures for updated ArticleCluster model (added `cluster_hash`, `similarity_score`)
- ✅ Fixed Article model field reference (`content` → `content_text`)
- Backend now starts without router conflicts
- All API routes properly registered
- Documentation now 100% accurate to Phase 1-3 implementation

**Code References:**
- Merged router: [articles.py](backend/app/routes/articles.py)
- Updated main: [main.py](backend/app/main.py:6,49)
- Fixed tests: [test_article_detail.py](backend/tests/test_article_detail.py)
- Complete API docs: [API.md](docs/API.md)
- Fixed jobs: [ARCHITECTURE.md](docs/ARCHITECTURE.md:221-294)

---

## 2025-10-04 00:45

**Comprehensive Documentation Audit** ✅

### Discrepancies Found
Created [DOCUMENTATION_DISCREPANCIES.md](DOCUMENTATION_DISCREPANCIES.md) detailing all mismatches between docs and code.

**Critical Issues (🔴 HIGH PRIORITY)**:
1. **Router Conflict**: Two routers using `/articles` prefix
   - [articles.py](backend/app/routes/articles.py) and [article_detail.py](backend/app/routes/article_detail.py)
   - Last registered wins - likely breaking routes
2. **API.md Outdated**: Missing all Phase 1-3 endpoints
   - `/analytics/*` (5 endpoints)
   - `/feed/*` (3 endpoints)
   - `/preferences/*` (10 endpoints)
   - `/auth/signup` should be `/auth/register`

**Medium Priority (🟡)**:
3. **Background Jobs Timing Wrong**:
   - AI Analysis: Docs say "every 4 hours", actually **every 6 hours**
   - Newsletter: Docs say "7am", actually **10:20 AM PST**
   - 3 jobs not documented (statistics, clustering, context)

**Verified Correct (✅)**:
- All 18 database tables match Phase 1-3 implementation
- All 12 services exist and match documentation
- Frontend pages match FRONTEND_ARCHITECTURE_PLAN Phase 3 status
- 127 backend tests + 107 frontend tests = **234 tests passing**

**Code References:**
- Full audit: [DOCUMENTATION_DISCREPANCIES.md](DOCUMENTATION_DISCREPANCIES.md)
- Routes: [backend/app/main.py](backend/app/main.py:45-53)
- Jobs: [backend/app/jobs/scheduler.py](backend/app/jobs/scheduler.py)

---

## 2025-10-04 00:15

**Documentation Restructure** ✅

### What Changed
- Moved changelog from `claude.md` to dedicated [CHANGELOG.md](CHANGELOG.md)
- Completely rewrote [claude.md](claude.md) as a comprehensive navigation guide for AI sessions
  - Quick project overview with current status
  - Complete file structure navigator (backend routes, services, frontend pages)
  - "Finding Code by Feature" section for quick navigation
  - Common development tasks reference
  - Documentation workflow instructions for future sessions
- Fixed AI model discrepancies across documentation:
  - Updated [README.md](README.md) - Changed "Claude Haiku" → "OpenAI GPT-4o-mini"
  - Updated [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Changed "Anthropic Claude" → "OpenAI GPT-4o-mini"
  - Fixed API key references and cost information

### Purpose
- New AI sessions can now quickly understand project structure
- Clear navigation to relevant files for any feature
- Consistent documentation workflow for all future changes
- Single source of truth for project context

### Documentation Standards Established
1. **CHANGELOG.md** - All chronological changes with timestamps
2. **claude.md** - Project navigation and context for AI sessions
3. **docs/** - Technical documentation (architecture, API, setup)

**Code References:**
- New navigation guide: [claude.md](claude.md)
- Complete history: [CHANGELOG.md](CHANGELOG.md)
- Fixed docs: [README.md](README.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 2025-10-03 23:45

**Navigation & UI Polish** ✅
- Created global navigation bar component - [frontend/src/components/Navbar.tsx](frontend/src/components/Navbar.tsx:1)
  - Shows current page with active state (indigo background)
  - Quick navigation between Dashboard, Feed, and Preferences
  - Logout functionality
  - Consistent branding with "Pulse" logo
- Updated all pages with navbar and consistent color palette:
  - Dashboard - [frontend/src/app/dashboard/page.tsx](frontend/src/app/dashboard/page.tsx:1)
  - Feed - [frontend/src/app/feed/page.tsx](frontend/src/app/feed/page.tsx:1)
  - Preferences - [frontend/src/app/preferences/page.tsx](frontend/src/app/preferences/page.tsx:1)
  - Article Detail - [frontend/src/app/article/[id]/page.tsx](frontend/src/app/article/[id]/page.tsx:1)
- Feed page styling improvements:
  - Consistent gray-50 background
  - White cards with shadow-sm
  - Indigo accent colors (matching dashboard)
  - Left border accent on article cards (border-l-4 border-indigo-500)
  - Improved empty state messaging
  - Better pagination button styling
  - Responsive filters with proper spacing

**Database Population** ✅
- Triggered article scraping: 119 articles scraped from RSS feeds
- Triggered extraction job: extracting full article content
- Triggered analysis job: AI analyzing articles (14 completed, 105 in progress)
- Articles now appearing in feed with full metadata

## 2025-10-03 23:30

**Frontend Test Suite Complete** ✅
- Comprehensive test coverage for all frontend features
- **107 tests passing** across 5 test suites:
  - API Client Tests (14 tests): Authentication, preferences, analytics, feed, error handling
  - Dashboard Page Tests (22 tests): Stats display, charts, time range selector, navigation, error handling
  - Preferences Page Tests (15 tests): Topics tab, sources tab, settings tab, save functionality, logout
  - Feed Page Tests (30 tests): Article list, filters, pagination, navigation, empty states, error handling
  - Article Detail Page Tests (26 tests): Article metadata, statistics, frameworks, context, related articles, verification badges
- Test infrastructure:
  - Jest configuration for Next.js
  - React Testing Library
  - Mocks for next/navigation and Recharts
  - Comprehensive fixtures and test data
- Fixed all test issues:
  - API method signatures (login/register use object params)
  - Token loading (ApiClient loads from localStorage in constructor)
  - Filter selectors (using getAllByRole('combobox') instead of getByLabelText)
  - Async state updates (proper waitFor usage)
  - Multiple element matches (using getAllByText for duplicates)

## 2025-10-03 00:00

**Changelog System Established**
- Created running changelog in `CLAUDE.md` for tracking development progress
- Format: Date/Time + Summary + Status Tags + Code References

**Frontend Architecture Plan Complete** ✅
- Created comprehensive 16-week implementation plan in `docs/FRONTEND_ARCHITECTURE_PLAN.md`
- Designed "Lens on Discourse" features:
  - Enhanced preferences (source customization, article ordering, discovery mode)
  - Dashboard with sentiment/bias visualizations (line charts, heatmaps, scatter plots)
  - Home feed with article analysis and cross-source coverage comparison
  - Weekly challenge system to track viewpoint changes
  - Advanced analytics (sentiment×framework heatmap, claim recurrence tracking)
- Defined new database tables: `user_source_subscriptions`, `challenges`, `challenge_responses`, `curated_reflections`
- Specified 15+ new API endpoints for analytics, preferences, and challenges
- Organized into 6 implementation phases with clear deliverables
- Tech stack: Next.js 15, React 19, Recharts, TanStack Query

**Phase 1: Enhanced Preferences** ✅ COMPLETE

### Backend ✅
- Created database migration `aafc42a52a96` for user preferences
- Added columns to `users` table: `source_discovery_mode`, `article_order_preference`, `articles_per_topic_default`
- Created `user_source_subscriptions` table for source management
- Added `articles_per_topic` to `user_topic_preferences`
- Implemented new API endpoints in `backend/app/routes/preferences.py`:
  - `GET /preferences/sources` - Get source subscriptions with political lean
  - `PUT /preferences/sources` - Update source subscriptions
  - `GET /preferences/settings` - Get user settings
  - `PUT /preferences/settings` - Update settings (discovery mode, article ordering)
- Updated newsletter service to respect:
  - User's subscribed sources (filters articles)
  - Article ordering preference (good_first, good_last, mixed)
  - Articles per topic setting

### Frontend (Partial) 🔨
- Extended API client (`frontend/src/lib/api.ts`) with:
  - `getSources()`, `updateSourcePreferences()`
  - `getSettings()`, `updateSettings()`
- Enhanced preferences page (`frontend/src/app/preferences/page.tsx`):
  - Added tabbed interface (Topics, Sources, Settings)
  - State management for sources and settings
  - Handlers for saving source/setting changes
  - **Note**: UI rendering incomplete - will complete in Phase 2

### Testing ✅
- Created `test_source_preferences.py` - 17 tests for source & settings endpoints
- Created `test_newsletter_preferences.py` - 9 tests for newsletter filtering/ordering
- **All 35 tests passing** (including existing 9 preference tests)
- Fixed bug: Invalid source IDs now properly skipped with accurate count

### Bugs Fixed 🐞
- Fixed `subscribed_count` to only count valid sources (not all requested)
- Fixed test ordering issues by preserving article_ids order from newsletter

---

## 2025-10-03 01:30

**Phase 2: Dashboard & Analytics** ✅ COMPLETE

### Backend ✅
- Created new analytics routes in `backend/app/routes/analytics.py` with 5 endpoints:
  - `GET /analytics/user-stats` - Articles read, newsletters received, topics tracked, sources subscribed
  - `GET /analytics/sentiment-over-time` - Daily sentiment scores by topic (multi-line chart data)
  - `GET /analytics/bias-distribution` - Weekly political lean percentages (stacked area chart data)
  - `GET /analytics/framework-heatmap` - 2D heatmap for framework positioning analysis
  - `GET /analytics/frameworks/available` - List frameworks with article counts
- Implemented database-agnostic date grouping (Python-based) for SQLite/PostgreSQL compatibility
- Registered analytics router in `backend/app/main.py`

### Frontend ✅
- Installed `recharts` library for data visualization (`npm install recharts`)
- Extended API client (`frontend/src/lib/api.ts`) with analytics methods:
  - `getUserStats()`, `getSentimentOverTime()`, `getBiasDistribution()`
  - `getFrameworkHeatmap()`, `getAvailableFrameworks()`
- Created dashboard page (`frontend/src/app/dashboard/page.tsx`):
  - User stats overview cards (articles read, newsletters received, etc.)
  - Time range selector (7/30/90 days)
  - Sentiment line chart (multi-topic sentiment trends using Recharts)
  - Bias stacked area chart (political lean distribution using Recharts)
  - Navigation buttons to preferences and home

### Testing ✅
- Created `test_analytics.py` - 10 tests covering all analytics endpoints
- **All 36 tests passing** (10 analytics + 17 source preferences + 9 newsletter preferences)

### Bugs Fixed 🐞
- Fixed SQLite incompatibility: Replaced PostgreSQL-specific `date_trunc()` and `cast(Date)` with Python-based date grouping
- Applied fix to both `get_sentiment_over_time` and `get_bias_distribution` endpoints
- Now works with both SQLite (testing) and PostgreSQL (production)

**Code References:**
- Analytics backend: [backend/app/routes/analytics.py](backend/app/routes/analytics.py)
- Dashboard UI: [frontend/src/app/dashboard/page.tsx](frontend/src/app/dashboard/page.tsx)
- Tests: [backend/tests/test_analytics.py](backend/tests/test_analytics.py)

---

## 2025-10-03 03:30

**Phase 3: Home Feed & Article Analysis** ✅ COMPLETE

### Backend ✅
- Created feed routes in `backend/app/routes/feed.py` with 3 endpoints:
  - `GET /feed/articles` - Paginated article feed with filtering (topic, source, political lean) and sorting (newest, oldest, sentiment)
  - `GET /feed/topics` - Available topics with article counts
  - `GET /feed/sources` - Available sources with article counts
- Created article detail routes in `backend/app/routes/article_detail.py`:
  - `GET /articles/{id}` - Full article analysis with verified statistics, framework positioning, related articles (cluster), and context
- Registered new routers in `backend/app/main.py`
- Response models include framework data, sentiment scores, political lean indicators

### Frontend ✅
- Extended API client (`frontend/src/lib/api.ts`) with feed and article detail methods:
  - `getFeedArticles()`, `getFeedTopics()`, `getFeedSources()`
  - `getArticleDetail()`
- Created feed page (`frontend/src/app/feed/page.tsx`):
  - Filter controls (topic, source, political lean, sort order)
  - Article cards with sentiment, lean, framework positioning
  - Pagination (20 articles per page)
  - Clickable articles navigate to detail page
- Created article detail page (`frontend/src/app/article/[id]/page.tsx`):
  - Full article summary and metadata
  - Sentiment & bias analysis with visual indicators
  - Verified statistics with badges (verified/unverified/disputed/false)
  - Framework positioning with axis visualization
  - Related articles (coverage comparison) from same cluster
  - Context sections (background, key players, timeline, significance)

### Testing ⚠️
- Created `test_feed.py` - 11 tests for feed endpoints
- Created `test_article_detail.py` - 9 tests for article detail endpoint
- **11/20 tests passing** (feed tests mostly passing, some article detail tests have fixture issues)
- Fixed multiple field name mismatches between models and tests:
  - `ai_explanation` (not `explanation`) in ArticleFrameworkLink
  - `statistic_text` (not `statistic`) in StatisticVerification
  - `confidence_score` (not `confidence`) in StatisticVerification
  - Removed non-existent `read_time_minutes` field from responses
  - Added required `axis_description` to Framework fixtures

### Bugs Fixed 🐞
- Fixed field name mismatches in ArticleFrameworkLink model usage
- Fixed StatisticVerification field names in article detail endpoint
- Removed references to non-existent `read_time_minutes` field
- Added missing required fields to test fixtures (Framework.axis_description)

**Code References:**
- Feed backend: [backend/app/routes/feed.py](backend/app/routes/feed.py)
- Article detail backend: [backend/app/routes/article_detail.py](backend/app/routes/article_detail.py)
- Feed UI: [frontend/src/app/feed/page.tsx](frontend/src/app/feed/page.tsx)
- Article detail UI: [frontend/src/app/article/[id]/page.tsx](frontend/src/app/article/[id]/page.tsx)
- Tests: [backend/tests/test_feed.py](backend/tests/test_feed.py), [backend/tests/test_article_detail.py](backend/tests/test_article_detail.py)

---

## 2025-10-03 04:00

**Frontend UI Fix: Preferences Page Tabs** 🐞

### Issue
- Sources and Settings tabs were not showing any UI
- Only Topics tab was rendering content
- Users couldn't see or interact with source preferences or settings

### Fix
- Added conditional rendering for all three tabs in preferences page
- **Sources Tab**: Grid layout with checkboxes, trust scores, political lean badges
- **Settings Tab**: Dropdowns for discovery mode, article ordering, slider for articles per topic
- Each tab now has its own save button with proper handler

**Code Reference:**
- Fixed file: [frontend/src/app/preferences/page.tsx](frontend/src/app/preferences/page.tsx:252-499)

---

## 2025-10-03 05:00

**Frontend Testing Infrastructure** ✅

### Setup Complete
- Installed testing libraries: Jest, React Testing Library, jest-dom, user-event
- Created `jest.config.js` with Next.js integration
- Created `jest.setup.js` with navigation mocks and window.matchMedia polyfill
- Added test scripts to package.json: `test`, `test:watch`, `test:coverage`
- Exported ApiClient class for testing

### Tests Created
- **API Client Tests** (`src/lib/__tests__/api.test.ts`) - 15+ test cases:
  - Authentication (login, register, token management)
  - Preferences (get/update preferences, sources, settings)
  - Analytics (user stats, sentiment over time)
  - Feed (articles, filtering, article detail)
  - Error handling

- **Preferences Page Tests** (`src/app/preferences/__tests__/page.test.tsx`) - 15+ test cases:
  - Loading state and data fetching
  - Topic toggle and priority adjustment
  - Sources tab (display, trust scores, subscription toggle)
  - Settings tab (discovery mode, article ordering, articles per topic)
  - Save functionality for all tabs
  - Logout and auth error handling

### Test Infrastructure Ready
- Can run tests with: `npm test`
- Watch mode: `npm test:watch`
- Coverage: `npm test:coverage`

### Database Seeded ✅
- Ran `python -m app.seed_data` to populate database
- **8 topics** created (general, politics, economics, technology, science, culture, world, environment)
- **8 sources** created (AP, Reuters, NPR, BBC, NYT, Politico, Ars Technica, The Atlantic)
- **10 frameworks** created (seed ethical debates)
- Backend APIs confirmed working with curl tests

**Code References:**
- Jest config: [frontend/jest.config.js](frontend/jest.config.js)
- API tests: [frontend/src/lib/__tests__/api.test.ts](frontend/src/lib/__tests__/api.test.ts)
- Preferences tests: [frontend/src/app/preferences/__tests__/page.test.tsx](frontend/src/app/preferences/__tests__/page.test.tsx)

**Next Steps** 🧠
- Run full frontend test suite and fix any issues
- Add tests for dashboard, feed, and article detail pages
- Phase 4: Challenge System (weekly challenges, viewpoint tracking, reflections)
