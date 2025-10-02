# Test Execution Notes

## Current Test Status: 82 Passing, 45 Failing

### ✅ What's Working (82 tests)
- All authentication tests
- All preference tests
- All model structure tests
- API route tests (when not calling services)
- Model relationship tests (except many-to-many)
- Article extractor mocking tests
- Framework generator basic tests

### ❌ What's Failing (45 tests)

#### Root Cause #1: Service Architecture (38 tests)
**Issue**: Services create their own database sessions using production `engine`:

```python
# Current pattern in services:
def analyze_articles_batch(batch_size: int = 5) -> int:
    with Session(engine) as session:  # Uses production PostgreSQL
        # ...
```

**Why it fails**:
- Tests run outside Docker try to connect to PostgreSQL hostname "db"
- Tests run inside Docker use production DB instead of test SQLite
- Cannot inject test database session

**Affected Tests**:
- `test_ai_analyzer.py`: All batch processing tests (7 tests)
- `test_article_extractor.py`: All `process_pending_articles` tests (6 tests)
- `test_framework_generator.py`: All tests that call services (15 tests)
- `test_rss_scraper.py`: All `scrape_all_active_sources` tests (4 tests)
- Some `test_api.py` and `test_api_routes.py` that call services (6 tests)

**Solution**: Refactor services to accept `session` parameter:
```python
def analyze_articles_batch(session: Session, batch_size: int = 5) -> int:
    # Use injected session
```

#### Root Cause #2: Article-Topic Many-to-Many (2 tests)
**Issue**: Relationship not properly configured in SQLModel

**Affected Tests**:
- `test_article_topic_many_to_many`
- `test_topic_articles_many_to_many`

**Error**: Article object has no attribute `topics`

**Solution**: Need to check and fix the Article/Topic relationship definition

#### Root Cause #3: Newsletter Service Imports (3 tests)
**Issue**: Import errors in newsletter service

**Affected Tests**:
- All `test_newsletter_service_simple.py` tests (3 tests)

**Solution**: Fix missing imports or model references

#### Root Cause #4: SQLAlchemy Connection (2 tests)
**Issue**: Some old tests still trying to connect to PostgreSQL

**Affected Tests**:
- `test_admin_stats_endpoint`
- `test_topics_endpoint`

---

## How to Run Tests Correctly

### ✅ Method 1: Inside Docker (Recommended)
```bash
docker-compose exec backend pytest tests/ -v
```
**Pros**:
- Services can access production DB if needed
- All dependencies available
- Realistic environment

**Cons**:
- Still uses production DB (data pollution risk)
- Slower

### ✅ Method 2: Local with Service Mocking (Current)
```bash
pytest -n auto
```
**Pros**:
- Fast parallel execution
- Uses test SQLite database
- No production DB pollution

**Cons**:
- Services that create own sessions fail
- Need to mock service functions

### ❌ Method 3: Local without Mocking (Current State)
This is what's failing - tests try to call real services which try to connect to PostgreSQL.

---

## Immediate Fixes Available

### Fix 1: SQLModel Deprecation Warnings (Easy - 4 locations)
Replace `session.query()` with `session.exec()` in:
- `test_auth.py:69`
- `test_preferences.py:136`
- `test_preferences.py:160`
- `test_preferences.py:191`

### Fix 2: Skip Service-Based Tests (Quick workaround)
Add `@pytest.mark.skip(reason="Service architecture needs refactor")` to failing tests

### Fix 3: Mock Services Instead of Calling Them (Better)
Change tests to mock the service functions rather than calling them

---

## Long-term Solution: Service Refactor

### Step 1: Update Service Signatures
```python
# Before
def analyze_articles_batch(batch_size: int = 5) -> int:
    with Session(engine) as session:
        # ...

# After
def analyze_articles_batch(session: Session, batch_size: int = 5) -> int:
    # Use injected session
```

### Step 2: Update All Service Calls
Update routes, background jobs, and CLI scripts to pass session

### Step 3: Update Tests
Tests can now inject test session:
```python
def test_analyze(session: Session):
    result = analyze_articles_batch(session, batch_size=5)
    assert result > 0
```

---

## Test Execution Recommendation

**For CI/CD**: Use Method 1 (Docker) with test database
**For Development**: Use Method 2 (Local) with proper service mocking
**For Coverage**: Method 1 with coverage reporting

---

## Summary

- **82 tests pass** when they use test fixtures properly
- **45 tests fail** because services bypass test infrastructure
- **Root cause**: Services create own DB sessions instead of accepting them
- **Quick fix**: Mock services in tests
- **Proper fix**: Refactor service architecture (estimated 2-3 hours)

The test quality is good - the architecture just needs adjustment to support dependency injection.
