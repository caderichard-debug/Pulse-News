# Test Architecture & Coverage Analysis

## Current Test Setup

### Test Infrastructure

**Framework**: pytest with FastAPI TestClient
**Database**: In-memory SQLite with StaticPool
**Total Tests**: 32 passing ✅

### Test Configuration ([conftest.py](backend/tests/conftest.py))

```python
# Key Fixtures

1. session_fixture - In-memory SQLite database
   - Creates fresh database for each test
   - Uses StaticPool for thread safety
   - Auto-creates all tables

2. client_fixture - FastAPI TestClient
   - Overrides database dependency
   - Provides HTTP client for API testing
   - Cleans up after each test
```

**Benefits**:
- ✅ Fast (in-memory)
- ✅ Isolated (fresh DB per test)
- ✅ No external dependencies
- ✅ Parallel test execution safe

---

## Current Test Coverage

### ✅ Well-Tested Components (32 tests)

#### 1. Authentication ([test_auth.py](backend/tests/test_auth.py)) - 10 tests
```
✅ User registration (email validation, password strength)
✅ Login flow (correct/incorrect credentials)
✅ JWT token generation and validation
✅ Password hashing (bcrypt)
✅ Protected endpoints
✅ Field name validation (prevents bugs!)
```

**Coverage**: ~90% of auth logic

#### 2. User Preferences ([test_preferences.py](backend/tests/test_preferences.py)) - 9 tests
```
✅ Get user preferences
✅ Update preferences (priority, active status)
✅ Subscribe/unsubscribe to topics
✅ Priority validation (1-10)
✅ Field name validation
✅ Authorization requirements
```

**Coverage**: ~85% of preferences logic

#### 3. Models ([test_models.py](backend/tests/test_models.py)) - 5 tests
```
✅ User model structure
✅ Article model structure
✅ Framework model structure
✅ Enum validations (ProcessingStatus, PoliticalLean)
```

**Coverage**: ~60% of models (basic validation only)

#### 4. API Endpoints ([test_api.py](backend/tests/test_api.py)) - 8 tests
```
✅ Root endpoint
✅ Admin stats endpoint
✅ Topics listing
✅ Registration validation
✅ Login validation
✅ Protected routes
✅ Articles endpoint
```

**Coverage**: ~40% of API routes (basic smoke tests)

---

## ⚠️ Components NOT Yet Tested

### High Priority (Core Features)

#### 1. **Article Analysis Service** ([ai_analyzer.py](backend/app/services/ai_analyzer.py))
```python
# What it does:
- Analyzes articles with OpenAI GPT-4o-mini
- Generates summaries and bias analysis
- Identifies ethical frameworks

# Why test:
- Uses external API (OpenAI) - needs mocking
- Core feature of the app
- Expensive if it breaks (API costs)

# Test ideas:
✅ Mock OpenAI responses
✅ Test prompt generation
✅ Test error handling (API failures)
✅ Test parsing of AI responses
✅ Test token limits
```

**Estimated tests needed**: 8-10

---

#### 2. **Newsletter Service** ([newsletter_service.py](backend/app/services/newsletter_service.py))
```python
# What it does:
- Generates personalized newsletters
- Sends emails via Resend
- Tracks which articles were sent

# Why test:
- Core feature (email delivery)
- Uses external API (Resend)
- Business logic for article selection

# Test ideas:
✅ Newsletter generation for user preferences
✅ Article selection algorithm
✅ Email template rendering
✅ Mock Resend API calls
✅ Error handling (send failures)
✅ Newsletter tracking
```

**Estimated tests needed**: 10-12

---

#### 3. **RSS Scraper** ([rss_scraper.py](backend/app/services/rss_scraper.py))
```python
# What it does:
- Fetches RSS feeds from sources
- Parses articles
- Deduplicates content

# Why test:
- Critical for data pipeline
- Network failures common
- Parsing can be fragile

# Test ideas:
✅ Parse valid RSS feeds
✅ Handle malformed XML
✅ Network error handling
✅ Deduplication logic
✅ Date parsing edge cases
```

**Estimated tests needed**: 8-10

---

#### 4. **Article Extractor** ([article_extractor.py](backend/app/services/article_extractor.py))
```python
# What it does:
- Extracts full article text from URLs
- Cleans HTML content
- Handles different site structures

# Why test:
- Parsing can fail on different sites
- Network requests need mocking
- Content cleaning is complex

# Test ideas:
✅ Extract from common news sites
✅ Handle paywalls
✅ Clean HTML (remove ads, menus)
✅ Handle missing content
✅ Timeout handling
```

**Estimated tests needed**: 6-8

---

### Medium Priority (Background Jobs)

#### 5. **Scheduler Tasks** ([jobs/tasks.py](backend/app/jobs/tasks.py))
```python
# What it does:
- Scrapes RSS feeds on schedule
- Processes articles with AI
- Sends newsletters

# Why test:
- Runs automatically (harder to debug)
- Coordinates multiple services
- Can cause expensive API calls

# Test ideas:
✅ Task scheduling works
✅ Error recovery (retry logic)
✅ Don't process duplicates
✅ Batch processing limits
```

**Estimated tests needed**: 5-7

---

#### 6. **Framework Generator** ([framework_generator.py](backend/app/services/framework_generator.py))
```python
# What it does:
- Generates ethical frameworks with AI
- Identifies debate axes
- Creates opposing positions

# Why test:
- Uses OpenAI (expensive if wrong)
- Complex prompt engineering
- Seed data quality matters

# Test ideas:
✅ Framework generation from topics
✅ Parse AI responses correctly
✅ Handle malformed responses
✅ Validate framework structure
```

**Estimated tests needed**: 6-8

---

### Lower Priority (Already Simple)

#### 7. **Admin Routes** ([routes/admin.py](backend/app/routes/admin.py))
```
Current tests: Basic stats endpoint ✅
Additional tests needed: 2-3
```

#### 8. **Articles Routes** ([routes/articles.py](backend/app/routes/articles.py))
```
Current tests: Basic endpoint ✅
Additional tests needed: 3-5
- Filtering by topic
- Pagination
- Framework links
```

#### 9. **Config & Utils**
```
- config.py - Mostly environment vars (1-2 tests)
- database.py - Simple setup (1-2 tests)
- auth utils - Already well tested ✅
```

---

## Recommended Testing Strategy

### Phase 1: Critical Services (High ROI)

**Priority order**:
1. **AI Analyzer** (8-10 tests) - Most critical, uses expensive API
2. **Newsletter Service** (10-12 tests) - Core feature
3. **RSS Scraper** (8-10 tests) - Data pipeline entry point

**Why these first**:
- Core features that cost money if broken
- Complex logic prone to bugs
- User-facing (breaks affect UX)

**Time estimate**: 3-4 hours
**Value**: Prevents most production bugs

---

### Phase 2: Data Pipeline (Reliability)

**Components**:
4. **Article Extractor** (6-8 tests)
5. **Background Tasks** (5-7 tests)

**Why next**:
- Data quality depends on these
- Run automatically (harder to debug)
- Network failures common

**Time estimate**: 2-3 hours
**Value**: Ensures data pipeline reliability

---

### Phase 3: Supporting Features

**Components**:
6. **Framework Generator** (6-8 tests)
7. **Additional API routes** (5-8 tests)
8. **Edge cases** (as discovered)

**Time estimate**: 2-3 hours
**Value**: Complete coverage

---

## Test Patterns to Use

### 1. Mocking External APIs

```python
# Example: Mock OpenAI
from unittest.mock import Mock, patch

@patch('app.services.ai_analyzer.openai.ChatCompletion.create')
def test_analyze_article(mock_openai, session):
    # Setup mock response
    mock_openai.return_value.choices = [
        Mock(message=Mock(content='{"summary": "Test"}'))
    ]

    # Test the service
    result = analyze_article("article text")

    # Verify
    assert result["summary"] == "Test"
    mock_openai.assert_called_once()
```

### 2. Testing Background Jobs

```python
# Example: Test newsletter generation
def test_newsletter_generation(session):
    # Create test data
    user = create_test_user(session)
    articles = create_test_articles(session, count=5)

    # Generate newsletter
    newsletter = generate_newsletter_for_user(user)

    # Verify
    assert len(newsletter.articles) <= 5
    assert newsletter.user_id == user.id
```

### 3. Testing RSS Parsing

```python
# Example: Test RSS parser
def test_parse_rss_feed():
    # Load test fixture
    with open('tests/fixtures/sample_feed.xml') as f:
        xml_content = f.read()

    # Parse
    articles = parse_rss_feed(xml_content)

    # Verify
    assert len(articles) > 0
    assert articles[0].title is not None
```

---

## Coverage Goals

### Current Coverage
```
Authentication:    ~90% ✅
Preferences:       ~85% ✅
Models:            ~60% ⚠️
API Routes:        ~40% ⚠️
Services:          ~10% ❌
Background Jobs:   ~5%  ❌
```

### Target Coverage (Recommended)
```
Authentication:    95%  (already good)
Preferences:       90%  (minor additions)
Models:            80%  (add relationship tests)
API Routes:        70%  (add edge cases)
Services:          75%  (priority: AI, newsletter, RSS)
Background Jobs:   60%  (focus on error handling)

Overall Target:    75-80% coverage
```

---

## Next Steps to Improve Tests

### Immediate (This Week)

1. **Add AI Analyzer Tests** (Highest Priority)
   ```bash
   touch backend/tests/test_ai_analyzer.py
   # Add 8-10 tests with mocked OpenAI
   ```

2. **Add Newsletter Tests**
   ```bash
   touch backend/tests/test_newsletter.py
   # Add 10-12 tests with mocked Resend
   ```

3. **Add RSS Scraper Tests**
   ```bash
   touch backend/tests/test_rss_scraper.py
   # Add 8-10 tests with sample XML fixtures
   ```

**Expected result**: Coverage jumps from ~40% to ~65%

---

### Short-term (Next 2 Weeks)

4. **Add Article Extractor Tests**
5. **Add Background Job Tests**
6. **Add Integration Tests** (end-to-end flows)

**Expected result**: Coverage reaches ~75%

---

### Long-term (Ongoing)

7. **Performance Tests** (response times, load)
8. **Security Tests** (SQL injection, XSS)
9. **E2E Tests** (with Playwright/Selenium)

---

## Test File Organization

### Current Structure ✅
```
backend/tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_api.py          # API smoke tests
├── test_auth.py         # Auth & JWT
├── test_models.py       # Database models
└── test_preferences.py  # User preferences
```

### Recommended Structure
```
backend/tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
│
├── unit/                          # Unit tests
│   ├── test_auth.py              ✅ Exists
│   ├── test_models.py            ✅ Exists
│   ├── test_ai_analyzer.py       ⚠️ Add this
│   ├── test_newsletter.py        ⚠️ Add this
│   ├── test_rss_scraper.py       ⚠️ Add this
│   ├── test_article_extractor.py ⚠️ Add this
│   └── test_framework_gen.py     ⚠️ Add this
│
├── integration/                   # Integration tests
│   ├── test_api.py               ✅ Exists (rename)
│   ├── test_preferences.py       ✅ Exists (move)
│   ├── test_article_pipeline.py  ⚠️ Add this
│   └── test_newsletter_flow.py   ⚠️ Add this
│
├── fixtures/                      # Test data
│   ├── sample_rss.xml
│   ├── sample_article.html
│   └── mock_responses.json
│
└── e2e/                           # End-to-end tests
    └── test_user_journey.py       ⚠️ Future
```

---

## Tools & Commands

### Run All Tests
```bash
docker exec news_backend pytest /app/tests/ -v
```

### Run Specific Test File
```bash
docker exec news_backend pytest /app/tests/test_auth.py -v
```

### Run with Coverage Report
```bash
docker exec news_backend pytest /app/tests/ --cov=app --cov-report=html
```

### Run Specific Test
```bash
docker exec news_backend pytest /app/tests/test_auth.py::test_login -v
```

### Generate Coverage Report
```bash
docker exec news_backend pytest /app/tests/ --cov=app --cov-report=term-missing
```

---

## Summary

### What's Tested Well ✅
- Authentication (90%)
- User preferences (85%)
- Basic API endpoints (40%)
- Model structure (60%)

### What Needs Testing ⚠️
- AI services (OpenAI integration)
- Newsletter generation & sending
- RSS scraping & parsing
- Article extraction
- Background jobs
- Error handling

### Recommended Priority
1. AI Analyzer (prevents expensive API bugs)
2. Newsletter Service (core feature)
3. RSS Scraper (data pipeline)
4. Everything else

### Expected Effort
- Phase 1 (Critical): 3-4 hours → 65% coverage
- Phase 2 (Pipeline): 2-3 hours → 70% coverage
- Phase 3 (Complete): 2-3 hours → 75-80% coverage

**Total**: ~8-10 hours for comprehensive coverage

Your test infrastructure is solid! Just need to expand coverage to services. 🎯
