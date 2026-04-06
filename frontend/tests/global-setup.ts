/**
 * Playwright global setup — saves admin auth state to disk once.
 * All tests that need auth import storageState from auth-state.json.
 */

import { chromium } from "@playwright/test";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3002";
const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL ?? "admin@nexus.local";
const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD ?? "admin123";

export default async function globalSetup() {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto(`${BASE_URL}/login`);
  await page.locator('input[type="email"]').fill(ADMIN_EMAIL);
  await page.locator('input[type="password"]').fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: /登入|login/i }).click();
  await page.waitForURL(`${BASE_URL}/home`, { timeout: 15_000 });

  // Save storage state (cookies) for reuse in tests
  await context.storageState({ path: "tests/.auth/admin.json" });
  await browser.close();
}
