import { Page } from '@playwright/test';

/**
 * Wait for Next.js to finish hydrating the page
 */
export async function waitForHydration(page: Page) {
  // Wait for Next.js to be ready
  await page.waitForFunction(() => {
    // @ts-ignore
    return window.next?.router?.isReady === true || document.readyState === 'complete';
  }, { timeout: 10000 });

  // Additional wait for React hydration
  await page.waitForLoadState('networkidle');
}

/**
 * Navigate to a page and wait for it to be fully ready
 */
export async function gotoAndWait(page: Page, url: string) {
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await waitForHydration(page);
}
