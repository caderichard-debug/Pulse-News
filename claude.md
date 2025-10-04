# Pulse Development Changelog

This file tracks significant changes, decisions, and progress throughout development.

---

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

**Next Steps** 🧠
- Phase 3: Home Feed & Article Analysis (feed page, article detail, coverage comparison)
