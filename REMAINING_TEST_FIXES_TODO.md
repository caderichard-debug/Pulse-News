# TODO: Fix Remaining 18 Test Failures

## Summary
**Current State**: 109 passing, 18 failing (85.8% success rate)
**Goal**: Fix all remaining failures to reach 100% pass rate

---

## Category 1: Mock Data Type Issues (5 tests)

### Issue
Tests are passing MagicMock objects instead of actual values, causing SQLite type binding errors.

**Error**: `sqlite3.InterfaceError: Error binding parameter - probably unsupported type`

### Failing Tests:
1. `test_rss_scraper.py::test_successful_scrape`
2. `test_rss_scraper.py::test_published_date_parsing`
3. `test_rss_scraper.py::test_invalid_date_fallback`
4. `test_rss_scraper.py::test_scrape_multiple_sources`
5. `test_article_extractor.py::test_fallback_to_readability`

### Fix Strategy:
Update mock feed entry objects to return actual values instead of MagicMock:
```python
# Before:
mock_entry.author = MagicMock()

# After:
mock_entry.author = "John Doe"
```

**Files to fix**: `backend/tests/test_rss_scraper.py`

**Estimated Time**: 15 minutes

---

## Category 2: Database Connection Pool Issues (4 tests)

### Issue
Tests are trying to use production database connection instead of test fixture session.

**Error**: `sqlalchemy.exc.OperationalError: could not translate host name "db"`

### Failing Tests:
1. `test_api.py::test_admin_stats_endpoint`
2. `test_api.py::test_topics_endpoint`
3. `test_api.py::test_login_with_invalid_credentials`
4. `test_api.py::test_articles_analyzed_endpoint`

### Fix Strategy:
These tests use FastAPI TestClient which creates its own app context. Need to override the `get_session` dependency:

```python
def test_admin_stats_endpoint(client: TestClient, session: Session):
    # Override the dependency
    app.dependency_overrides[get_session] = lambda: session

    response = client.get("/admin/stats")
    assert response.status_code == 200

    # Clean up
    app.dependency_overrides.clear()
```

**Files to fix**: `backend/tests/test_api.py`

**Estimated Time**: 20 minutes

---

## Category 3: Field Name Assertion Issues (2 tests)

### Issue
Tests expect User model to have certain field names but we added new fields.

**Error**: `NameError: name 'topic_ids' is not defined` or `AssertionError: assert ... in User.__fields__`

### Failing Tests:
1. `test_auth.py::test_user_registration_creates_user`
2. `test_auth.py::test_user_model_field_names`

### Fix Strategy:
Update tests to match new User model schema with `name` field:

```python
# In test_user_model_field_names:
def test_user_model_field_names():
    assert 'email' in User.__fields__
    assert 'name' in User.__fields__  # Add this
    assert 'hashed_password' in User.__fields__
```

**Files to fix**: `backend/tests/test_auth.py`

**Estimated Time**: 10 minutes

---

## Category 4: Article Detail Response Issues (1 test)

### Issue
Test expects article detail endpoint to return analysis data but relationship is lazy-loaded.

### Failing Tests:
1. `test_api_routes.py::test_get_article_detail_success`

### Fix Strategy:
Update the route to eager load the analysis relationship or update the test expectations.

**Files to fix**: `backend/app/routes/articles.py` or `backend/tests/test_api_routes.py`

**Estimated Time**: 10 minutes

---

## Category 5: Newsletter Service Issues (1 test)

### Issue
Newsletter generation test expects certain behavior that needs session parameter.

### Failing Tests:
1. `test_newsletter_service_simple.py::test_generate_newsletter_for_user_called`

### Fix Strategy:
Update the test to properly mock the newsletter service with session parameter.

**Files to fix**: `backend/tests/test_newsletter_service_simple.py`

**Estimated Time**: 10 minutes

---

## Category 6: Preferences Route Issues (3 tests)

### Issue
Preference routes need session dependency override like Category 2.

**Error**: `NameError: name 'Topic' is not defined` (import issue)

### Failing Tests:
1. `test_preferences.py::test_update_preferences_creates_topic_preferences`
2. `test_preferences.py::test_subscribe_to_topic`
3. `test_preferences.py::test_unsubscribe_from_topic`

### Fix Strategy:
1. Fix import statement in test file to import Topic model
2. Override get_session dependency like Category 2

**Files to fix**: `backend/tests/test_preferences.py`

**Estimated Time**: 15 minutes

---

## Category 7: Framework Generator API Key Test (1 test)

### Issue
Test needs session parameter passed correctly.

### Failing Tests:
1. `test_framework_generator.py::test_no_api_key`

### Fix Strategy:
Add missing session parameter to test:
```python
def test_no_api_key(self, mock_client, session: Session):  # Add session parameter
    mock_client.is_available.return_value = False
    count = discover_new_frameworks(session)  # Already fixed
    assert count == 0
```

**Files to fix**: `backend/tests/test_framework_generator.py`

**Estimated Time**: 5 minutes

---

## Category 8: Article Extractor Short Content Test (1 test)

### Issue
Mock data setup issue - trafilatura returns content that's too short.

### Failing Tests:
1. `test_article_extractor.py::test_extraction_too_short`

### Fix Strategy:
Fix the mock setup to properly simulate short content scenario.

**Files to fix**: `backend/tests/test_article_extractor.py`

**Estimated Time**: 5 minutes

---

## Execution Plan

### Priority Order (by impact and ease):
1. **Category 7** - Framework Generator (1 test, 5 min) - Quick win
2. **Category 8** - Article Extractor (1 test, 5 min) - Quick win
3. **Category 3** - Field Name Assertions (2 tests, 10 min) - Easy fix
4. **Category 6** - Preferences (3 tests, 15 min) - Import + dependency override
5. **Category 1** - Mock Data Types (5 tests, 15 min) - Tedious but straightforward
6. **Category 5** - Newsletter (1 test, 10 min) - Single test fix
7. **Category 4** - Article Detail (1 test, 10 min) - Route or test update
8. **Category 2** - Database Connection (4 tests, 20 min) - Dependency override pattern

**Total Estimated Time**: 1.5 hours

---

## Success Criteria
- ✅ All 127 tests passing
- ✅ No deprecation warnings addressed
- ✅ Test coverage maintained at current level
- ✅ No breaking changes to production code
