# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Login page >> login with wrong password → Chinese error message
- Location: tests/e2e/auth.spec.ts:32:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('帳號或密碼錯誤')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for getByText('帳號或密碼錯誤')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e3]:
    - generic [ref=e4]:
      - heading "Project Nexus" [level=1] [ref=e5]
      - paragraph [ref=e6]: B2B 戰略控制台
    - generic [ref=e7]:
      - generic [ref=e8]:
        - generic [ref=e9]: 電子郵件
        - textbox "電子郵件" [active] [ref=e10]:
          - /placeholder: you@company.com
      - generic [ref=e11]:
        - generic [ref=e12]: 密碼
        - textbox "密碼" [ref=e13]:
          - /placeholder: ••••••••
      - button "登入" [ref=e14] [cursor=pointer]:
        - img [ref=e15]
        - text: 登入
  - button "Open Next.js Dev Tools" [ref=e23] [cursor=pointer]:
    - img [ref=e24]
  - alert [ref=e27]
```

# Test source

```ts
  1  | /**
  2  |  * E2E tests — Authentication flows
  3  |  *
  4  |  * Covers: login success, login failure (Chinese error), logout redirect,
  5  |  * unauthenticated redirect to /login.
  6  |  */
  7  | 
  8  | import { test, expect } from "@playwright/test";
  9  | 
  10 | const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL ?? "admin@nexus.local";
  11 | const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD ?? "admin123";
  12 | 
  13 | test.describe("Login page", () => {
  14 |   test.beforeEach(async ({ page }) => {
  15 |     await page.goto("/login");
  16 |   });
  17 | 
  18 |   test("renders email and password fields", async ({ page }) => {
  19 |     await expect(page.locator('input[type="email"]')).toBeVisible();
  20 |     await expect(page.locator('input[type="password"]')).toBeVisible();
  21 |   });
  22 | 
  23 |   test("login with valid credentials → redirected to /home", async ({ page }) => {
  24 |     await page.locator('input[type="email"]').fill(ADMIN_EMAIL);
  25 |     await page.locator('input[type="password"]').fill(ADMIN_PASSWORD);
  26 |     await page.getByRole("button", { name: /登入|login/i }).click();
  27 | 
  28 |     await page.waitForURL("**/home", { timeout: 10_000 });
  29 |     expect(page.url()).toContain("/home");
  30 |   });
  31 | 
  32 |   test("login with wrong password → Chinese error message", async ({ page }) => {
  33 |     await page.locator('input[type="email"]').fill(ADMIN_EMAIL);
  34 |     await page.locator('input[type="password"]').fill("wrongpassword");
  35 |     await page.getByRole("button", { name: /登入|login/i }).click();
  36 | 
> 37 |     await expect(page.getByText("帳號或密碼錯誤")).toBeVisible({ timeout: 10_000 });
     |                                             ^ Error: expect(locator).toBeVisible() failed
  38 |   });
  39 | 
  40 |   test("login with unknown email → error message shown", async ({ page }) => {
  41 |     await page.locator('input[type="email"]').fill("nobody@example.com");
  42 |     await page.locator('input[type="password"]').fill("whatever");
  43 |     await page.getByRole("button", { name: /登入|login/i }).click();
  44 | 
  45 |     await expect(page.getByText("帳號或密碼錯誤")).toBeVisible({ timeout: 10_000 });
  46 |   });
  47 | });
  48 | 
  49 | test.describe("Protected routes", () => {
  50 |   test("accessing /home without auth redirects to /login", async ({ page }) => {
  51 |     await page.goto("/home");
  52 |     await page.waitForURL("**/login", { timeout: 5_000 });
  53 |     expect(page.url()).toContain("/login");
  54 |   });
  55 | 
  56 |   test("accessing /deals without auth redirects to /login", async ({ page }) => {
  57 |     await page.goto("/deals");
  58 |     await page.waitForURL("**/login", { timeout: 5_000 });
  59 |     expect(page.url()).toContain("/login");
  60 |   });
  61 | });
  62 | 
  63 | test.describe("Logout", () => {
  64 |   test.beforeEach(async ({ page }) => {
  65 |     // Login first
  66 |     await page.goto("/login");
  67 |     await page.locator('input[type="email"]').fill(ADMIN_EMAIL);
  68 |     await page.locator('input[type="password"]').fill(ADMIN_PASSWORD);
  69 |     await page.getByRole("button", { name: /登入|login/i }).click();
  70 |     await page.waitForURL("**/home", { timeout: 10_000 });
  71 |   });
  72 | 
  73 |   test("logout redirects to /login (no blank page)", async ({ page }) => {
  74 |     // Find and click logout button
  75 |     const logoutBtn = page.getByRole("button", { name: /登出|logout/i });
  76 |     await expect(logoutBtn).toBeVisible({ timeout: 10_000 });
  77 |     await logoutBtn.click();
  78 | 
  79 |     await page.waitForURL("**/login", { timeout: 10_000 });
  80 |     expect(page.url()).toContain("/login");
  81 |     // Ensure page is not blank
  82 |     await expect(page.locator("body")).not.toBeEmpty();
  83 |   });
  84 | });
  85 | 
```