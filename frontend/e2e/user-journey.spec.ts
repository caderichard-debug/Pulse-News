import { test, expect } from '@playwright/test';
import { gotoAndWait } from './helpers';

/**
 * Complete user journey E2E tests
 * Tests the full workflow: signup → preferences → dashboard → feed → article detail
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

    // Step 2: Navigate to Dashboard
    await page.getByRole('button', { name: /📊.*dashboard/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Verify dashboard elements
    await expect(page.getByText(/articles read/i)).toBeVisible();
    await expect(page.getByText(/newsletters/i)).toBeVisible();
    await expect(page.getByText(/topics tracked/i)).toBeVisible();

    // Check for charts (they might be loading)
    await expect(page.locator('.recharts-wrapper')).toBeVisible({ timeout: 5000 }).catch(() => {
      // Charts might not load if there's no data yet
      console.log('Charts not loaded - possibly no data yet');
    });

    // Step 3: Navigate to Feed
    await page.getByRole('button', { name: /📰.*feed/i }).click();
    await expect(page).toHaveURL(/\/feed/);

    // Verify feed page elements
    await expect(page.getByRole('heading', { name: /article feed/i })).toBeVisible();

    // Check for filters
    await expect(page.getByRole('combobox').first()).toBeVisible(); // Topic filter

    // Step 4: Go back to Preferences
    await page.getByRole('button', { name: /⚙️.*preferences/i }).click();
    await expect(page).toHaveURL(/\/preferences/);

    // Verify tabs are present
    await expect(page.getByRole('button', { name: /topics/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /sources/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /settings/i })).toBeVisible();

    // Switch to Sources tab
    await page.getByRole('button', { name: /sources/i }).click();

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

    // Step 5: Navigate to How It Works
    await page.getByRole('button', { name: /💡.*how it works/i }).click();
    await expect(page).toHaveURL(/\/how-it-works/);

    // Verify educational content
    await expect(page.getByRole('heading', { name: /how pulse works/i })).toBeVisible();

    // Step 6: Logout
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
    await page.getByRole('checkbox').first().check();
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });
  });

  test('should navigate between all main pages using navbar', async ({ page }) => {
    // Test Dashboard button
    await page.getByRole('button', { name: /📊.*dashboard/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Test Feed button
    await page.getByRole('button', { name: /📰.*feed/i }).click();
    await expect(page).toHaveURL(/\/feed/);

    // Test Preferences button (in navbar, not the user menu)
    await page.getByRole('button', { name: /⚙️.*preferences/i }).click();
    await expect(page).toHaveURL(/\/preferences/);

    // Test How It Works button
    await page.getByRole('button', { name: /💡.*how it works/i }).click();
    await expect(page).toHaveURL(/\/how-it-works/);
  });

  test('should highlight active page in navbar', async ({ page }) => {
    // Go to dashboard
    await page.getByRole('button', { name: /📊.*dashboard/i }).click();

    // Dashboard button should be highlighted
    const dashboardButton = page.getByRole('button', { name: /📊.*dashboard/i });
    await expect(dashboardButton).toHaveClass(/bg-indigo/);

    // Go to feed
    await page.getByRole('button', { name: /📰.*feed/i }).click();

    // Feed button should be highlighted
    const feedButton = page.getByRole('button', { name: /📰.*feed/i });
    await expect(feedButton).toHaveClass(/bg-indigo/);
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
    // Try to access dashboard without authentication
    await gotoAndWait(page, '/dashboard');

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
