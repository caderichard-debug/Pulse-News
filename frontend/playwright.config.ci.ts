import { defineConfig, devices } from '@playwright/test';

/**
 * CI-specific Playwright configuration
 * This config assumes the web server is already running
 */
export default defineConfig({
  testDir: './e2e',
  /* Run tests in files in parallel */
  fullyParallel: false,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: true,
  /* Retry on CI */
  retries: 2,
  /* Single worker on CI to avoid conflicts */
  workers: 1,
  /* Reporter to use */
  reporter: [['html'], ['list']],
  /* Shared settings */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:3000',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Shorter timeouts for CI */
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  /* Global timeout for each test */
  timeout: 60000,

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* DO NOT auto-start web server in CI - it's managed externally */
});
