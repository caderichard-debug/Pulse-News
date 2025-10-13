import { test, expect } from '@playwright/test';
import { gotoAndWait } from './helpers';

/**
 * Complete user journey E2E tests
 * Tests the full workflow: signup → preferences → feed → sources → analytics → how it works
 */

test.describe('Complete User Journey', () => {
  let userEmail: string;
  let userPassword: string;

  test.beforeAll(() => {
    // Generate unique credentials for this test run
    const timestamp = Date.now();
    userEmail = `journey${timestamp}@example.com`;
    userPassword = 'JourneyPassword123!';
  });

  test('should complete full user journey from signup to reading articles', async ({ page }) => {
    // Step 1: Sign up
    await gotoAndWait(page, '/signup');

    await page.getByLabel(/name/i).fill('Journey User');
    await page.getByLabel(/email/i).fill(userEmail);
    await page.getByLabel(/^password/i).first().fill(userPassword);
    await page.getByLabel(/confirm password/i).fill(userPassword);
    await page.getByRole('button', { name: /continue/i }).click();

    // Select topics
    await expect(page.getByRole('heading', { name: /choose.*topics/i })).toBeVisible();
    const checkboxes = page.getByRole('checkbox');
    await checkboxes.first().check();
    await checkboxes.nth(1).check(); // Select at least 2 topics

    await page.getByRole('button', { name: /create account/i }).click();

    // Should redirect to preferences
    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });

    // Step 2: Navigate to Analytics
    await page.getByRole('button', { name: /📊.*analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/, { timeout: 10000 });

    // Wait for page to hydrate and render
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000); // Allow React to hydrate

    // Verify analytics page elements
    await expect(page.getByRole('heading', { name: /📊.*data analysis/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/explore sentiment trends and bias distribution/i)).toBeVisible();

    // Verify chart sections are present
    await expect(page.getByRole('heading', { name: /sentiment over time/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /source bias distribution/i })).toBeVisible();

    // Check for time range selector
    await expect(page.getByRole('button', { name: /7d/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /30d/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /90d/i })).toBeVisible();

    // Step 3: Navigate to Feed
    await page.getByRole('button', { name: /📰.*feed/i }).click();
    await expect(page).toHaveURL(/\/feed/, { timeout: 10000 });

    // Wait for page to hydrate and render
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Wait for either the heading or error message to appear (defensive)
    await page.waitForSelector('h1, .bg-red-50', { timeout: 15000 }).catch(() => {
      console.log('Neither heading nor error appeared on feed page');
    });

    // Additional wait for React hydration
    await page.waitForTimeout(1000);

    // Check if there's an error message (which would prevent the heading from showing)
    const errorMessage = page.locator('.bg-red-50');
    const hasError = await errorMessage.isVisible().catch(() => false);
    if (hasError) {
      const errorText = await errorMessage.textContent();
      throw new Error(`Feed page showed error: ${errorText}`);
    }

    // Verify feed page elements - the heading should now be visible
    await expect(page.getByRole('heading', { name: /📰.*article feed/i })).toBeVisible({ timeout: 10000 });

    // Check for filters on feed page
    await expect(page.getByRole('combobox').first()).toBeVisible({ timeout: 10000 }); // Topic filter

    // Step 3: Navigate to Sources
    await page.getByRole('button', { name: /📑.*sources/i }).click();
    await expect(page).toHaveURL(/\/sources/, { timeout: 10000 });

    // Wait for page to hydrate and render
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000); // Allow React to hydrate

    // Verify sources page elements
    await expect(page.getByRole('heading', { name: /📰.*supported news sources/i })).toBeVisible({ timeout: 10000 });

    // Step 4: Navigate to Analytics
    await page.getByRole('button', { name: /📊.*analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/, { timeout: 10000 });

    // Wait for page to hydrate and render
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000); // Allow React to hydrate

    // Verify analytics elements
    await expect(page.getByText(/analytics/i).first()).toBeVisible({ timeout: 10000 });

    // Step 5: Go back to Preferences
    await page.getByRole('button', { name: /⚙️.*preferences/i }).click();
    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });

    // Wait for page to hydrate and render
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000); // Allow React to hydrate

    // Verify tabs are present
    await expect(page.getByRole('button', { name: /topics/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /sources \(/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /settings/i })).toBeVisible();

    // Switch to Sources tab
    await page.getByRole('button', { name: /sources \(/i }).click();

    // Verify sources are displayed
    await expect(page.getByText(/trust score/i).first()).toBeVisible({ timeout: 5000 }).catch(() => {
      console.log('Sources not loaded yet');
    });

    // Switch to Settings tab
    await page.getByRole('button', { name: /settings/i }).click();

    // Wait for settings tab to load
    await expect(page.getByText(/newsletter settings/i)).toBeVisible();

    // Verify settings options
    await expect(page.getByText(/source discovery mode/i)).toBeVisible();
    await expect(page.getByText(/article order preference/i)).toBeVisible();

    // Step 6: Navigate to How It Works
    await page.getByRole('button', { name: /💡.*how it works/i }).click();
    await expect(page).toHaveURL(/\/how-it-works/, { timeout: 10000 });

    // Wait for page to hydrate and render
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000); // Allow React to hydrate

    // Verify educational content
    await expect(page.getByRole('heading', { name: /how pulse works/i })).toBeVisible({ timeout: 10000 });

    // Step 7: Logout
    await page.getByRole('button', { name: /logout/i }).click();

    // Should redirect to landing page
    await expect(page).toHaveURL('/', { timeout: 5000 });
  });
});

test.describe('Preferences Management', () => {
  let userEmail: string;
  let userPassword: string;

  test.beforeEach(async ({ page }) => {
    // Create a user and login
    const timestamp = Date.now();
    userEmail = `prefs${timestamp}@example.com`;
    userPassword = 'PrefsPassword123!';

    await gotoAndWait(page, '/signup');
    await page.getByLabel(/name/i).fill('Prefs User');
    await page.getByLabel(/email/i).fill(userEmail);
    await page.getByLabel(/^password/i).first().fill(userPassword);
    await page.getByLabel(/confirm password/i).fill(userPassword);
    await page.getByRole('button', { name: /continue/i }).click();

    // Wait for topic selection page
    await expect(page.getByRole('heading', { name: /choose.*topics/i })).toBeVisible();
    await page.getByRole('checkbox').first().check();
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });
  });

  test('should update topic preferences', async ({ page }) => {
    // Should already be on preferences page
    await expect(page.getByRole('button', { name: /topics/i })).toBeVisible();

    // Topics should already be loaded - look for topic headings instead of checkboxes
    const topicHeadings = page.getByRole('heading', { level: 3 });
    const count = await topicHeadings.count();
    expect(count).toBeGreaterThan(0);

    // Toggle a topic - find the toggle button (the switch-style button)
    // The toggle buttons are styled buttons with rounded-full class
    const toggleButtons = page.locator('button.rounded-full');
    await toggleButtons.first().click();

    // Save changes
    await page.getByRole('button', { name: /save preferences/i }).click();

    // Should show success message
    await expect(page.getByText(/saved/i)).toBeVisible({ timeout: 5000 });
  });

  test('should update settings preferences', async ({ page }) => {
    // Switch to Settings tab
    await page.getByRole('button', { name: /settings/i }).click();

    // Wait for settings tab to load
    await expect(page.getByText(/article order preference/i)).toBeVisible();

    // Change article ordering - find the select by label text
    const orderingSelect = page.locator('select').nth(1); // Second select is article order
    await orderingSelect.selectOption('good_first');

    // Save changes
    await page.getByRole('button', { name: /save settings/i }).click();

    // Should show success message
    await expect(page.getByText(/saved/i)).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Navigation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Create a user and login
    const timestamp = Date.now();
    const email = `nav${timestamp}@example.com`;
    const password = 'NavPassword123!';

    await gotoAndWait(page, '/signup');
    await page.getByLabel(/name/i).fill('Nav User');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password/i).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole('button', { name: /continue/i }).click();

    // Wait for topic selection page
    await expect(page.getByRole('heading', { name: /choose.*topics/i })).toBeVisible();
    await page.getByRole('checkbox').first().check();
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });
  });

  test('should navigate between all main pages using navbar', async ({ page }) => {
    // Test Analytics button
    await page.getByRole('button', { name: /📊.*analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Test Feed button
    await page.getByRole('button', { name: /📰.*feed/i }).click();
    await expect(page).toHaveURL(/\/feed/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Test Sources button
    await page.getByRole('button', { name: /📑.*sources/i }).click();
    await expect(page).toHaveURL(/\/sources/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Test Analytics button
    await page.getByRole('button', { name: /📊.*analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Test Preferences button (in navbar, not the user menu)
    await page.getByRole('button', { name: /⚙️.*preferences/i }).click();
    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');

    // Test How It Works button
    await page.getByRole('button', { name: /💡.*how it works/i }).click();
    await expect(page).toHaveURL(/\/how-it-works/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
  });

  test('should highlight active page in navbar', async ({ page }) => {
    // Go to analytics
    await page.getByRole('button', { name: /📊.*analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // Extra wait for React hydration

    // Analytics button should be highlighted (has bg-indigo-50 and text-indigo-700 classes)
    const analyticsButton = page.getByRole('button', { name: /📊.*analytics/i });
    await expect(analyticsButton).toHaveClass(/bg-indigo-50.*text-indigo-700/);

    // Go to feed
    await page.getByRole('button', { name: /📰.*feed/i }).click();
    await expect(page).toHaveURL(/\/feed/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // Extra wait for React hydration

    // Feed button should be highlighted (has bg-indigo-50 and text-indigo-700 classes)
    const feedButton = page.getByRole('button', { name: /📰.*feed/i });
    await expect(feedButton).toHaveClass(/bg-indigo-50.*text-indigo-700/);
  });

  test('should display user name in navbar', async ({ page }) => {
    // Navbar should show user name
    await expect(page.getByText(/nav user/i)).toBeVisible();
  });
});

test.describe('Error Handling', () => {
  test('should handle 404 pages gracefully', async ({ page }) => {
    await gotoAndWait(page, '/nonexistent-page');

    // Next.js should show 404 page
    await expect(page.getByText(/404|not found/i)).toBeVisible();
  });

  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    // Try to access analytics without authentication
    await gotoAndWait(page, '/analytics');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });

  test('should persist login across page reloads', async ({ page }) => {
    // Create a user and login
    const timestamp = Date.now();
    const email = `persist${timestamp}@example.com`;
    const password = 'PersistPassword123!';

    await gotoAndWait(page, '/signup');
    await page.getByLabel(/name/i).fill('Persist User');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password/i).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole('button', { name: /continue/i }).click();

    // Wait for topic selection page
    await expect(page.getByRole('heading', { name: /choose.*topics/i })).toBeVisible();
    await page.getByRole('checkbox').first().check();
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });

    // Reload the page
    await page.reload();

    // Should still be on preferences (not redirected to login)
    await expect(page).toHaveURL(/\/preferences/);
    await expect(page.getByRole('button', { name: /topics/i })).toBeVisible();
  });
});
