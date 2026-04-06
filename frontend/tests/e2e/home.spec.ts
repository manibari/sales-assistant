/**
 * E2E tests — Home screen role-based section visibility
 *
 * Uses pre-saved admin auth state (from global setup) — no login per test.
 * Covers: 5 sections visible, card links correct, coming-soon cards not clickable.
 */

import { test, expect } from "@playwright/test";

// Reuse admin cookie saved by global-setup.ts
test.use({ storageState: "tests/.auth/admin.json" });

test.describe("Home screen — admin role", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/home");
    // Wait for page to fully load — auth/me call may take a moment
    await expect(page.getByRole("heading", { name: /歡迎回來/ })).toBeVisible({ timeout: 20_000 });
  });

  test("shows 業務與銷售 section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "業務與銷售" })).toBeVisible();
  });

  test("shows 情報與研究 section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "情報與研究" })).toBeVisible();
  });

  test("shows 法務與行政 section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "法務與行政" })).toBeVisible();
  });

  test("shows 財務管理 section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "財務管理" })).toBeVisible();
  });

  test("shows 系統管理 section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "系統管理" })).toBeVisible();
  });

  test("商機管理 card links to /deals", async ({ page }) => {
    const card = page.getByRole("link", { name: /商機管理/ });
    await expect(card).toBeVisible();
    await expect(card).toHaveAttribute("href", "/deals");
  });

  test("coming-soon cards are not links", async ({ page }) => {
    // Scroll to bottom to ensure all cards are in DOM
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    const badges = page.locator("text=即將開放");
    await expect(badges.first()).toBeVisible({ timeout: 8_000 });
    const count = await badges.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const isInsideLink = await badges.nth(i).evaluate((el) => {
        let node: Element | null = el;
        while (node) {
          if (node.tagName.toLowerCase() === "a") return true;
          node = node.parentElement;
        }
        return false;
      });
      expect(isInsideLink).toBe(false);
    }
  });
});

test.describe("Home screen — welcome message", () => {
  test.use({ storageState: "tests/.auth/admin.json" });

  test("shows 歡迎回來 with user name", async ({ page }) => {
    await page.goto("/home");
    await expect(page.getByRole("heading", { name: /歡迎回來/ })).toBeVisible();
    await expect(page.getByText("系統管理員 · Project Nexus")).toBeVisible();
  });
});
