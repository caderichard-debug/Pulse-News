# E2E Testing Methodology for Pulse

> **Best practices for writing reliable end-to-end tests with Playwright**

---

## Table of Contents

1. [Overview](#overview)
2. [Core Principles](#core-principles)
3. [Navigation Patterns](#navigation-patterns)
4. [Timing and Waits](#timing-and-waits)
5. [Common Pitfalls](#common-pitfalls)
6. [Test Structure](#test-structure)
7. [CI/CD Considerations](#cicd-considerations)
8. [Examples](#examples)

---

## Overview

Pulse uses **Playwright** for end-to-end testing. These tests simulate real user interactions with the application, from signup through article reading. This document outlines the methodology for writing reliable, maintainable E2E tests that work consistently in both local and CI environments.

### Key Technologies

- **Playwright** - Browser automation framework
- **Next.js 15** - React framework with client-side navigation
- **React 19** - UI library with concurrent rendering

### Test Location

All E2E tests are located in `/frontend/e2e/`

---

## Core Principles

### 1. **Wait for Hydration After Navigation**

Next.js uses client-side navigation (via `next/link` and `next/navigation`). When navigating between pages using navbar buttons or links, the page must fully hydrate before elements are accessible.

**❌ Wrong:**
```typescript
await page.getByRole('button', { name: /feed/i }).click();
await expect(page.getByRole('heading')).toBeVisible(); // May fail!
```

**✅ Correct:**
```typescript
await page.getByRole('button', { name: /feed/i }).click();
await expect(page).toHaveURL(/\/feed/, { timeout: 10000 });

// Wait for page to hydrate
await page.waitForLoadState('domcontentloaded');
await page.waitForTimeout(1000); // Allow React to hydrate

await expect(page.getByRole('heading')).toBeVisible({ timeout: 10000 });
```

### 2. **Use Generous Timeouts for CI**

CI environments (GitHub Actions) are slower than local development machines. Always use explicit timeouts for critical assertions.

**Default timeouts (too short for CI):**
- `expect(...).toBeVisible()` → 5000ms
- `expect(page).toHaveURL(...)` → 5000ms

**Recommended for CI:**
- URL checks: `{ timeout: 10000 }` (10 seconds)
- First element on page: `{ timeout: 10000 }`
- Subsequent elements: Can use default if first element is visible

### 3. **Use Semantic Selectors**

Always prefer accessible selectors that mirror how users interact with the app:

**Priority order:**
1. `getByRole()` - Best for buttons, headings, links
2. `getByLabel()` - Best for form inputs
3. `getByText()` - For static text content
4. `getByTestId()` - Only when above options don't work

**❌ Avoid:**
```typescript
page.locator('.css-class-name')
page.locator('#specific-id')
page.locator('div > button:nth-child(2)')
```

**✅ Prefer:**
```typescript
page.getByRole('button', { name: /submit/i })
page.getByLabel(/email/i)
page.getByText(/welcome/i)
```

---

## Navigation Patterns

### Pattern 1: Initial Page Load (with gotoAndWait)

For the first page visit in a test, use the `gotoAndWait` helper:

```typescript
import { gotoAndWait } from './helpers';

await gotoAndWait(page, '/signup');
await expect(page.getByLabel(/email/i)).toBeVisible();
```

**What gotoAndWait does:**
1. Navigates to URL
2. Waits for `domcontentloaded`
3. Waits for Next.js router to be ready
4. Waits 500ms for React hydration

### Pattern 2: Client-Side Navigation (via navbar/links)

For subsequent navigation using Next.js links or buttons:

```typescript
// Step 1: Click navigation element
await page.getByRole('button', { name: /📰.*feed/i }).click();

// Step 2: Verify URL changed
await expect(page).toHaveURL(/\/feed/, { timeout: 10000 });

// Step 3: Wait for page to hydrate
await page.waitForLoadState('domcontentloaded');
await page.waitForTimeout(1000); // CI-safe hydration wait

// Step 4: Assert on page content
await expect(page.getByRole('heading', { name: /article feed/i }))
  .toBeVisible({ timeout: 10000 });
```

### Pattern 3: Form Submission with Redirect

For forms that redirect (signup, login):

```typescript
// Fill form
await page.getByLabel(/email/i).fill('user@example.com');
await page.getByLabel(/password/i).fill('password123');

// Submit
await page.getByRole('button', { name: /login/i }).click();

// Wait for redirect with generous timeout
await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

// Wait for hydration
await page.waitForLoadState('domcontentloaded');
await page.waitForTimeout(1000);

// Now safe to interact with new page
await expect(page.getByText(/welcome/i)).toBeVisible({ timeout: 10000 });
```

---

## Timing and Waits

### When to Use Different Wait Strategies

#### `waitForLoadState('domcontentloaded')`
- **Use:** After every client-side navigation
- **Purpose:** Ensures DOM is parsed and ready
- **Example:**
  ```typescript
  await page.getByRole('button', { name: /feed/i }).click();
  await page.waitForLoadState('domcontentloaded');
  ```

#### `waitForTimeout(ms)`
- **Use:** After `domcontentloaded` to allow React hydration
- **Recommended:** 1000ms for CI, 500ms for local
- **Example:**
  ```typescript
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000); // Allow React to hydrate
  ```

#### `expect(...).toBeVisible({ timeout: ms })`
- **Use:** For the first critical element on a page
- **Recommended:** 10000ms (10 seconds)
- **Example:**
  ```typescript
  await expect(page.getByRole('heading', { name: /dashboard/i }))
    .toBeVisible({ timeout: 10000 });
  ```

#### `waitForSelector()` / `waitForFunction()`
- **Use:** For dynamic content that loads via API
- **Example:**
  ```typescript
  // Wait for API-loaded content
  await page.waitForSelector('.article-card', { timeout: 10000 });
  ```

### Wait Strategy Flowchart

```
Navigation Action
    ↓
Wait for URL change (10s timeout)
    ↓
Wait for domcontentloaded
    ↓
Wait 1000ms for hydration
    ↓
Assert on first element (10s timeout)
    ↓
Assert on other elements (default timeout OK)
```

---

## Common Pitfalls

### 1. Race Conditions in CI

**Problem:** Tests pass locally but fail in CI

**Cause:** CI environments are slower, causing race conditions

**Solution:**
- Always use explicit timeouts
- Add hydration waits after navigation
- Don't rely on "it works on my machine"

**Example Fix:**
```typescript
// Before (flaky in CI)
await page.getByRole('button', { name: /feed/i }).click();
await expect(page.getByRole('heading')).toBeVisible();

// After (CI-stable)
await page.getByRole('button', { name: /feed/i }).click();
await expect(page).toHaveURL(/\/feed/, { timeout: 10000 });
await page.waitForLoadState('domcontentloaded');
await page.waitForTimeout(1000);
await expect(page.getByRole('heading')).toBeVisible({ timeout: 10000 });
```

### 2. Elements Not Found After Navigation

**Problem:** `expect(locator).toBeVisible()` fails with "element(s) not found"

**Cause:** React hasn't hydrated yet, so elements aren't in the DOM

**Solution:** Add proper hydration waits (see Pattern 2 above)

### 3. Stale Element References

**Problem:** Element reference becomes stale after navigation

**Solution:** Re-query elements after navigation instead of storing references

**❌ Wrong:**
```typescript
const button = page.getByRole('button', { name: /submit/i });
await page.goto('/other-page');
await button.click(); // Stale reference!
```

**✅ Correct:**
```typescript
await page.goto('/other-page');
const button = page.getByRole('button', { name: /submit/i });
await button.click();
```

### 4. Inconsistent Test Data

**Problem:** Tests fail due to database state from previous tests

**Solution:** Generate unique test data per test run

**✅ Best Practice:**
```typescript
test.beforeAll(() => {
  const timestamp = Date.now();
  userEmail = `test${timestamp}@example.com`;
  userPassword = 'TestPassword123!';
});
```

### 5. Missing Elements in Error States

**Problem:** Tests fail because pages show different content when there's an error

**Cause:** Pages may have early returns that render error-only views without structural elements

**Example Issue:**
```typescript
// ❌ Page component with early error return
if (error && !data) {
  return <div>{error}</div>; // No heading, no structure!
}

return (
  <>
    <h1>Page Title</h1> {/* Only shown when no error */}
    <div>{data}</div>
  </>
);
```

**Solution:** Always render page structure (headings, navigation) even in error states

**✅ Fixed:**
```typescript
if (error && !data) {
  return (
    <>
      <Navbar />
      <div className="container">
        <h1>Page Title</h1> {/* Always visible! */}
        <div className="error">{error}</div>
      </div>
    </>
  );
}

return (
  <>
    <Navbar />
    <div className="container">
      <h1>Page Title</h1>
      <div>{data}</div>
    </div>
  </>
);
```

**Benefits:**
- Tests can reliably find structural elements
- Better UX - users know where they are even when data fails
- Consistent layout regardless of data state

**Real Example from Pulse:**
The feed page was failing E2E tests because it showed an error-only view without the "Article Feed" heading when API calls failed. Adding the heading to the error state fixed both the test and improved UX.

---

## Test Structure

### Recommended Test Organization

```typescript
import { test, expect } from '@playwright/test';
import { gotoAndWait } from './helpers';

test.describe('Feature Name', () => {
  let testData: any;

  // Setup unique test data
  test.beforeAll(() => {
    testData = generateUniqueTestData();
  });

  // Setup for each test
  test.beforeEach(async ({ page }) => {
    // Login or navigate to starting point
    await gotoAndWait(page, '/login');
    // ... authentication if needed
  });

  test('should do something', async ({ page }) => {
    // Arrange
    await gotoAndWait(page, '/starting-page');

    // Act
    await page.getByRole('button', { name: /action/i }).click();
    await expect(page).toHaveURL(/\/result/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    // Assert
    await expect(page.getByText(/success/i))
      .toBeVisible({ timeout: 10000 });
  });
});
```

### File Naming Convention

- `*.spec.ts` - Test files
- `helpers.ts` - Shared utilities
- `fixtures.ts` - Test data generators

---

## CI/CD Considerations

### GitHub Actions Configuration

Our CI runs tests with:
- **Retries:** 2 (total 3 attempts)
- **Workers:** 4 parallel workers
- **Browsers:** Chromium, Firefox, WebKit
- **Sharding:** Split across multiple jobs for speed

### Writing CI-Friendly Tests

1. **Use longer timeouts:**
   ```typescript
   { timeout: 10000 } // Not 5000
   ```

2. **Add hydration waits:**
   ```typescript
   await page.waitForLoadState('domcontentloaded');
   await page.waitForTimeout(1000);
   ```

3. **Generate unique test data:**
   ```typescript
   const timestamp = Date.now();
   const email = `test${timestamp}@example.com`;
   ```

4. **Handle async operations:**
   ```typescript
   // Wait for API calls to complete
   await page.waitForResponse(resp => resp.url().includes('/api/feed'));
   ```

5. **Avoid hardcoded waits except for hydration:**
   ```typescript
   // ❌ Bad
   await page.waitForTimeout(5000); // Arbitrary wait

   // ✅ Good
   await page.waitForSelector('.data-loaded', { timeout: 10000 });
   ```

### Debugging CI Failures

When tests fail in CI:

1. **Check artifacts:**
   - Screenshots: `test-results/**/*.png`
   - Traces: `test-results/**/*.zip`
   - Error context: `test-results/**/error-context.md`

2. **View trace:**
   ```bash
   npx playwright show-trace test-results/.../trace.zip
   ```

3. **Run with same conditions locally:**
   ```bash
   # Slow down to match CI speed
   npm run test:e2e -- --slow-mo 1000

   # Run specific test
   npm run test:e2e -- user-journey.spec.ts
   ```

---

## Examples

### Example 1: Complete User Journey

```typescript
test('should complete full user journey', async ({ page }) => {
  // 1. Signup (initial load)
  await gotoAndWait(page, '/signup');
  await page.getByLabel(/email/i).fill('user@example.com');
  await page.getByLabel(/password/i).fill('Password123!');
  await page.getByRole('button', { name: /create account/i }).click();

  // Wait for redirect
  await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000);

  // 2. Navigate to Dashboard (client-side navigation)
  await page.getByRole('button', { name: /dashboard/i }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000);

  await expect(page.getByText(/articles read/i))
    .toBeVisible({ timeout: 10000 });

  // 3. Navigate to Feed (client-side navigation)
  await page.getByRole('button', { name: /feed/i }).click();
  await expect(page).toHaveURL(/\/feed/, { timeout: 10000 });
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000);

  await expect(page.getByRole('heading', { name: /article feed/i }))
    .toBeVisible({ timeout: 10000 });
});
```

### Example 2: Testing Dynamic Content

```typescript
test('should filter articles by topic', async ({ page }) => {
  await gotoAndWait(page, '/feed');

  // Wait for filters to load
  await expect(page.getByRole('combobox').first())
    .toBeVisible({ timeout: 10000 });

  // Select topic
  await page.getByRole('combobox').first().selectOption('technology');

  // Wait for articles to reload
  await page.waitForResponse(
    resp => resp.url().includes('/api/feed/articles'),
    { timeout: 10000 }
  );

  // Verify filtered results
  const articles = page.locator('.article-card');
  await expect(articles.first()).toBeVisible({ timeout: 10000 });
});
```

### Example 3: Error Handling

```typescript
test('should show error for invalid login', async ({ page }) => {
  await gotoAndWait(page, '/login');

  await page.getByLabel(/email/i).fill('wrong@example.com');
  await page.getByLabel(/password/i).fill('wrongpassword');
  await page.getByRole('button', { name: /login/i }).click();

  // Should stay on login page
  await expect(page).toHaveURL(/\/login/);

  // Should show error message
  await expect(page.getByText(/invalid credentials/i))
    .toBeVisible({ timeout: 10000 });
});
```

---

## Quick Reference

### Navigation Checklist

After every client-side navigation, follow this pattern:

```typescript
// ✅ The 4-Step Navigation Pattern
// 1. Click navigation element
await page.getByRole('button', { name: /page name/i }).click();

// 2. Verify URL (with 10s timeout)
await expect(page).toHaveURL(/\/page-route/, { timeout: 10000 });

// 3. Wait for hydration
await page.waitForLoadState('domcontentloaded');
await page.waitForTimeout(1000);

// 4. Assert on first element (with 10s timeout)
await expect(page.getByRole('heading'))
  .toBeVisible({ timeout: 10000 });
```

### Timeout Reference

| Action | Recommended Timeout | Reason |
|--------|-------------------|--------|
| URL change | 10000ms | CI environments are slow |
| First element on page | 10000ms | Allow time for hydration |
| Subsequent elements | 5000ms (default) | First element confirms page ready |
| API responses | 10000ms | Network latency in CI |
| Hydration wait | 1000ms | React needs time to attach handlers |

---

## Real-World Bug Fix Example: Enum Type Mismatch

### The Problem

During E2E testing, the "Complete User Journey" test was failing consistently with this error:

```
Error: expect(locator).toBeVisible() failed
Locator: getByRole('heading', { name: /article feed/i })
Expected: visible
Timeout: 10000ms
Error: element(s) not found
```

The feed page wasn't loading because the backend returned a **500 Internal Server Error**.

### Root Cause Analysis

**Backend logs showed:**
```
sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation)
invalid input value for enum processingstatus: "COMPLETED"
LINE 3: WHERE articles.processing_status = 'COMPLETED' ...
```

**The Issue:**
Three endpoints in [backend/app/routes/feed.py](../backend/app/routes/feed.py) were using string literals instead of the proper `ProcessingStatus` enum:

```python
# ❌ Wrong - string literal
.where(Article.processing_status == "completed")
```

The Python enum `ProcessingStatus.COMPLETED` has the value `"completed"` (lowercase), but when used as a string literal, SQLAlchemy couldn't properly convert it to match the PostgreSQL enum type.

### The Fix

**Changed:** [backend/app/routes/feed.py](../backend/app/routes/feed.py)

1. **Added import** (line 11):
```python
from ..models import (
    ...,
    ProcessingStatus  # ← Added
)
```

2. **Fixed three locations** (lines 71, 160, 182):
```python
# ✅ Correct - use enum
.where(Article.processing_status == ProcessingStatus.COMPLETED)
```

### Why This Fixed the E2E Test

**Before fix:**
```
User clicks "Feed" → Frontend requests /feed/articles
→ Backend query fails with enum error
→ 500 error returned
→ Frontend shows error (no "Article Feed" heading)
→ E2E test timeout ❌
```

**After fix:**
```
User clicks "Feed" → Frontend requests /feed/articles
→ Backend properly uses ProcessingStatus.COMPLETED enum
→ PostgreSQL accepts query
→ 200 OK with article data
→ Frontend renders feed with heading
→ E2E test finds heading ✅
```

### Key Lessons

1. **Always use enums**: Don't use string literals when enums are defined
2. **Database enum compatibility**: SQLAlchemy needs proper enum types for PostgreSQL
3. **E2E tests catch integration issues**: Unit tests might not catch this type of database-level error
4. **Check backend logs**: E2E test failures often stem from API errors, not frontend issues

### Related Code

- **Enum definition**: [backend/app/models.py:9-13](../backend/app/models.py)
- **Fixed endpoints**: [backend/app/routes/feed.py:71,160,182](../backend/app/routes/feed.py)
- **E2E test**: [frontend/e2e/user-journey.spec.ts:20-121](../frontend/e2e/user-journey.spec.ts)

---

## Maintenance

### When to Update This Document

- New navigation patterns are discovered
- CI failures reveal timing issues
- Playwright version updates change behavior
- New Next.js features affect hydration
- Real-world bugs are fixed that demonstrate important concepts

### Related Documentation

- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Next.js Testing Guide](https://nextjs.org/docs/testing)
- [TESTING.md](./TESTING.md) - General testing guide
- [CLAUDE.md](../CLAUDE.md) - Project context for AI assistants
- [API.md](./API.md) - Backend API reference

---

**Last Updated:** 2025-10-10
**Maintained by:** AI assistants working on Pulse
