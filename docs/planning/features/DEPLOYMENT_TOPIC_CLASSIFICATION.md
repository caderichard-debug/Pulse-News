# Deployment Guide: Topic Classification Feature

## Overview

This deployment adds AI-powered topic classification to articles, enabling users to filter the feed by topics like politics, technology, culture, etc.

## Changes Summary

### Backend Changes
1. **OpenAI Prompt Update** - Added topic classification to AI analysis
   - File: `backend/app/utils/openai_client.py`
   - Returns 8 predefined topics: general, politics, economics, technology, science, culture, world, environment

2. **AI Analyzer Enhancement** - Populates topic data during analysis
   - File: `backend/app/services/ai_analyzer.py`
   - Updates `Article.topic_category` (string field)
   - Creates `ArticleTopicLink` entries (many-to-many)

3. **Backfill Script** - Re-analyzes existing articles
   - File: `backend/scripts/backfill_article_topics.py`
   - Documentation: `backend/scripts/README_BACKFILL.md`

### Database
- **No migration required** - Schema already supports these fields
- `Article.topic_category` field exists (currently NULL for old articles)
- `article_topics` table exists (currently empty)

### API
- **No breaking changes** - Existing endpoints work as before
- `/feed/topics` now returns actual topics instead of empty array

## Pre-Deployment Checklist

- [ ] All changes committed to git
- [ ] Docker build succeeds: `docker-compose build backend`
- [ ] Backend tests pass: `docker-compose exec backend pytest`
- [ ] Frontend tests pass: `cd frontend && npm test`
- [ ] Verified local-container sync: `./scripts/sync-local-container.sh`

## Deployment Steps

### 1. Deploy Code Changes

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Start services
docker-compose up -d

# Wait for services to be healthy
sleep 10

# Check backend is running
docker logs news_backend --tail 20
```

### 2. Verify Database Schema

```bash
# Check current migration (should be at head)
docker-compose exec backend alembic current

# Expected output: 9c422eafa504 (head)
```

### 3. Verify API Works

```bash
# Test the feed/topics endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/feed/topics

# Expected: Empty array initially (articles not yet re-analyzed)
# Result: []
```

### 4. Backfill Existing Articles

**Option A: Full Backfill (Recommended for Production)**

```bash
# Run backfill script (will process all ~613 articles)
docker-compose exec backend python scripts/backfill_article_topics.py --batch-size 50

# This will:
# - Take ~20-30 minutes
# - Cost ~$1.20-$1.30 in OpenAI API calls
# - Require confirmation before starting
```

**Option B: Gradual Backfill (If Concerned About Cost)**

```bash
# Day 1: First 200 articles
docker-compose exec backend python scripts/backfill_article_topics.py --max-articles 200

# Day 2: Next 200 articles
docker-compose exec backend python scripts/backfill_article_topics.py --max-articles 200

# Day 3: Remaining articles
docker-compose exec backend python scripts/backfill_article_topics.py --max-articles 0
```

**Option C: Test First (Recommended)**

```bash
# Test with just 10 articles
docker-compose exec backend python scripts/backfill_article_topics.py --max-articles 10

# Verify topics appear
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/feed/topics

# If successful, run full backfill
docker-compose exec backend python scripts/backfill_article_topics.py
```

### 5. Verify Backfill Succeeded

```bash
# Check topic distribution
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/feed/topics

# Expected output (example):
# [
#   {"name":"politics","article_count":150},
#   {"name":"world","article_count":120},
#   {"name":"technology","article_count":85},
#   ...
# ]

# Check database directly
docker-compose exec backend python -c "
from app.database import get_session
from app.models import Article, ArticleTopicLink
from sqlmodel import select, func

with next(get_session()) as session:
    with_topics = session.exec(select(func.count(Article.id)).where(Article.topic_category.isnot(None))).one()
    topic_links = session.exec(select(func.count(ArticleTopicLink.article_id))).one()
    print(f'Articles with topics: {with_topics}')
    print(f'ArticleTopicLink entries: {topic_links}')
"
```

### 6. Test Frontend

1. Navigate to feed page: http://localhost:3000/feed
2. Check topics dropdown - should show all available topics
3. Select a topic - feed should filter correctly
4. Verify article counts match

## Rollback Plan

If issues arise, the feature can be safely rolled back:

```bash
# Revert code changes
git revert HEAD

# Rebuild and restart
docker-compose build
docker-compose up -d
```

**Note:** Existing topic data will remain in database but won't be used. No data loss occurs.

## Post-Deployment

### Monitor New Articles

New articles will automatically be classified:

```bash
# Trigger analysis job to test
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/admin/jobs/analyze

# Check logs for topic classification
docker logs news_backend --tail 100 | grep "topic:"
```

### Expected Log Output

```
INFO:app.services.ai_analyzer:  ✓ Analyzed: Article title... (sentiment: 5, lean: center, topic: politics)
```

## Troubleshooting

### Topics dropdown still shows "All Topics" only

**Cause:** Backfill not run or failed
**Fix:**
```bash
docker-compose exec backend python scripts/backfill_article_topics.py --dry-run
# Check output, then run without --dry-run
```

### OpenAI API errors during backfill

**Cause:** API key issues or rate limits
**Fix:**
```bash
# Check API key is set
docker-compose exec backend env | grep OPENAI_API_KEY

# Reduce batch size
docker-compose exec backend python scripts/backfill_article_topics.py --batch-size 25
```

### Database connection errors

**Cause:** Database not ready or connection pool exhausted
**Fix:**
```bash
# Restart database
docker-compose restart db

# Wait and retry
sleep 10
docker-compose exec backend python scripts/backfill_article_topics.py
```

### Partial backfill completion

**Cause:** Script interrupted
**Fix:** Simply re-run the script - it will skip articles that already have topics

## Files Changed

### Modified Files
- `backend/app/utils/openai_client.py` - Added topic to AI prompt
- `backend/app/services/ai_analyzer.py` - Added topic population logic

### New Files
- `backend/scripts/backfill_article_topics.py` - Backfill script
- `backend/scripts/README_BACKFILL.md` - Script documentation
- `backend/scripts/README.md` - Scripts directory overview
- `DEPLOYMENT_TOPIC_CLASSIFICATION.md` - This file

### Synced from Container
- `backend/alembic/versions/9c422eafa504_add_user_submitted_articles.py` - Migration

## Cost Estimate

### One-Time Backfill Cost
- **Articles to process:** ~613
- **Cost per article:** ~$0.002
- **Total cost:** ~$1.20-$1.30

### Ongoing Costs
- New articles analyzed automatically as part of existing pipeline
- No additional cost beyond current AI analysis

## Performance Impact

- **Backfill time:** ~20-30 minutes for ~600 articles
- **API load:** 5 articles per OpenAI call (optimal batch size)
- **Database impact:** Minimal (just updates to existing records)
- **Frontend impact:** None (endpoint returns instantly)

## Success Criteria

- [ ] Backend builds and starts successfully
- [ ] Topics endpoint returns list of topics with counts
- [ ] Frontend dropdown shows all topics
- [ ] Filtering by topic works correctly
- [ ] New articles automatically get topics assigned
- [ ] No errors in backend logs

## Support

For issues or questions:
1. Check logs: `docker logs news_backend --tail 100`
2. Review this document's Troubleshooting section
3. Check script documentation: `backend/scripts/README_BACKFILL.md`
4. Verify sync status: `./scripts/sync-local-container.sh`
