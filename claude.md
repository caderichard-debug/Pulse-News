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

**Next Steps** 🧠
- Phase 2: Dashboard & Analytics (sentiment graphs, bias charts, heatmaps)
