/**
 * E2E tests — Sidebar navigation and page routing
 *
 * Covers: sidebar visible, nav links work, active state highlights correct item,
 * collapsible sections.
 */

import { test, expect } from "@playwright/test";

// Reuse admin cookie saved by global-setup.ts
test.use({ storageState: "tests/.auth/admin.json" });

test.describe("Desktop sidebar", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/home");
    // Wait for the user footer (logout button) in the sidebar — this only renders after
    // React hydration AND auth/me resolves, guaranteeing sidebar event handlers are live.
    await page.getByRole("button", { name: "登出" }).waitFor({ state: "visible", timeout: 30_000 });
  });

  test("sidebar is visible on desktop viewport", async ({ page }) => {
    await expect(page.getByRole("complementary")).toBeVisible(); // <aside>
  });

  test("sidebar shows Project Nexus brand", async ({ page }) => {
    // Scope to sidebar to avoid matching "系統管理員 · Project Nexus" on the home page
    const sidebar = page.getByRole("complementary");
    await expect(sidebar.getByRole("heading", { name: "Project Nexus" })).toBeVisible();
  });

  test("sidebar shows 主畫面 link", async ({ page }) => {
    await expect(page.getByRole("link", { name: /主畫面/ })).toBeVisible();
  });

  test("clicking 商機 Pipeline navigates to /deals", async ({ page }) => {
    await page.getByRole("link", { name: /商機 Pipeline/ }).click();
    await page.waitForURL("**/deals", { timeout: 8_000 });
    expect(page.url()).toContain("/deals");
  });

  test("clicking 關係網 navigates to /contacts", async ({ page }) => {
    // Scope to sidebar to avoid matching the home page card
    await page.getByRole("complementary").getByRole("link", { name: "關係網", exact: true }).click();
    await page.waitForURL("**/contacts", { timeout: 8_000 });
    expect(page.url()).toContain("/contacts");
  });

  test("active link is highlighted on /deals", async ({ page }) => {
    await page.goto("/deals");
    const activeLink = page.getByRole("link", { name: /商機 Pipeline/ });
    // Active links have blue-500 styling
    await expect(activeLink).toHaveClass(/text-blue-500|bg-blue-500/);
  });

  test("sidebar hides on mobile viewport", async ({ page }) => {
    // Shrink viewport — beforeEach already loaded /home at 1280px
    await page.setViewportSize({ width: 375, height: 812 });
    const sidebar = page.getByRole("complementary");
    // Sidebar uses hidden md:flex — should not be visible on mobile
    await expect(sidebar).toBeHidden({ timeout: 5_000 });
  });

  test("業務與銷售 section is collapsible", async ({ page }) => {
    // Scope to sidebar to avoid matching home page headings
    const sidebar = page.getByRole("complementary");

    // Section header button
    const sectionBtn = sidebar.getByRole("button", { name: /業務與銷售/ });
    await expect(sectionBtn).toBeVisible({ timeout: 10_000 });

    // Deals link should initially be visible
    const dealsLink = sidebar.getByRole("link", { name: /商機 Pipeline/ });
    await expect(dealsLink).toBeVisible();

    // Click to collapse — wait for animation/state to settle
    await sectionBtn.click();
    await expect(dealsLink).toBeHidden({ timeout: 8_000 });

    // Click again to expand
    await sectionBtn.click();
    await expect(dealsLink).toBeVisible({ timeout: 8_000 });
  });
});
