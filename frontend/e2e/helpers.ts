import { Page } from '@playwright/test';

/**
 * Wait for Next.js to finish hydrating the page
 */
export async function waitForHydration(page: Page) {
  // Wait for DOM to be ready
  await page.waitForLoadState('domcontentloaded');

  // Wait for Next.js to be ready
  await page.waitForFunction(() => {
    // @ts-ignore
    return window.next?.router?.isReady === true || document.readyState === 'complete';
  }, { timeout: 10000 });

  // Wait a bit for React to hydrate (networkidle can be unreliable in CI)
  await page.waitForTimeout(500);
}

/**
 * Navigate to a page and wait for it to be fully ready
 * Includes retry logic for CI environments where navigation can be flaky
 */
export async function gotoAndWait(page: Page, url: string, retries = 3) {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await page.goto(url, {
        waitUntil: 'domcontentloaded',
        timeout: 30000 // Increase timeout for CI
      });
      await waitForHydration(page);
      return; // Success!
    } catch (error) {
      lastError = error as Error;
      console.log(`Navigation attempt ${attempt} failed: ${error}`);

      if (attempt < retries) {
        // Wait before retrying
        await page.waitForTimeout(1000);
      }
    }
  }

  // All retries failed
  throw new Error(`Failed to navigate to ${url} after ${retries} attempts. Last error: ${lastError?.message}`);
}
