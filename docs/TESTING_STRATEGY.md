# Pulse Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the Pulse project, following the **test pyramid** principle: many unit tests, fewer integration tests, and focused end-to-end tests for critical paths.

---

## Test Structure

### Directory Organization

```
backend/tests/
├── conftest.py                    # Shared fixtures
├── test_api.py                   # Basic API smoke tests
├── test_models.py                # Model validation tests
├── utils/                        # Unit tests for utilities
│   ├── test_auth.py             # Authentication utils (35 tests)
│   └── test_openai_client.py    # OpenAI client wrapper (25+ tests)
├── services/                     # Unit tests for services
│   ├── test_ai_analyzer.py
│   ├── test_article_clusterer.py
│   ├── test_article_extractor.py
│   ├── test_context_generator.py
│   ├── test_credibility_rater.py
│   ├── test_fact_check_integrator.py
│   ├── test_framework_generator.py
│   ├── test_newsletter_service.py
│   ├── test_rss_scraper.py
│   ├── test_source_tracer.py
│   └── test_statistics_verifier.py
├── routes/                       # Integration tests for API routes
│   ├── test_analytics.py
│   ├── test_api_routes.py
│   ├── test_article_detail.py
│   ├── test_auth.py
│   ├── test_feed.py
│   ├── test_preferences.py
│   └── test_source_preferences.py
├── integration/                  # Multi-component integration tests
│   ├── test_article_pipeline.py  # NEW: Article processing pipeline
│   ├── test_newsletter_preferences.py
│   ├── test_model_relationships.py
│   └── test_enhancement_models.py
├── e2e/                          # End-to-end user journey tests
│   └── test_user_journey.py      # NEW: Complete user workflows
└── jobs/                         # Background job tests
    └── (to be added)
```

---

## Test Categories

### 1. Unit Tests (~60% of total tests)

**Purpose**: Test individual functions/classes in isolation with mocked dependencies.

#### Utilities (NEW - 60+ tests)
- **`test_auth.py`** (35 tests):
  - Password hashing and verification
  - JWT token creation and validation
  - Specialized tokens (verification, password reset)
  - Edge cases (long passwords, unicode, empty strings)

- **`test_openai_client.py`** (25+ tests):
  - Client initialization (with/without API key)
  - Batch article analysis
  - Framework generation
  - Article-to-framework mapping
  - Cost calculation
  - Prompt building
  - Error handling (JSON decode, API errors)

#### Services (existing - ~40 tests)
- AI analyzer, article clusterer, article extractor
- Context generator, credibility rater
- Fact-check integrator, framework generator
- Newsletter service, RSS scraper
- Source tracer, statistics verifier

**Characteristics**:
- Mock external dependencies (OpenAI, HTTP requests, file I/O)
- Fast execution (< 1 second per test)
- Test pure logic and business rules

---

### 2. Integration Tests (~30% of total tests)

**Purpose**: Test multiple components working together.

#### API Routes (existing - ~50 tests)
- Test API endpoints with real database (in-memory SQLite)
- Verify request/response formats
- Test authentication and authorization
- Validate data persistence

#### Multi-Component Pipelines (NEW - ~15 tests)
- **`test_article_pipeline.py`**:
  - Scrape → Extract → Analyze workflow
  - Batch processing with multiple services
  - Error handling across pipeline stages
  - Newsletter generation with preferences

**Characteristics**:
- Use real database (in-memory SQLite for speed)
- Mock only external APIs (OpenAI, fact-checking)
- Medium execution time (1-3 seconds per test)
- Test data flow between components

---

### 3. End-to-End Tests (~10% of total tests)

**Purpose**: Test complete user workflows through the API.

#### Critical User Journeys (NEW - ~10 tests)
- **`test_user_journey.py`**:
  - **Full User Workflow**:
    1. User registration
    2. User login
    3. Set topic preferences
    4. Browse feed
    5. Read article detail

  - **Article Pipeline Workflow**:
    1. Create article (scraping)
    2. Extract content
    3. AI analysis
    4. Framework mapping
    5. User views article

  - **Newsletter Generation Workflow**:
    1. User subscribes to topics
    2. Articles are analyzed
    3. Newsletter is generated
    4. User views newsletter

  - **Authentication Flow**:
    - Complete login/logout cycle
    - Token validation
    - Invalid credentials handling

  - **Error Handling**:
    - Database constraints
    - Invalid inputs
    - Missing resources

**Characteristics**:
- No mocking (except OpenAI for cost reasons)
- Test complete user stories
- Slower execution (3-10 seconds per test)
- Focus on critical business flows

---

## Test Coverage Summary

### Current Status (After New Tests Added)

| Category | Test Files | Estimated Tests | Coverage |
|----------|-----------|-----------------|----------|
| **Unit Tests** | 15 | ~100 | Core services, utilities |
| **Integration Tests** | 12 | ~70 | API routes, pipelines |
| **E2E Tests** | 1 | ~10 | Critical user flows |
| **Total** | **28** | **~180** | **Good coverage** |

### Coverage by Component

#### Backend
| Component | Unit | Integration | E2E |
|-----------|------|-------------|-----|
| Utils (auth, openai) | ✅ 60 | - | - |
| Services | ✅ 40 | ✅ 15 | - |
| Routes | - | ✅ 50 | ✅ 5 |
| Jobs | ⚠️ Missing | - | ✅ 2 |
| **Total** | **~100** | **~65** | **~7** |

#### Frontend
| Component | Unit | Integration | E2E |
|-----------|------|-------------|-----|
| API Client | ✅ 14 | - | - |
| Components | - | ✅ 93 | ⚠️ Missing |
| Pages (Login, Signup, Landing) | ⚠️ Missing | ⚠️ Missing | ⚠️ Missing |
| **Total** | **14** | **93** | **0** |

---

## What's Still Missing

### Backend

1. **Unit Tests** (High Priority):
   - ❌ `jobs/tasks.py` - Background job functions
   - ❌ `database.py` - Session management utilities
   - ❌ `config.py` - Settings validation

2. **Integration Tests** (Medium Priority):
   - ❌ Email delivery (newsletter HTML + Resend API)
   - ❌ Scheduler integration (APScheduler + tasks)
   - ❌ Database migrations (Alembic)

3. **E2E Tests** (Medium Priority):
   - ❌ Admin job triggers → execution → results
   - ❌ Full newsletter delivery flow (generation → email → tracking)

4. **Error Scenarios** (Low Priority):
   - ❌ Network timeouts and retries
   - ❌ Database connection failures
   - ❌ Rate limiting (OpenAI API)
   - ❌ Malformed data handling

5. **Performance Tests** (Low Priority):
   - ❌ Load testing (1000s of articles)
   - ❌ Batch processing performance
   - ❌ Database query optimization

### Frontend

1. **Unit Tests** (High Priority):
   - ❌ Utility functions (date formatting, number formatting)
   - ❌ Custom hooks (if any)
   - ❌ Form validation logic
   - ❌ Local storage utilities

2. **Integration Tests** (High Priority):
   - ❌ Login page (`app/login/page.tsx`)
   - ❌ Signup page (`app/signup/page.tsx`)
   - ❌ Landing page (`app/page.tsx`)
   - ❌ Navbar component (`components/Navbar.tsx`)
   - ❌ "How It Works" page (`app/how-it-works/page.tsx`)

3. **E2E Tests** (High Priority - Playwright):
   - ❌ User registration → login → browse → read
   - ❌ Preferences update → see personalized feed
   - ❌ Dashboard interactions (charts, filters)
   - ❌ Cross-browser testing
   - ❌ Mobile responsive testing

4. **Accessibility Tests** (Medium Priority):
   - ❌ ARIA labels and screen reader compatibility
   - ❌ Keyboard navigation (tab order, focus)
   - ❌ Color contrast (WCAG compliance)

5. **Visual Regression Tests** (Low Priority):
   - ❌ Screenshot comparisons (component appearance)
   - ❌ Responsive design (mobile/tablet/desktop)

---

## Running Tests

### Backend Tests

```bash
# All tests
docker-compose exec backend pytest

# Specific category
docker-compose exec backend pytest tests/utils/          # Unit tests (utils)
docker-compose exec backend pytest tests/services/       # Unit tests (services)
docker-compose exec backend pytest tests/routes/         # Integration tests (routes)
docker-compose exec backend pytest tests/integration/    # Integration tests (pipelines)
docker-compose exec backend pytest tests/e2e/            # E2E tests

# Specific file
docker-compose exec backend pytest tests/utils/test_auth.py -v

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Fast tests only (exclude slow E2E)
docker-compose exec backend pytest tests/utils tests/services -v
```

### Frontend Tests

```bash
# All tests
cd frontend && npm test

# Watch mode
cd frontend && npm run test:watch

# Coverage
cd frontend && npm run test:coverage

# Specific file
cd frontend && npm test -- api.test.ts
```

### Frontend E2E Tests (Playwright - when implemented)

```bash
# Install Playwright
cd frontend && npx playwright install

# Run E2E tests
cd frontend && npx playwright test

# Run in headed mode (see browser)
cd frontend && npx playwright test --headed

# Run specific test
cd frontend && npx playwright test user-journey.spec.ts
```

---

## Test Pyramid Compliance

### Current State
```
Backend:
  E2E Tests:          ~4%  (7 tests)    ✅ Good
  Integration Tests: ~38%  (65 tests)   ✅ Good
  Unit Tests:        ~58%  (100 tests)  ✅ Good

Frontend:
  E2E Tests:          0%   (0 tests)    ❌ Missing
  Integration Tests: 87%   (93 tests)   ⚠️ Too many (should be unit)
  Unit Tests:        13%   (14 tests)   ❌ Too few
```

### Target State
```
Backend:
  E2E Tests:         10%   (Add admin flows, email delivery)
  Integration Tests: 30%   (Current is good)
  Unit Tests:        60%   (Add jobs, database, config tests)

Frontend:
  E2E Tests:         15%   (Add Playwright tests)
  Integration Tests: 25%   (Convert some to unit tests)
  Unit Tests:        60%   (Add utils, hooks, components)
```

---

## Testing Best Practices

### 1. Test Naming
- Use descriptive names: `test_user_can_login_with_valid_credentials`
- Follow pattern: `test_<what>_<condition>_<expected_result>`

### 2. Arrange-Act-Assert (AAA)
```python
def test_example():
    # Arrange: Set up test data
    user = User(email="test@example.com")

    # Act: Execute the function
    result = authenticate(user, "password")

    # Assert: Verify the result
    assert result is True
```

### 3. Test Independence
- Each test should be independent
- Use fixtures for common setup
- Clean up after tests (database, files)

### 4. Mock External Services
- Always mock: OpenAI, Resend, fact-checking APIs
- Never mock: Database (use in-memory), internal services

### 5. Test Error Cases
- Test happy path AND error paths
- Test edge cases (empty strings, None, very large inputs)
- Test validation and constraints

---

## Continuous Integration (CI)

### GitHub Actions Workflow (Recommended)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          docker-compose up -d
          docker-compose exec backend pytest --cov=app

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Run tests
        run: cd frontend && npm test
```

---

## Next Steps

### Immediate (Week 1)
1. ✅ Add unit tests for utils (auth, openai_client) - DONE
2. ✅ Add E2E tests for critical user journeys - DONE
3. ✅ Add integration tests for article pipeline - DONE
4. Run all tests and fix any failures
5. Measure code coverage

### Short-term (Week 2-3)
1. Add unit tests for jobs/tasks.py
2. Add frontend unit tests for missing pages
3. Set up Playwright for frontend E2E tests
4. Write 5-10 critical frontend E2E tests

### Medium-term (Month 2)
1. Add accessibility tests
2. Add performance/load tests
3. Set up CI/CD pipeline
4. Achieve >80% code coverage

### Long-term (Ongoing)
1. Visual regression testing
2. Security testing
3. Chaos testing (resilience)
4. Continuous monitoring and improvement

---

## Success Metrics

### Coverage Targets
- **Unit Tests**: >80% code coverage
- **Integration Tests**: All API endpoints covered
- **E2E Tests**: All critical user flows covered

### Quality Targets
- **Test Pass Rate**: 100% (all tests passing)
- **Test Speed**: Unit < 0.1s, Integration < 3s, E2E < 10s
- **Flakiness**: < 1% flaky tests

### Maintenance
- Tests updated with every code change
- New features include tests (TDD preferred)
- Regular review and refactoring of tests

---

**Last Updated**: 2025-10-08
**Status**: Enhanced with unit, integration, and E2E tests
**Next Review**: After all missing tests are added
