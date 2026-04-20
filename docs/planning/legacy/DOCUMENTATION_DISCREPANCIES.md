# Documentation vs. Code Discrepancies

**Generated**: 2025-10-04 00:30
**Updated**: 2025-10-04 01:15
**Status**: ✅ ALL CRITICAL ISSUES RESOLVED

---

## API Endpoint Discrepancies

### ✅ CORRECT - Routes Match Documentation

**Actual Implementation:**
- `/auth/register` (not `/auth/signup` as docs suggest)
- `/auth/login`
- `/auth/me`
- `/auth/verify-email`
- `/auth/logout`

**Documentation Issue**: ~~[API.md](docs/API.md) references `/auth/signup`~~ - **FIXED** to `/auth/register`

### ✅ New Routes - ALL DOCUMENTED

**Analytics** (`/analytics/*` prefix):
- `GET /analytics/user-stats` ✅
- `GET /analytics/sentiment-over-time` ✅
- `GET /analytics/bias-distribution` ✅
- `GET /analytics/framework-heatmap` ✅
- `GET /analytics/frameworks/available` ✅

**Feed** (`/feed/*` prefix):
- `GET /feed/articles` ✅
- `GET /feed/topics` ✅
- `GET /feed/sources` ✅

**Article Detail** (`/articles/*` prefix):
- `GET /articles/{id}` - Conflicts with existing articles.py router!

**Preferences** (`/preferences/*` prefix):
- `GET /preferences` ✅
- `PUT /preferences` ✅
- `GET /preferences/topics` ✅
- `POST /preferences/topics/{topic_id}/subscribe` ✅
- `POST /preferences/topics/{topic_id}/unsubscribe` ✅
- `GET /preferences/newsletter-preview` ✅
- `GET /preferences/sources` ✅
- `PUT /preferences/sources` ✅
- `GET /preferences/settings` ✅
- `PUT /preferences/settings` ✅

### ✅ ROUTER CONFLICT - RESOLVED

**Problem**: Two routers with same prefix `/articles` ~~FIXED~~
1. ~~[articles.py](backend/app/routes/articles.py)~~ - Merged into single router
2. ~~[article_detail.py](backend/app/routes/article_detail.py)~~ - **REMOVED**

**Solution Implemented** (2025-10-04 01:15):
- Merged both routers into [articles.py](backend/app/routes/articles.py)
- Routes now available:
  - `GET /articles/analyzed` - List analyzed articles
  - `GET /articles/{article_id}` - Full article detail with statistics, frameworks, context
- Removed article_detail.py file
- Updated [main.py](backend/app/main.py:6,49) to remove article_detail import
- **Impact**: Routes now work correctly without collision ✅

---

## Database Schema Discrepancies

### ✅ Tables Implemented vs. Documented

**All tables in models.py**:
1. `sources` ✅
2. `topics` ✅
3. `articles` ✅
4. `article_analysis` ✅
5. `frameworks` ✅
6. `users` ✅
7. `newsletters` ✅
8. `source_topics` (link table) ✅
9. `article_topics` (link table) ✅
10. `newsletter_articles` (link table) ✅
11. `article_frameworks` ✅
12. `user_topic_preferences` ✅
13. `user_source_subscriptions` ✅
14. `statistic_verifications` ✅
15. `article_clusters` ✅
16. `article_cluster_members` ✅
17. `article_context` ✅
18. `source_credibility_ratings` ✅

**Tables mentioned in FRONTEND_ARCHITECTURE_PLAN.md but NOT implemented**:
- ❌ `challenges` - Phase 4 feature (not yet implemented)
- ❌ `challenge_responses` - Phase 4 feature
- ❌ `challenge_articles` - Phase 4 feature
- ❌ `curated_reflections` - Phase 4 feature

**Status**: Schema matches Phase 1-3 implementation. Phase 4 tables not yet created (expected).

---

## Services Implementation vs. Documentation

### ✅ All Services Implemented

**Article Pipeline**:
- [rss_scraper.py](backend/app/services/rss_scraper.py) ✅
- [article_extractor.py](backend/app/services/article_extractor.py) ✅
- [ai_analyzer.py](backend/app/services/ai_analyzer.py) ✅
- [framework_generator.py](backend/app/services/framework_generator.py) ✅

**Statistics Verification V2**:
- [statistics_verifier.py](backend/app/services/statistics_verifier.py) ✅
- [source_tracer.py](backend/app/services/source_tracer.py) ✅
- [credibility_rater.py](backend/app/services/credibility_rater.py) ✅
- [fact_check_integrator.py](backend/app/services/fact_check_integrator.py) ✅

**Enhancement Services**:
- [article_clusterer.py](backend/app/services/article_clusterer.py) ✅
- [context_generator.py](backend/app/services/context_generator.py) ✅
- [newsletter_service.py](backend/app/services/newsletter_service.py) ✅

**All services match documentation** ✅

---

## Frontend Implementation vs. Plan

### ✅ Phases 1-3 Complete

**Implemented Pages**:
- [/](frontend/src/app/page.tsx) - Landing page ✅
- [/login](frontend/src/app/login/) ✅
- [/signup](frontend/src/app/signup/) ✅
- [/preferences](frontend/src/app/preferences/) - Phases 1 complete ✅
- [/dashboard](frontend/src/app/dashboard/) - Phase 2 complete ✅
- [/feed](frontend/src/app/feed/) - Phase 3 complete ✅
- [/article/[id]](frontend/src/app/article/[id]/) - Phase 3 complete ✅

**Components**:
- [Navbar.tsx](frontend/src/components/Navbar.tsx) - Global nav ✅

**Missing (Phase 4-6)**:
- ❌ `/challenge` - Weekly challenge page
- ❌ `/challenge/history` - Challenge history
- ❌ `/analytics` - Advanced analytics page (beyond dashboard)

**Status**: Matches FRONTEND_ARCHITECTURE_PLAN.md Phase 3 completion ✅

---

## Background Jobs

### ⚠️ Jobs Implementation - Discrepancies Found!

**Actual Jobs** ([tasks.py](backend/app/jobs/tasks.py) + [scheduler.py](backend/app/jobs/scheduler.py)):
1. `scrape_job` - Every 3 hours ✅
2. `extract_job` - Every 4 hours ✅
3. `analyze_job` - Every 6 hours ⚠️ (docs say "every 4 hours")
4. `framework_job` - Daily at 2:00 AM ✅
5. `newsletter_job` - Daily at 10:20 AM PST ⚠️ (docs say "7am")
6. `statistics_verification_job` - Every 6 hours ✅ (not documented!)
7. `article_clustering_job` - Every 4 hours ✅ (not documented!)
8. `context_generation_job` - Every 8 hours ✅ (not documented!)

**Documented Jobs** ([ARCHITECTURE.md](docs/ARCHITECTURE.md)):
- Scrape RSS (every 3 hours) ✅
- Extract Articles (every 4 hours) ✅
- AI Analysis ❌ Says "every 4 hours" but actually runs **every 6 hours**
- Update Frameworks (daily 2am) ✅
- Send Newsletters ❌ Says "daily 7am" but actually **10:20 AM PST**

**Missing from Documentation**:
- Statistics Verification (every 6 hours)
- Article Clustering (every 4 hours)
- Context Generation (every 8 hours)

---

## Critical Issues to Address

### ✅ ALL ISSUES RESOLVED

1. ✅ **Router Conflict**: FIXED (2025-10-04 01:15)
   - Merged routers into single [articles.py](backend/app/routes/articles.py)
   - Removed article_detail.py
   - Updated main.py imports

2. ✅ **API Documentation**: FIXED (2025-10-04 01:15)
   - [API.md](docs/API.md) now includes ALL Phase 1-3 endpoints
   - 18 new endpoints documented with examples
   - Fixed `/auth/register` (was `/auth/signup`)

3. ✅ **Background Jobs**: FIXED (2025-10-04 01:15)
   - [ARCHITECTURE.md](docs/ARCHITECTURE.md:221-294) updated with:
     - Correct timings (AI: 6hrs, Newsletter: 10:20 AM PST)
     - All 8 jobs documented (added statistics, clustering, context)

4. ✅ **AI Model References**: Fixed (2025-10-04 00:15)
   - ARCHITECTURE.md: "Claude Haiku" → "OpenAI GPT-4o-mini"
   - README.md: "Claude Haiku" → "OpenAI GPT-4o-mini"

### 🟢 LOW PRIORITY (Expected)

5. Phase 4-6 features documented but not implemented (expected, roadmap items)

---

## Recommended Actions

### Immediate (Critical)
1. ✅ Fix router conflict in main.py or rename article_detail router
2. ✅ Update [API.md](docs/API.md) with all new endpoints

### Short-term
3. Verify background jobs in [tasks.py](backend/app/jobs/tasks.py) match documentation
4. Add API endpoint examples for analytics, feed, preferences to API.md

### Long-term
5. Keep FRONTEND_ARCHITECTURE_PLAN.md updated as Phase 4-6 are implemented
6. Document challenge system API endpoints when Phase 4 begins

---

**Next Steps**:
1. Investigate router conflict
2. Update API.md comprehensively
3. Verify actual job schedules in code
