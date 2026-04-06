/**
 * E2E tests — Authentication flows
 *
 * Covers: login success, login failure (Chinese error), logout redirect,
 * unauthenticated redirect to /login.
 */

import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL ?? "admin@nexus.local";
const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD ?? "admin123";

test.describe("Login page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
  });

  test("renders email and password fields", async ({ page }) => {
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test("login with valid credentials → redirected to /home", async ({ page }) => {
    await page.locator('input[type="email"]').fill(ADMIN_EMAIL);
    await page.locator('input[type="password"]').fill(ADMIN_PASSWORD);
    await page.getByRole("button", { name: /登入|login/i }).click();

    await page.waitForURL("**/home", { timeout: 20_000 });
    expect(page.url()).toContain("/home");
  });

  test("login with wrong password → Chinese error message", async ({ page }) => {
    await page.locator('input[type="email"]').fill(ADMIN_EMAIL);
    await page.locator('input[type="password"]').fill("wrongpassword");
    await page.getByRole("button", { name: /登入|login/i }).click();

    await expect(page.getByText("帳號或密碼錯誤")).toBeVisible({ timeout: 10_000 });
  });

  test("login with unknown email → error message shown", async ({ page }) => {
    await page.locator('input[type="email"]').fill("nobody@example.com");
    await page.locator('input[type="password"]').fill("whatever");
    await page.getByRole("button", { name: /登入|login/i }).click();

    await expect(page.getByText("帳號或密碼錯誤")).toBeVisible({ timeout: 15_000 });
  });
});

test.describe("Protected routes", () => {
  test("accessing /home without auth redirects to /login", async ({ page }) => {
    await page.goto("/home");
    await page.waitForURL("**/login", { timeout: 5_000 });
    expect(page.url()).toContain("/login");
  });

  test("accessing /deals without auth redirects to /login", async ({ page }) => {
    await page.goto("/deals");
    await page.waitForURL("**/login", { timeout: 5_000 });
    expect(page.url()).toContain("/login");
  });
});

test.describe("Logout", () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto("/login");
    await page.locator('input[type="email"]').fill(ADMIN_EMAIL);
    await page.locator('input[type="password"]').fill(ADMIN_PASSWORD);
    await page.getByRole("button", { name: /登入|login/i }).click();
    await page.waitForURL("**/home", { timeout: 20_000 });
  });

  test("logout redirects to /login (no blank page)", async ({ page }) => {
    // The logout button only renders after React hydration + auth/me resolves
    const logoutBtn = page.getByRole("button", { name: "登出" });
    await expect(logoutBtn).toBeVisible({ timeout: 20_000 });
    await logoutBtn.click();

    await page.waitForURL("**/login", { timeout: 10_000 });
    expect(page.url()).toContain("/login");
    // Ensure page is not blank
    await expect(page.locator("body")).not.toBeEmpty();
  });
});
