# How to Run Tests

## Basic Test Execution in Docker

### Run All Tests
```bash
# Run all tests with verbose output
docker-compose exec backend pytest tests/ -v

# Run all tests with shorter error output
docker-compose exec backend pytest tests/ -v --tb=short

# Run all tests quietly (just pass/fail summary)
docker-compose exec backend pytest tests/ -q
```

---

## Run Specific Test Files

```bash
# Run just AI analyzer tests
docker-compose exec backend pytest tests/test_ai_analyzer.py -v

# Run just auth tests
docker-compose exec backend pytest tests/test_auth.py -v

# Run just API tests
docker-compose exec backend pytest tests/test_api_routes.py -v

# Run just model tests
docker-compose exec backend pytest tests/test_models.py -v

# Run just relationship tests
docker-compose exec backend pytest tests/test_model_relationships.py -v
```

---

## Run Specific Test Classes or Functions

```bash
# Run specific test class
docker-compose exec backend pytest tests/test_ai_analyzer.py::TestAnalyzeArticlesBatch -v

# Run specific test function
docker-compose exec backend pytest tests/test_auth.py::test_user_registration_creates_user -v

# Run multiple specific tests
docker-compose exec backend pytest tests/test_auth.py::test_user_registration_creates_user tests/test_auth.py::test_login_verifies_password_correctly -v
```

---

## Coverage Reporting

```bash
# Run tests with coverage report in terminal
docker-compose exec backend pytest tests/ --cov=app --cov-report=term-missing

# Generate HTML coverage report
docker-compose exec backend pytest tests/ --cov=app --cov-report=html

# View the HTML report (opens in browser)
open backend/htmlcov/index.html

# Coverage with specific minimum threshold
docker-compose exec backend pytest tests/ --cov=app --cov-fail-under=75
```

---

## Useful Test Options

### Debugging
```bash
# Stop on first failure
docker-compose exec backend pytest tests/ -x

# Show print statements and logging
docker-compose exec backend pytest tests/ -v -s

# Show local variables on failure
docker-compose exec backend pytest tests/ -v -l

# More detailed error output
docker-compose exec backend pytest tests/ -vv
```

### Selective Runs
```bash
# Run only failed tests from last run
docker-compose exec backend pytest tests/ --lf

# Run failed tests first, then continue with others
docker-compose exec backend pytest tests/ --ff

# Run tests that match a keyword
docker-compose exec backend pytest tests/ -k "auth" -v

# Run tests from multiple files
docker-compose exec backend pytest tests/test_auth.py tests/test_models.py -v
```

### Parallel Execution (if pytest-xdist installed)
```bash
# Run tests in parallel using all CPU cores
docker-compose exec backend pytest tests/ -n auto

# Run tests using specific number of workers
docker-compose exec backend pytest tests/ -n 4
```

---

## Filter by Test Markers

If you add markers to your tests (e.g., `@pytest.mark.slow`, `@pytest.mark.integration`):

```bash
# Run only unit tests
docker-compose exec backend pytest tests/ -m unit -v

# Skip slow tests
docker-compose exec backend pytest tests/ -m "not slow" -v

# Run only integration tests
docker-compose exec backend pytest tests/ -m integration -v

# Combine markers
docker-compose exec backend pytest tests/ -m "unit and not slow" -v
```

---

## Recommended Test Commands

### Quick Validation (Fast, Reliable Tests Only)
```bash
docker-compose exec backend pytest tests/test_auth.py tests/test_preferences.py tests/test_models.py tests/test_model_relationships.py -v
```
**Expected**: ~50+ tests passing ✅

### Full Test Suite
```bash
docker-compose exec backend pytest tests/ -v --tb=short
```
**Expected**: ~82 passing, ~45 failing (due to service architecture issues)

### Full Suite with Coverage
```bash
docker-compose exec backend pytest tests/ -v --cov=app --cov-report=html
```

### Save Output to File
```bash
docker-compose exec backend pytest tests/ -v --tb=short 2>&1 | tee test_results.log
```

---

## Current Test Status

### ✅ Reliably Passing Tests (82 tests)
- `test_auth.py` - 10/10 ✅
- `test_preferences.py` - 9/9 ✅
- `test_models.py` - 5/5 ✅
- `test_model_relationships.py` - 11/13 (85%) ✅
- `test_api_routes.py` - 16/18 (89%) ✅
- Portions of other test files

### ⚠️ Tests with Known Issues (45 tests)
- `test_ai_analyzer.py` - 7/14 (50%)
- `test_rss_scraper.py` - 15/19 (79%)
- `test_article_extractor.py` - 8/14 (57%)
- `test_framework_generator.py` - 0/15 (0%)
- `test_newsletter_service_simple.py` - 0/3 (0%)

**Why they fail**: Services create their own DB sessions instead of using test fixtures (see [TEST_FIXES_APPLIED.md](TEST_FIXES_APPLIED.md))

---

## Test Organization

```
backend/tests/
├── conftest.py                         # Shared fixtures
├── test_api.py                        # Basic API tests
├── test_api_routes.py                 # Detailed API endpoint tests
├── test_auth.py                       # Authentication & JWT
├── test_models.py                     # Model structure
├── test_model_relationships.py        # Foreign keys & relationships
├── test_preferences.py                # User preferences
├── test_ai_analyzer.py               # AI analysis service
├── test_article_extractor.py         # Web scraping service
├── test_framework_generator.py       # Framework discovery
├── test_rss_scraper.py               # RSS feed parsing
└── test_newsletter_service_simple.py # Newsletter generation
```

---

## Troubleshooting

### Tests Fail with "connection refused"
Make sure Docker containers are running:
```bash
docker-compose up -d
docker-compose ps  # Verify containers are up
```

### Tests Fail with Import Errors
Rebuild the container:
```bash
docker-compose down
docker-compose build backend
docker-compose up -d
```

### Tests Pass Locally but Fail in Docker
Check Python versions match:
```bash
docker-compose exec backend python --version
python --version  # Local version
```

### Want to Debug a Specific Test
```bash
# Add breakpoint in test code, then:
docker-compose exec backend pytest tests/test_auth.py::test_login -v -s --pdb
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    docker-compose up -d
    docker-compose exec -T backend pytest tests/ -v --cov=app --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./backend/coverage.xml
```

### Local Pre-commit Hook
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
docker-compose exec backend pytest tests/test_auth.py tests/test_preferences.py -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose exec backend pytest tests/ -v` | Run all tests |
| `docker-compose exec backend pytest tests/ -x` | Stop on first failure |
| `docker-compose exec backend pytest tests/ -k "auth"` | Run tests matching keyword |
| `docker-compose exec backend pytest tests/ --lf` | Run last failed |
| `docker-compose exec backend pytest tests/ -s` | Show print output |
| `docker-compose exec backend pytest tests/ --cov=app` | With coverage |
| `docker-compose exec backend pytest tests/test_auth.py -v` | Run specific file |

---

## See Also

- [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md) - Test strategy and coverage plan
- [TEST_FIXES_APPLIED.md](TEST_FIXES_APPLIED.md) - Known issues and fixes
- [TEST_EXECUTION_NOTES.md](TEST_EXECUTION_NOTES.md) - Detailed execution analysis
- [COMPREHENSIVE_TEST_SUMMARY.md](COMPREHENSIVE_TEST_SUMMARY.md) - Complete test overview
