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
 */
export async function gotoAndWait(page: Page, url: string) {
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await waitForHydration(page);
}
