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

  // Warm up the backend: retry /login up to 5 times with 3s gap before proceeding.
  // Prevents flakiness when the Docker container is cold after a rebuild.
  for (let attempt = 1; attempt <= 5; attempt++) {
    try {
      const res = await fetch(`${BASE_URL}/api/nx/auth/me`);
      if (res.status === 401 || res.status === 200) break; // backend is up
    } catch {
      // backend not ready yet
    }
    if (attempt < 5) await new Promise((r) => setTimeout(r, 3_000));
  }

  await page.goto(`${BASE_URL}/login`);
  await page.locator('input[type="email"]').fill(ADMIN_EMAIL);
  await page.locator('input[type="password"]').fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: /登入|login/i }).click();
  await page.waitForURL(`${BASE_URL}/home`, { timeout: 30_000 });

  // Wait for sidebar to fully hydrate (auth/me call completes, logout button appears)
  await page.getByRole("button", { name: "登出" }).waitFor({ state: "visible", timeout: 20_000 });

  // Save storage state (cookies) for reuse in tests
  await context.storageState({ path: "tests/.auth/admin.json" });
  await browser.close();
}
