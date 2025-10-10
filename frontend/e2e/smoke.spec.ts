import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('can reach the landing page', async ({ page }) => {
    const response = await page.goto('/');

    // Check that page loaded successfully
    expect(response?.status()).toBe(200);

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Take a screenshot for debugging
    await page.screenshot({ path: 'smoke-test-landing.png', fullPage: true });

    // Check that we got some content
    const content = await page.content();
    console.log('Page title:', await page.title());
    console.log('Page URL:', page.url());
    console.log('Content length:', content.length);

    // Very basic check - page should have some HTML
    expect(content.length).toBeGreaterThan(100);
  });

  test('can reach the signup page', async ({ page }) => {
    const response = await page.goto('/signup');

    expect(response?.status()).toBe(200);
    await page.waitForLoadState('networkidle');

    const content = await page.content();
    console.log('Signup page URL:', page.url());
    console.log('Content length:', content.length);

    expect(content.length).toBeGreaterThan(100);
  });

  test('can reach the login page', async ({ page }) => {
    const response = await page.goto('/login');

    expect(response?.status()).toBe(200);
    await page.waitForLoadState('networkidle');

    const content = await page.content();
    console.log('Login page URL:', page.url());
    console.log('Content length:', content.length);

    expect(content.length).toBeGreaterThan(100);
  });

  test('backend API is accessible', async ({ request }) => {
    const response = await request.get('http://localhost:8000/docs');
    expect(response.status()).toBe(200);
    console.log('Backend /docs returned:', response.status());
  });

  test('can fetch topics from API', async ({ request }) => {
    const response = await request.get('http://localhost:8000/preferences/topics');
    expect(response.status()).toBe(200);
    const data = await response.json();
    console.log('Topics API returned:', data);
  });
});
