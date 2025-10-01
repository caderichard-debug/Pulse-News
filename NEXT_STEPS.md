# Next Steps - Implementation Guide

## 🎯 Current Status

We've completed the **foundation layer**:
- ✅ Database schema (all tables defined with SQLModel)
- ✅ Alembic migrations configured
- ✅ Docker setup optimized
- ✅ Configuration management (.env, settings)
- ✅ Initial data seeding (8 sources, 8 topics, 10 frameworks)
- ✅ Project documentation

## 🚦 Getting Started (30 minutes)

### 1. Get API Keys
1. **Anthropic Claude** (for AI analysis)
   - Go to https://console.anthropic.com/
   - Sign up and get API key
   - Free tier includes $5 credit (enough for testing)

2. **Resend** (for email)
   - Go to https://resend.com/
   - Sign up (free tier: 3,000 emails/month)
   - Get API key

### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Update these lines:
```
ANTHROPIC_API_KEY=sk-ant-xxx  # Your Anthropic key
RESEND_API_KEY=re_xxx          # Your Resend key
```

### 3. Start the Application
```bash
# Run the quick start script
./scripts/start.sh

# Or manually:
docker-compose up --build
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.seed_data
```

### 4. Verify Setup
```bash
# Test API
curl http://localhost:8000/health

# Check database
docker-compose exec db psql -U postgres -d news_db -c "SELECT COUNT(*) FROM sources;"
# Should return: 8

# View API docs
open http://localhost:8000/docs
```

## 📋 Week 1: Core Pipeline (RSS Scraping)

### Day 1: RSS Scraper Service

**File:** `backend/app/services/rss_scraper.py`

```python
"""
RSS feed scraper that fetches article metadata.
Stores: title, url, author, published_at, source
"""

import feedparser
from sqlmodel import Session, select
from app.models import Source, Article
from app.database import engine
from datetime import datetime
import hashlib

def scrape_source(source: Source) -> list[Article]:
    """Scrape a single source's RSS feed"""
    # TODO: Implement using feedparser
    # 1. Parse RSS feed
    # 2. For each entry, create Article if not exists
    # 3. Return list of new articles
    pass

def scrape_all_active_sources() -> int:
    """Scrape all active sources, return count of new articles"""
    # TODO: Iterate through active sources
    pass
```

**Implementation checklist:**
- [ ] Parse RSS feed with feedparser
- [ ] Check for duplicate articles (by URL)
- [ ] Handle RSS feed errors gracefully
- [ ] Extract: title, link, author, published date
- [ ] Set article status to PENDING
- [ ] Add logging
- [ ] Test with one source first

**Test:**
```bash
docker-compose exec backend python -c "
from app.services.rss_scraper import scrape_all_active_sources
count = scrape_all_active_sources()
print(f'Scraped {count} new articles')
"
```

### Day 2: Article Content Extraction

**File:** `backend/app/services/article_extractor.py`

```python
"""
Extract full article text from URLs.
Cascade: trafilatura → readability-lxml → RSS summary
"""

import trafilatura
from readability import Document
from bs4 import BeautifulSoup
import requests

def extract_article_content(url: str) -> dict:
    """Extract full article text, return dict with content and method used"""
    # TODO:
    # 1. Try trafilatura first
    # 2. If fails, try readability-lxml
    # 3. If both fail, return None
    # 4. Track which method succeeded
    pass

def process_pending_articles(batch_size: int = 20) -> int:
    """Process articles with status=PENDING, return count processed"""
    # TODO:
    # 1. Get articles with status PENDING
    # 2. Extract content for each
    # 3. Update article.content_text and article.extraction_method
    # 4. Set status to COMPLETED or FAILED
    pass
```

**Implementation checklist:**
- [ ] Implement trafilatura extraction
- [ ] Implement readability fallback
- [ ] Handle network errors (timeouts, 404s)
- [ ] Calculate word count
- [ ] Update article record in database
- [ ] Add rate limiting (1 req/second)
- [ ] Test with various news sites

**Test:**
```bash
# Test extraction on single article
docker-compose exec backend python -c "
from app.services.article_extractor import extract_article_content
result = extract_article_content('https://apnews.com/article/...')
print(result)
"
```

### Day 3-4: APScheduler Jobs

**File:** `backend/app/jobs/scheduler.py`

```python
"""
Background job scheduler using APScheduler.
4 separate jobs with different schedules.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from app.services.rss_scraper import scrape_all_active_sources
from app.services.article_extractor import process_pending_articles

scheduler = BackgroundScheduler()

def scrape_job():
    """Job 1: Scrape RSS feeds every 3 hours"""
    count = scrape_all_active_sources()
    print(f"Scraped {count} new articles")

def extract_job():
    """Job 2: Extract article content every 4 hours"""
    count = process_pending_articles(batch_size=20)
    print(f"Extracted content for {count} articles")

def framework_job():
    """Job 3: Update frameworks daily at 2am"""
    # TODO: Implement in Week 2
    pass

def newsletter_job():
    """Job 4: Send newsletters daily at 7am"""
    # TODO: Implement in Week 3
    pass

def start_scheduler():
    scheduler.add_job(scrape_job, 'interval', hours=3, id='scrape')
    scheduler.add_job(extract_job, 'interval', hours=4, id='extract', max_instances=1)
    scheduler.add_job(framework_job, 'cron', hour=2, id='frameworks')
    scheduler.add_job(newsletter_job, 'cron', hour=7, id='newsletter')
    scheduler.start()
```

**File:** `backend/app/main.py` (update)

```python
from app.jobs.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    start_scheduler()  # ADD THIS
    yield
```

**Implementation checklist:**
- [ ] Set up APScheduler
- [ ] Create 4 job functions
- [ ] Add to FastAPI lifespan
- [ ] Test manual job execution
- [ ] Add error handling and logging
- [ ] Verify jobs run on schedule

**Test:**
```bash
# Manually trigger jobs
docker-compose exec backend python -c "
from app.jobs.scheduler import scrape_job, extract_job
scrape_job()
extract_job()
"
```

### Day 5: Testing & Refinement

- [ ] Run scraper for 24 hours, collect 100+ articles
- [ ] Verify extraction success rate (aim for >80%)
- [ ] Check for duplicate articles
- [ ] Monitor errors and fix edge cases
- [ ] Add logging throughout
- [ ] Create admin API endpoint to view stats

**Admin endpoint** (`backend/app/routes/admin.py`):
```python
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from app.models import Article, Source
from app.database import get_session

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
def get_stats(session: Session = Depends(get_session)):
    total_articles = session.exec(select(func.count(Article.id))).first()
    pending = session.exec(
        select(func.count(Article.id))
        .where(Article.processing_status == "pending")
    ).first()

    return {
        "total_articles": total_articles,
        "pending_extraction": pending,
        "sources": session.exec(select(func.count(Source.id))).first()
    }
```

## 🎯 Success Criteria for Week 1

By end of Week 1, you should have:
- ✅ 100+ articles in database
- ✅ RSS scraping running automatically every 3 hours
- ✅ Article extraction working with >80% success rate
- ✅ APScheduler jobs running reliably
- ✅ Basic admin stats endpoint
- ✅ No duplicate articles
- ✅ Comprehensive logging

## 📊 Week 2 Preview: AI Integration

Once Week 1 is solid, you'll implement:

1. **Claude API Client** (`utils/claude_client.py`)
   - Wrapper for Anthropic API
   - Batch processing (5 articles at once)
   - Cost tracking
   - Error handling & retries

2. **AI Analyzer Service** (`services/ai_analyzer.py`)
   - Generate summaries (100 words)
   - Sentiment analysis (-10 to +10)
   - Political lean detection (left/center/right)
   - Statistics extraction

3. **Framework Mapper** (`services/framework_generator.py`)
   - Map articles to existing frameworks
   - Generate relevance scores
   - Weekly: discover new frameworks from article clusters

## 🐛 Debugging Tips

**If scraping fails:**
```bash
# Check source RSS feeds manually
docker-compose exec backend python -c "
import feedparser
feed = feedparser.parse('https://rsshub.app/apnews/topics/apf-topnews')
print(f'Entries: {len(feed.entries)}')
print(feed.entries[0] if feed.entries else 'No entries')
"
```

**If extraction fails:**
```bash
# Test extraction directly
docker-compose exec backend python -c "
import trafilatura
content = trafilatura.extract(
    requests.get('YOUR_URL').text,
    include_comments=False
)
print(content[:500] if content else 'Failed')
"
```

**Database queries:**
```bash
# View latest articles
docker-compose exec db psql -U postgres -d news_db -c "
SELECT id, title, source_id, processing_status
FROM articles
ORDER BY scraped_at DESC
LIMIT 10;
"
```

## 📚 Resources

**Libraries to study:**
- [feedparser docs](https://feedparser.readthedocs.io/)
- [trafilatura docs](https://trafilatura.readthedocs.io/)
- [APScheduler docs](https://apscheduler.readthedocs.io/)
- [SQLModel docs](https://sqlmodel.tiangolo.com/)

**Example RSS scraper:**
```python
import feedparser

feed = feedparser.parse('https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml')

for entry in feed.entries[:5]:  # First 5 entries
    print(f"Title: {entry.title}")
    print(f"Link: {entry.link}")
    print(f"Published: {entry.published}")
    print(f"Author: {entry.get('author', 'Unknown')}")
    print("---")
```

## 🎓 Learning Approach

**For each service, follow this pattern:**
1. **Research** - Read library docs, find examples
2. **Prototype** - Test in Python REPL or notebook
3. **Implement** - Write the service function
4. **Test** - Manual testing with real data
5. **Integrate** - Add to scheduler/main app
6. **Monitor** - Run for 24hrs, check logs

## 💡 Quick Wins

If you want to see results faster:

1. **Start with 1 source** - Just AP News to begin
2. **Manual testing** - Run jobs manually before scheduling
3. **Print debugging** - Use print() liberally at first
4. **Small batches** - Process 5 articles at a time initially

## 🤔 Questions to Consider

As you implement Week 1:

1. **Error handling:** What happens if an RSS feed is down?
2. **Duplicates:** How to detect if article already scraped?
3. **Rate limiting:** How to avoid overwhelming news sites?
4. **Logging:** What information is important to track?
5. **Performance:** How long does extracting 20 articles take?

## 📞 Getting Help

If stuck:
1. Check logs: `docker-compose logs -f backend`
2. Test in isolation: Use Python REPL
3. Review docs: All libraries are well-documented
4. Simplify: Remove complexity until it works

## 🚀 Let's Build!

You now have:
- ✅ Complete architecture plan
- ✅ Database schema and migrations
- ✅ 8 news sources configured
- ✅ 10 seed frameworks
- ✅ Docker environment ready
- ✅ Clear week-by-week roadmap

**Start with Day 1: RSS Scraper Service**

The foundation is solid. Time to make it work! 🎉
