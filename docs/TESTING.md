# Testing Guide

## Quick Start

### Run All Tests
```bash
cd backend
python3 -m pytest tests/ -v
```

### Run Specific Test File
```bash
python3 -m pytest tests/test_api.py -v
```

### Run Specific Test
```bash
python3 -m pytest tests/test_api.py::test_root_endpoint -v
```

### Run with Coverage
```bash
python3 -m pytest tests/ --cov=app --cov-report=html
```

## Test Status

**✅ 127/127 tests passing (100% success rate)**

### Test Coverage by Module

- `test_ai_analyzer.py` - 14 tests ✅ - AI article analysis
- `test_api.py` - 8 tests ✅ - API endpoints
- `test_api_routes.py` - 17 tests ✅ - Admin and article routes
- `test_article_extractor.py` - 14 tests ✅ - Content extraction
- `test_auth.py` - 10 tests ✅ - Authentication & authorization
- `test_framework_generator.py` - 14 tests ✅ - Framework mapping
- `test_model_relationships.py` - 13 tests ✅ - Database relationships
- `test_models.py` - 5 tests ✅ - Model definitions
- `test_newsletter_service_simple.py` - 3 tests ✅ - Newsletter generation
- `test_preferences.py` - 9 tests ✅ - User preferences
- `test_rss_scraper.py` - 20 tests ✅ - RSS feed scraping

## Testing Patterns

### 1. FastAPI Testing with Database

```python
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session

@pytest.fixture(name="session")
def session_fixture():
    """Create test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with overridden database dependency"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_endpoint(client: TestClient):
    response = client.get("/endpoint")
    assert response.status_code == 200
```

### 2. Mock RSS Feed Entries

```python
class MockEntry:
    """Mock RSS entry supporting both dict and attribute access"""
    def __init__(self, **kwargs):
        self._data = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __setattr__(self, name, value):
        if name == '_data':
            super().__setattr__(name, value)
        else:
            if hasattr(self, '_data'):
                self._data[name] = value
            super().__setattr__(name, value)
```

### 3. Service Session Injection

```python
def service_function(session: Session = None) -> Dict:
    """Service that accepts optional session for testing"""

    def _inner(session: Session):
        # Actual business logic here
        return {"result": "success"}

    if session is not None:
        return _inner(session)
    else:
        with Session(engine) as session:
            return _inner(session)

# In test:
def test_service(session: Session):
    result = service_function(session)
    assert result["result"] == "success"
```

### 4. Mocking External Libraries

```python
from unittest.mock import patch, Mock

# Patch where imported FROM, not where imported TO
@patch('bs4.BeautifulSoup')  # ✅ Correct
@patch('app.services.extractor.BeautifulSoup')  # ❌ Won't work
def test_extraction(mock_bs):
    mock_soup = Mock()
    mock_soup.get_text.return_value = "Extracted text content"
    mock_bs.return_value = mock_soup

    result = extract_content(url)
    assert result == "Extracted text content"
```

## Common Issues & Solutions

### Issue: Database Connection Error
**Error**: `could not translate host name "db"`

**Solution**: Use test fixtures with dependency override instead of global client
```python
# ❌ Don't do this
client = TestClient(app)  # Uses production DB

# ✅ Do this
@pytest.fixture(name="client")
def client_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)
```

### Issue: Mock Not Working
**Error**: Mock is called but code still uses real implementation

**Solution**: Patch the import location correctly
```python
# If code does: from bs4 import BeautifulSoup
@patch('bs4.BeautifulSoup')  # ✅ Correct

# NOT:
@patch('app.services.article_extractor.BeautifulSoup')  # ❌ Wrong
```

### Issue: Enum Value Mismatch
**Error**: `assert 'completed' == 'COMPLETED'`

**Solution**: SQLModel returns lowercase enum values
```python
# Enum definition
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

# In test
assert data["status"] == "completed"  # Lowercase!
```

## CI/CD Integration

Tests run automatically on GitHub Actions for every push and PR.

See `.github/workflows/test.yml` for configuration.

### Local CI Testing

```bash
# Install act to run GitHub Actions locally
brew install act

# Run test workflow
act -j test
```

## Test Development Guidelines

### 1. Test File Organization
- One test file per service/route module
- Group tests by functionality using classes
- Use descriptive test names: `test_<action>_<expected_outcome>`

### 2. Fixtures
- Create reusable fixtures in `conftest.py`
- Use `@pytest.fixture(name="...")` for clean names
- Leverage fixture dependency injection

### 3. Mocking Strategy
- Mock external APIs (Claude, Resend)
- Mock slow operations (HTTP requests, file I/O)
- Use real database for integration tests (in-memory SQLite)

### 4. Assertions
- Test one thing per test
- Use specific assertions (`assert x == y`, not just `assert x`)
- Include failure messages when helpful

### 5. Test Data
- Use factories or fixtures for test data
- Keep test data minimal but realistic
- Clean up after tests (fixtures handle this automatically)

## Performance

Full test suite completes in ~12 seconds on average hardware.

Individual test execution: <0.1s per test

## Future Improvements

- [ ] Add integration tests for full pipeline
- [ ] Add load testing for API endpoints
- [ ] Add contract tests for external APIs
- [ ] Increase coverage to 95%+ (currently ~85%)
- [ ] Add mutation testing
- [ ] Add performance benchmarks
