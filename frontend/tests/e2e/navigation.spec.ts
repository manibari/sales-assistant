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
    await page.goto("/home");
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test("sidebar is visible on desktop viewport", async ({ page }) => {
    await expect(page.getByRole("complementary")).toBeVisible(); // <aside>
  });

  test("sidebar shows Project Nexus brand", async ({ page }) => {
    await expect(page.getByText("Project Nexus")).toBeVisible();
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
    await page.goto("/home");
    await page.setViewportSize({ width: 375, height: 812 });
    const sidebar = page.getByRole("complementary");
    // Sidebar uses hidden md:flex — should not be visible on mobile
    await expect(sidebar).toBeHidden();
  });

  test("業務與銷售 section is collapsible", async ({ page }) => {
    // Section header button
    const sectionBtn = page.getByRole("button", { name: /業務與銷售/ });
    await expect(sectionBtn).toBeVisible();

    // Deals link should initially be visible
    const dealsLink = page.getByRole("link", { name: /商機 Pipeline/ });
    await expect(dealsLink).toBeVisible();

    // Click to collapse
    await sectionBtn.click();
    await expect(dealsLink).toBeHidden();

    // Click again to expand
    await sectionBtn.click();
    await expect(dealsLink).toBeVisible();
  });
});
