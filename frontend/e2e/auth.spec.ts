import { test, expect } from '@playwright/test';
import { gotoAndWait } from './helpers';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the home page and wait for hydration
    await gotoAndWait(page, '/');
  });

  test('should display landing page correctly', async ({ page }) => {
    // Check for hero section
    await expect(page.getByRole('heading', { name: /pulse/i })).toBeVisible();

    // Check for CTA buttons
    await expect(page.getByRole('link', { name: /get started/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /log in/i })).toBeVisible();
  });

  test('should navigate to signup page', async ({ page }) => {
    // Click "Get Started" button
    await page.getByRole('link', { name: /get started/i }).first().click();

    // Wait for navigation and hydration
    await page.waitForURL(/\/signup/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');

    // Wait for the heading to be visible (indicates page is fully loaded)
    await page.getByRole('heading', { name: /create.*account/i }).waitFor({ state: 'visible', timeout: 10000 });

    // Should be on signup page
    await expect(page).toHaveURL(/\/signup/);
    await expect(page.getByRole('heading', { name: /create.*account/i })).toBeVisible();
  });

  test('should navigate to login page', async ({ page }) => {
    // Click "Log In" button
    await page.getByRole('link', { name: /log in/i }).first().click();

    // Wait for navigation and hydration
    await page.waitForURL(/\/login/, { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');

    // Wait for the heading to be visible (indicates page is fully loaded)
    await page.getByRole('heading', { name: /welcome back/i }).waitFor({ state: 'visible', timeout: 10000 });

    // Should be on login page
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
  });

  test('should complete full signup flow', async ({ page }) => {
    // Navigate to signup and wait for hydration
    await gotoAndWait(page, '/signup');

    // Fill in user details (Step 1)
    const timestamp = Date.now();
    const email = `test${timestamp}@example.com`;

    await page.getByLabel(/name/i).fill('Test User');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password/i).first().fill('SecurePassword123!');
    await page.getByLabel(/confirm password/i).fill('SecurePassword123!');

    // Click next to go to topic selection
    await page.getByRole('button', { name: /continue/i }).click();

    // Step 2: Choose topics
    await expect(page.getByRole('heading', { name: /choose.*topics/i })).toBeVisible();

    // Select at least one topic (if topics are available)
    const topicCheckboxes = page.getByRole('checkbox');
    const checkboxCount = await topicCheckboxes.count();

    if (checkboxCount > 0) {
      await topicCheckboxes.first().check();
    } else {
      console.log('No topics available - skipping topic selection');
    }

    // Complete signup
    await page.getByRole('button', { name: /create account/i }).click();

    // Should redirect to preferences page
    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });
  });

  test('should login with valid credentials', async ({ page }) => {
    // First, create an account
    await gotoAndWait(page, '/signup');

    const timestamp = Date.now();
    const email = `login${timestamp}@example.com`;
    const password = 'LoginPassword123!';

    await page.getByLabel(/name/i).fill('Login User');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password/i).first().fill(password);
    await page.getByLabel(/confirm password/i).fill(password);
    await page.getByRole('button', { name: /continue/i }).click();

    // Wait for topic selection page
    await page.waitForLoadState('networkidle');

    // Select a topic if available
    const checkboxes = page.getByRole('checkbox');
    const count = await checkboxes.count();
    if (count > 0) {
      await checkboxes.first().check();
    }

    await page.getByRole('button', { name: /create account/i }).click();

    // Wait for redirect and logout
    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });
    await page.getByRole('button', { name: /logout/i }).click();

    // Now login
    await gotoAndWait(page, '/login');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole('button', { name: /log in/i }).click();

    // Should redirect to feed (default after login)
    await expect(page).toHaveURL(/\/feed/, { timeout: 10000 });
  });

  test('should show error for invalid login credentials', async ({ page }) => {
    await gotoAndWait(page, '/login');

    await page.getByLabel(/email/i).fill('nonexistent@example.com');
    await page.getByLabel(/password/i).fill('WrongPassword123!');
    await page.getByRole('button', { name: /log in/i }).click();

    // Should show error message (backend returns "Incorrect email or password")
    await expect(page.getByText(/incorrect.*email.*password/i)).toBeVisible({ timeout: 10000 });
  });

  test('should validate password requirements on signup', async ({ page }) => {
    await gotoAndWait(page, '/signup');

    await page.getByLabel(/name/i).fill('Test User');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/^password/i).first().fill('short');
    await page.getByLabel(/confirm password/i).fill('short');

    await page.getByRole('button', { name: /continue/i }).click();

    // Should show validation error
    await expect(page.getByText(/password.*8.*characters/i)).toBeVisible();
  });

  test('should validate password match on signup', async ({ page }) => {
    await gotoAndWait(page, '/signup');

    await page.getByLabel(/name/i).fill('Test User');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/^password/i).first().fill('SecurePassword123!');
    await page.getByLabel(/confirm password/i).fill('DifferentPassword123!');

    await page.getByRole('button', { name: /continue/i }).click();

    // Should show validation error
    await expect(page.getByText(/passwords.*match/i)).toBeVisible();
  });

  test('should prevent duplicate email registration', async ({ page }) => {
    const email = `duplicate${Date.now()}@example.com`;

    // First registration
    await gotoAndWait(page, '/signup');
    await page.getByLabel(/name/i).fill('First User');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password/i).first().fill('Password123!');
    await page.getByLabel(/confirm password/i).fill('Password123!');
    await page.getByRole('button', { name: /continue/i }).click();

    // Wait for topic selection
    await page.waitForLoadState('networkidle');

    // Select topic if available
    const checkboxes1 = page.getByRole('checkbox');
    const count1 = await checkboxes1.count();
    if (count1 > 0) {
      await checkboxes1.first().check();
    }

    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page).toHaveURL(/\/preferences/, { timeout: 10000 });
    await page.getByRole('button', { name: /logout/i }).click();

    // Try to register again with same email
    await gotoAndWait(page, '/signup');
    await page.getByLabel(/name/i).fill('Second User');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/^password/i).first().fill('Password123!');
    await page.getByLabel(/confirm password/i).fill('Password123!');
    await page.getByRole('button', { name: /continue/i }).click();

    // Wait for topic selection
    await page.waitForLoadState('networkidle');

    // Select topic if available
    const checkboxes2 = page.getByRole('checkbox');
    const count2 = await checkboxes2.count();
    if (count2 > 0) {
      await checkboxes2.first().check();
    }

    await page.getByRole('button', { name: /create account/i }).click();

    // Should show error (backend returns "Email already registered")
    await expect(page.getByText(/email.*already.*registered/i)).toBeVisible();
  });
});
