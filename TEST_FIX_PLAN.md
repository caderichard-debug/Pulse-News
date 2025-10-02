# Test Fix Implementation Plan

## Overview

This plan addresses all 45 failing tests by fixing the root causes:
1. **Service Architecture** (38 tests) - Services need dependency injection
2. **Model Relationships** (2 tests) - Article-Topic many-to-many configuration
3. **Newsletter Service** (3 tests) - Model/service alignment
4. **Minor Issues** (2 tests) - Import and configuration fixes

**Estimated Total Time**: 4-5 hours
**Expected Result**: 127/127 tests passing ✅

---

## Phase 1: Service Architecture Refactor (2-3 hours)

### Problem
Services create their own database sessions using `with Session(engine)`, bypassing test fixtures.

**Current Pattern**:
```python
def analyze_articles_batch(batch_size: int = 5) -> int:
    with Session(engine) as session:  # ❌ Creates new session with production DB
        # ...
```

**Target Pattern**:
```python
def analyze_articles_batch(session: Session, batch_size: int = 5) -> int:
    # ✅ Uses injected session (test or production)
```

### Affected Services
1. `ai_analyzer.py` - 3 functions
2. `article_extractor.py` - 1 function
3. `framework_generator.py` - 2 functions
4. `rss_scraper.py` - 2 functions

---

### Step 1.1: Refactor AI Analyzer Service (30 min)

**File**: `backend/app/services/ai_analyzer.py`

#### Function 1: `analyze_articles_batch`
```python
# BEFORE (lines 17-109)
def analyze_articles_batch(batch_size: int = 5) -> int:
    if not openai_client.is_available():
        logger.error("OpenAI API not configured. Set OPENAI_API_KEY in .env")
        return 0

    analyzed_count = 0

    with Session(engine) as session:  # ❌ Remove this
        # Get completed articles that haven't been analyzed yet
        articles_to_analyze = session.exec(...)
        # ... rest of logic

# AFTER
def analyze_articles_batch(session: Session, batch_size: int = 5) -> int:
    """
    Analyze a batch of articles using Claude API.

    Args:
        session: Database session (injected for testing)
        batch_size: Number of articles to process in one API call (max 5 recommended)

    Returns:
        Number of articles successfully analyzed
    """
    if not openai_client.is_available():
        logger.error("OpenAI API not configured. Set OPENAI_API_KEY in .env")
        return 0

    analyzed_count = 0

    # Get completed articles that haven't been analyzed yet
    articles_to_analyze = session.exec(...)
    # ... rest of logic stays the same, just remove the `with Session(engine)` wrapper

    return analyzed_count
```

**Changes**:
- Add `session: Session` as first parameter
- Remove `with Session(engine) as session:` wrapper
- Unindent all code inside the removed wrapper
- Update docstring to document session parameter

#### Function 2: `get_article_analysis`
Already accepts session ✅ - no changes needed

#### Function 3: `get_unanalyzed_article_count`
Already accepts session ✅ - no changes needed

---

### Step 1.2: Refactor Article Extractor Service (30 min)

**File**: `backend/app/services/article_extractor.py`

#### Function 1: `extract_article_content`
Already pure function (no DB access) ✅ - no changes needed

#### Function 2: `process_pending_articles`
```python
# BEFORE (lines 90-149)
def process_pending_articles(batch_size: int = 20, delay: float = 1.0) -> int:
    processed_count = 0

    with Session(engine) as session:  # ❌ Remove this
        # Get pending articles
        pending_articles = session.exec(...)
        # ... processing logic

# AFTER
def process_pending_articles(session: Session, batch_size: int = 20, delay: float = 1.0) -> int:
    """
    Process articles with status=PENDING, extracting their full content.

    Args:
        session: Database session (injected for testing)
        batch_size: Maximum number of articles to process
        delay: Delay between requests in seconds (rate limiting)

    Returns:
        Number of articles successfully processed
    """
    processed_count = 0

    # Get pending articles
    pending_articles = session.exec(...)
    # ... rest of logic stays the same

    return processed_count
```

**Changes**:
- Add `session: Session` as first parameter
- Remove `with Session(engine) as session:` wrapper
- Unindent all code
- Update docstring

---

### Step 1.3: Refactor Framework Generator Service (45 min)

**File**: `backend/app/services/framework_generator.py`

#### Function 1: `map_articles_to_frameworks`
```python
# BEFORE (lines 20-146)
def map_articles_to_frameworks(article_ids: List[int] = None, limit: int = 10) -> int:
    if not openai_client.is_available():
        logger.error("OpenAI API not configured")
        return 0

    mappings_created = 0

    with Session(engine) as session:  # ❌ Remove this
        # Get frameworks to map against
        frameworks = session.exec(...)
        # ... mapping logic

# AFTER
def map_articles_to_frameworks(
    session: Session,
    article_ids: List[int] = None,
    limit: int = 10
) -> int:
    """
    Map analyzed articles to existing frameworks using AI.

    Args:
        session: Database session (injected for testing)
        article_ids: Specific article IDs to map, or None for recent unanalyzed ones
        limit: Maximum number of articles to process

    Returns:
        Number of article-framework mappings created
    """
    if not openai_client.is_available():
        logger.error("OpenAI API not configured")
        return 0

    mappings_created = 0

    # Get frameworks to map against
    frameworks = session.exec(...)
    # ... rest of logic stays the same

    return mappings_created
```

#### Function 2: `discover_new_frameworks`
```python
# BEFORE (lines 149-232)
def discover_new_frameworks(min_articles: int = 50) -> int:
    if not openai_client.is_available():
        logger.error("OpenAI API not configured")
        return 0

    created_count = 0

    with Session(engine) as session:  # ❌ Remove this
        # Get recent analyzed articles
        # ... discovery logic

# AFTER
def discover_new_frameworks(session: Session, min_articles: int = 50) -> int:
    """
    Use AI to discover new ethical frameworks from recent articles.
    This is run weekly to evolve the framework library.

    Args:
        session: Database session (injected for testing)
        min_articles: Minimum number of recent articles to analyze

    Returns:
        Number of new frameworks created
    """
    if not openai_client.is_available():
        logger.error("OpenAI API not configured")
        return 0

    created_count = 0

    # Get recent analyzed articles
    # ... rest of logic stays the same

    return created_count
```

---

### Step 1.4: Refactor RSS Scraper Service (30 min)

**File**: `backend/app/services/rss_scraper.py`

#### Function 1: `scrape_source`
Already accepts session ✅ - no changes needed

#### Function 2: `scrape_all_active_sources`
```python
# BEFORE (lines 112-135)
def scrape_all_active_sources() -> int:
    total_count = 0

    with Session(engine) as session:  # ❌ Remove this
        # Get all active sources
        active_sources = session.exec(...)
        # ... scraping logic

# AFTER
def scrape_all_active_sources(session: Session) -> int:
    """
    Scrape all active sources and return the total count of new articles.

    Args:
        session: Database session (injected for testing)

    Returns:
        Total number of new articles scraped
    """
    total_count = 0

    # Get all active sources
    active_sources = session.exec(...)
    # ... rest of logic stays the same

    return total_count
```

---

### Step 1.5: Update Service Callers (45 min)

Now update all code that calls these services to pass a session.

#### Update Routes

**File**: `backend/app/routes/admin.py`

```python
# BEFORE
from app.jobs.tasks import scrape_job, extract_job, analyze_job, framework_job

@router.post("/jobs/scrape")
def trigger_scrape_job(background_tasks: BackgroundTasks):
    background_tasks.add_task(scrape_job)
    return {"status": "triggered", ...}

# AFTER
from app.database import get_session
from sqlmodel import Session
from fastapi import Depends

@router.post("/jobs/scrape")
def trigger_scrape_job(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    background_tasks.add_task(scrape_job, session)
    return {"status": "triggered", ...}
```

Do this for all job triggers in `admin.py`.

#### Update Background Jobs

**File**: `backend/app/jobs/tasks.py`

```python
# BEFORE
def scrape_job():
    count = scrape_all_active_sources()
    logger.info(f"Scraped {count} articles")

# AFTER
from sqlmodel import Session
from app.database import engine

def scrape_job(session: Session = None):
    """
    Background job to scrape RSS feeds.

    Args:
        session: Optional session (for testing). If None, creates new session.
    """
    if session is None:
        with Session(engine) as session:
            count = scrape_all_active_sources(session)
    else:
        count = scrape_all_active_sources(session)

    logger.info(f"Scraped {count} articles")
```

Apply same pattern to:
- `extract_job()` - calls `process_pending_articles(session, ...)`
- `analyze_job()` - calls `analyze_articles_batch(session, ...)`
- `framework_job()` - calls `map_articles_to_frameworks(session, ...)` and `discover_new_frameworks(session, ...)`

#### Update CLI/Main Scripts

**File**: `backend/app/services/ai_analyzer.py` (bottom)

```python
# BEFORE (lines 132-135)
if __name__ == "__main__":
    # Test the analyzer
    count = analyze_articles_batch(batch_size=5)
    print(f"Analyzed {count} articles")

# AFTER
if __name__ == "__main__":
    from app.database import engine
    from sqlmodel import Session

    with Session(engine) as session:
        count = analyze_articles_batch(session, batch_size=5)
        print(f"Analyzed {count} articles")
```

Apply to all service files with `if __name__ == "__main__"` blocks.

---

### Step 1.6: Update Tests (30 min)

Update tests to pass session to service functions.

**Example: `test_ai_analyzer.py`**

```python
# BEFORE
def test_analyze_articles_success(self, mock_client, session: Session, sample_article: Article):
    mock_client.is_available.return_value = True
    mock_client.analyze_articles_batch.return_value = [...]

    count = analyze_articles_batch(batch_size=5)  # ❌ No session

    assert count == 1

# AFTER
def test_analyze_articles_success(self, mock_client, session: Session, sample_article: Article):
    mock_client.is_available.return_value = True
    mock_client.analyze_articles_batch.return_value = [...]

    count = analyze_articles_batch(session, batch_size=5)  # ✅ Pass session

    assert count == 1
```

Update all test files:
- `test_ai_analyzer.py` - Add `session` to all `analyze_articles_batch()` calls
- `test_article_extractor.py` - Add `session` to all `process_pending_articles()` calls
- `test_framework_generator.py` - Add `session` to all service calls
- `test_rss_scraper.py` - Add `session` to all `scrape_all_active_sources()` calls

---

## Phase 2: Model Relationship Fixes (1 hour)

### Problem
Article-Topic many-to-many relationship not working.

**Error**: `AttributeError: 'Article' object has no attribute 'topics'`

### Step 2.1: Check Current Model Definitions

**File**: `backend/app/models.py`

Look for Article and Topic models. They should have relationship defined:

```python
# Article model should have:
class Article(SQLModel, table=True):
    # ... fields ...

    # Relationships
    topics: List["Topic"] = Relationship(
        back_populates="articles",
        link_model=ArticleTopicLink  # If using link table
    )

# Topic model should have:
class Topic(SQLModel, table=True):
    # ... fields ...

    # Relationships
    articles: List["Article"] = Relationship(
        back_populates="topics",
        link_model=ArticleTopicLink  # If using link table
    )
```

### Step 2.2: Check for Link Table

Look for `ArticleTopicLink` or similar association table:

```python
class ArticleTopicLink(SQLModel, table=True):
    __tablename__ = "article_topic_link"

    article_id: int = Field(foreign_key="articles.id", primary_key=True)
    topic_id: int = Field(foreign_key="topics.id", primary_key=True)
```

### Step 2.3: Fix the Relationship

If relationship is missing or incorrectly configured:

```python
# Add to Article model (around line 92)
class Article(SQLModel, table=True):
    __tablename__ = "articles"

    # ... existing fields ...

    # Relationships
    source: Optional["Source"] = Relationship(back_populates="articles")
    topics: List["Topic"] = Relationship(back_populates="articles")  # ✅ Add this

# Add to Topic model (around line 76)
class Topic(SQLModel, table=True):
    __tablename__ = "topics"

    # ... existing fields ...

    # Relationships
    articles: List["Article"] = Relationship(back_populates="topics")  # ✅ Add this
```

### Step 2.4: Create Migration (if needed)

If changing existing models:

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Add article-topic relationship"

# Review migration file
cat backend/alembic/versions/[new_file].py

# Apply migration
docker-compose exec backend alembic upgrade head
```

---

## Phase 3: Newsletter Service Fixes (30-45 min)

### Problem
Model references `NewsletterArticle` table that doesn't exist.

### Step 3.1: Check Newsletter Model

**File**: `backend/app/models.py` (around line 201)

```python
class Newsletter(SQLModel, table=True):
    __tablename__ = "newsletters"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Current: JSON fields
    article_ids: str = Field(max_length=500)  # "[1,2,3,4,5]"
    framework_ids: str = Field(max_length=500)  # "[1,2,3]"

    # Missing: html_content field
    # Missing: NewsletterArticle relationship
```

### Step 3.2: Option A - Add Missing Fields (Simpler)

```python
class Newsletter(SQLModel, table=True):
    __tablename__ = "newsletters"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Email metadata
    subject: str = Field(max_length=200)
    html_content: str = Field(default="")  # ✅ Add this
    sent_at: Optional[datetime] = Field(default=None, index=True)  # ✅ Change from default_factory

    # Content references
    article_ids: str = Field(max_length=500)
    framework_ids: str = Field(max_length=500)

    # Tracking
    email_opened: bool = Field(default=False)
    links_clicked: int = Field(default=0)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="newsletters")
```

### Step 3.3: Option B - Add NewsletterArticle Table (Better)

```python
# Add new link table
class NewsletterArticle(SQLModel, table=True):
    __tablename__ = "newsletter_articles"

    newsletter_id: int = Field(foreign_key="newsletters.id", primary_key=True)
    article_id: int = Field(foreign_key="articles.id", primary_key=True)

    # Optional: order in newsletter
    display_order: int = Field(default=0)

# Update Newsletter model
class Newsletter(SQLModel, table=True):
    __tablename__ = "newsletters"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Email metadata
    subject: str = Field(max_length=200)
    html_content: str = Field(default="")  # ✅ Add this
    sent_at: Optional[datetime] = Field(default=None, index=True)

    # Remove: article_ids, framework_ids strings

    # Relationships
    user: Optional["User"] = Relationship(back_populates="newsletters")
    articles: List["Article"] = Relationship(link_model=NewsletterArticle)  # ✅ Add this
```

### Step 3.4: Update Newsletter Service

**File**: `backend/app/services/newsletter_service.py`

If using Option A (JSON fields):
```python
# Line 75-81 - Update to use JSON field
newsletter = Newsletter(
    user_id=user.id,
    subject=f"Your Pulse News Digest - {datetime.utcnow().strftime('%B %d, %Y')}",
    html_content=newsletter_data["html"],  # ✅ Use html_content field
    article_ids=json.dumps(newsletter_data["article_ids"]),  # ✅ JSON encode
    sent_at=None
)
session.add(newsletter)
session.commit()  # Don't need flush if not linking
```

If using Option B (proper table):
```python
# Line 75-82 - Keep as is (it's correct with proper table)
newsletter = Newsletter(
    user_id=user.id,
    subject=f"Your Pulse News Digest - {datetime.utcnow().strftime('%B %d, %Y')}",
    html_content=newsletter_data["html"],
    sent_at=None
)
session.add(newsletter)
session.flush()  # Get newsletter.id

# Link articles to newsletter
for article_id in newsletter_data["article_ids"]:
    newsletter_article = NewsletterArticle(
        newsletter_id=newsletter.id,
        article_id=article_id
    )
    session.add(newsletter_article)
```

### Step 3.5: Update Tests

**File**: `backend/tests/test_newsletter_service_simple.py`

```python
# Currently fails on import - will work after model fix
from app.services.newsletter_service import (
    generate_and_send_newsletters,
    _generate_newsletter_for_user,
    _render_newsletter_template
)
```

Tests should work as-is once model is fixed.

---

## Phase 4: Verification (30 min)

### Step 4.1: Run Tests Incrementally

```bash
# Test service refactors one by one
docker-compose exec backend pytest tests/test_ai_analyzer.py -v
docker-compose exec backend pytest tests/test_article_extractor.py -v
docker-compose exec backend pytest tests/test_framework_generator.py -v
docker-compose exec backend pytest tests/test_rss_scraper.py -v

# Test relationship fixes
docker-compose exec backend pytest tests/test_model_relationships.py::TestArticleRelationships::test_article_topic_many_to_many -v

# Test newsletter fixes
docker-compose exec backend pytest tests/test_newsletter_service_simple.py -v

# Run all tests
docker-compose exec backend pytest tests/ -v --tb=short
```

### Step 4.2: Expected Results

After all fixes:
```
================= 127 passed in X.XXs ==================
```

### Step 4.3: Generate Coverage Report

```bash
docker-compose exec backend pytest tests/ --cov=app --cov-report=html
open backend/htmlcov/index.html
```

Expected coverage: **~75-80%** ✅

---

## Implementation Checklist

### Phase 1: Service Architecture ✓
- [ ] Update `ai_analyzer.py` - add session parameter
- [ ] Update `article_extractor.py` - add session parameter
- [ ] Update `framework_generator.py` - add session parameter
- [ ] Update `rss_scraper.py` - add session parameter
- [ ] Update `routes/admin.py` - pass session to jobs
- [ ] Update `jobs/tasks.py` - accept session parameter
- [ ] Update CLI scripts - create session and pass
- [ ] Update all test files - pass session to service calls

### Phase 2: Model Relationships ✓
- [ ] Check `Article` and `Topic` relationship definitions
- [ ] Add/fix many-to-many relationship
- [ ] Create migration if needed
- [ ] Run migration
- [ ] Test relationship in Python shell

### Phase 3: Newsletter Service ✓
- [ ] Choose option (A: JSON fields or B: NewsletterArticle table)
- [ ] Update Newsletter model
- [ ] Update newsletter service code
- [ ] Create migration
- [ ] Run migration
- [ ] Update tests if needed

### Phase 4: Verification ✓
- [ ] Run each test file individually
- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] Document results

---

## Rollback Plan

If something breaks:

```bash
# Rollback database migration
docker-compose exec backend alembic downgrade -1

# Restore code from git
git checkout backend/app/services/
git checkout backend/app/models.py

# Rebuild container
docker-compose down
docker-compose build backend
docker-compose up -d
```

---

## Success Criteria

- ✅ 127/127 tests passing
- ✅ ~75-80% code coverage
- ✅ No deprecation warnings
- ✅ All services accept session parameter
- ✅ All relationships working
- ✅ Newsletter service functional

---

## Estimated Timeline

| Phase | Task | Time | Total |
|-------|------|------|-------|
| 1.1 | AI Analyzer | 30 min | 0.5h |
| 1.2 | Article Extractor | 30 min | 1.0h |
| 1.3 | Framework Generator | 45 min | 1.75h |
| 1.4 | RSS Scraper | 30 min | 2.25h |
| 1.5 | Update Callers | 45 min | 3.0h |
| 1.6 | Update Tests | 30 min | 3.5h |
| 2.1-2.4 | Model Relationships | 60 min | 4.5h |
| 3.1-3.5 | Newsletter Service | 45 min | 5.25h |
| 4.1-4.3 | Verification | 30 min | 5.75h |

**Total Estimated Time: 5-6 hours**

With focused work, could be completed in one development session.

---

## Next Steps

1. **Read this plan thoroughly**
2. **Create a feature branch**: `git checkout -b fix/test-architecture`
3. **Start with Phase 1.1** (AI Analyzer)
4. **Test after each phase** to catch issues early
5. **Commit frequently** with descriptive messages
6. **Create PR when all tests pass**

Good luck! The test suite is well-designed - once these architectural fixes are in place, you'll have a robust, comprehensive test foundation for the entire application.
