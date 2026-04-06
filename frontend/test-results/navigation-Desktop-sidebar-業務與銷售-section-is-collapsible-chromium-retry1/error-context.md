# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navigation.spec.ts >> Desktop sidebar >> 業務與銷售 section is collapsible
- Location: tests/e2e/navigation.spec.ts:59:7

# Error details

```
Error: expect(locator).toBeHidden() failed

Locator:  getByRole('link', { name: /商機 Pipeline/ })
Expected: hidden
Received: visible
Timeout:  5000ms

Call log:
  - Expect "toBeHidden" with timeout 5000ms
  - waiting for getByRole('link', { name: /商機 Pipeline/ })
    9 × locator resolved to <a href="/deals" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-200 cursor-pointer text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">…</a>
      - unexpected value "visible"

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e2]:
    - complementary [ref=e3]:
      - generic [ref=e4]:
        - heading "Project Nexus" [level=1] [ref=e5]
        - paragraph [ref=e6]: Strategic Console
      - navigation [ref=e7]:
        - generic [ref=e9]:
          - link "主畫面" [ref=e10] [cursor=pointer]:
            - /url: /home
            - img [ref=e11]
            - text: 主畫面
          - link "控制台" [ref=e14] [cursor=pointer]:
            - /url: /dashboard
            - img [ref=e15]
            - text: 控制台
        - generic [ref=e20]:
          - button "業務與銷售" [active] [ref=e21] [cursor=pointer]:
            - img [ref=e23]
            - generic [ref=e25]: 業務與銷售
          - generic [ref=e26]:
            - link "商機 Pipeline" [ref=e27] [cursor=pointer]:
              - /url: /deals
              - img [ref=e28]
              - text: 商機 Pipeline
            - link "行事曆" [ref=e31] [cursor=pointer]:
              - /url: /calendar
              - img [ref=e32]
              - text: 行事曆
            - link "關係網" [ref=e34] [cursor=pointer]:
              - /url: /contacts
              - img [ref=e35]
              - text: 關係網
            - link "陌開工作台" [ref=e39] [cursor=pointer]:
              - /url: /outreach
              - img [ref=e40]
              - text: 陌開工作台
        - generic [ref=e44]:
          - button "情報與研究" [ref=e45] [cursor=pointer]:
            - img [ref=e47]
            - generic [ref=e49]: 情報與研究
          - generic [ref=e50]:
            - link "新增情報" [ref=e51] [cursor=pointer]:
              - /url: /capture
              - img [ref=e52]
              - text: 新增情報
            - link "情報紀錄" [ref=e53] [cursor=pointer]:
              - /url: /intel
              - img [ref=e54]
              - text: 情報紀錄
            - link "知識庫" [ref=e56] [cursor=pointer]:
              - /url: /knowledge
              - img [ref=e57]
              - text: 知識庫
            - link "補助案" [ref=e65] [cursor=pointer]:
              - /url: /subsidies
              - img [ref=e66]
              - text: 補助案
            - link "政府標案" [ref=e68] [cursor=pointer]:
              - /url: /tenders
              - img [ref=e69]
              - text: 政府標案
        - generic [ref=e75]:
          - button "法務與行政" [ref=e76] [cursor=pointer]:
            - img [ref=e78]
            - generic [ref=e80]: 法務與行政
          - link "文件追蹤" [ref=e82] [cursor=pointer]:
            - /url: /documents
            - img [ref=e83]
            - text: 文件追蹤
    - main [ref=e88]
  - button [ref=e91] [cursor=pointer]:
    - img [ref=e92]
```

# Test source

```ts
  1  | /**
  2  |  * E2E tests — Sidebar navigation and page routing
  3  |  *
  4  |  * Covers: sidebar visible, nav links work, active state highlights correct item,
  5  |  * collapsible sections.
  6  |  */
  7  | 
  8  | import { test, expect } from "@playwright/test";
  9  | 
  10 | // Reuse admin cookie saved by global-setup.ts
  11 | test.use({ storageState: "tests/.auth/admin.json" });
  12 | 
  13 | test.describe("Desktop sidebar", () => {
  14 |   test.beforeEach(async ({ page }) => {
  15 |     await page.goto("/home");
  16 |     await page.setViewportSize({ width: 1280, height: 800 });
  17 |   });
  18 | 
  19 |   test("sidebar is visible on desktop viewport", async ({ page }) => {
  20 |     await expect(page.getByRole("complementary")).toBeVisible(); // <aside>
  21 |   });
  22 | 
  23 |   test("sidebar shows Project Nexus brand", async ({ page }) => {
  24 |     await expect(page.getByText("Project Nexus")).toBeVisible();
  25 |   });
  26 | 
  27 |   test("sidebar shows 主畫面 link", async ({ page }) => {
  28 |     await expect(page.getByRole("link", { name: /主畫面/ })).toBeVisible();
  29 |   });
  30 | 
  31 |   test("clicking 商機 Pipeline navigates to /deals", async ({ page }) => {
  32 |     await page.getByRole("link", { name: /商機 Pipeline/ }).click();
  33 |     await page.waitForURL("**/deals", { timeout: 8_000 });
  34 |     expect(page.url()).toContain("/deals");
  35 |   });
  36 | 
  37 |   test("clicking 關係網 navigates to /contacts", async ({ page }) => {
  38 |     // Scope to sidebar to avoid matching the home page card
  39 |     await page.getByRole("complementary").getByRole("link", { name: "關係網", exact: true }).click();
  40 |     await page.waitForURL("**/contacts", { timeout: 8_000 });
  41 |     expect(page.url()).toContain("/contacts");
  42 |   });
  43 | 
  44 |   test("active link is highlighted on /deals", async ({ page }) => {
  45 |     await page.goto("/deals");
  46 |     const activeLink = page.getByRole("link", { name: /商機 Pipeline/ });
  47 |     // Active links have blue-500 styling
  48 |     await expect(activeLink).toHaveClass(/text-blue-500|bg-blue-500/);
  49 |   });
  50 | 
  51 |   test("sidebar hides on mobile viewport", async ({ page }) => {
  52 |     await page.goto("/home");
  53 |     await page.setViewportSize({ width: 375, height: 812 });
  54 |     const sidebar = page.getByRole("complementary");
  55 |     // Sidebar uses hidden md:flex — should not be visible on mobile
  56 |     await expect(sidebar).toBeHidden();
  57 |   });
  58 | 
  59 |   test("業務與銷售 section is collapsible", async ({ page }) => {
  60 |     // Section header button
  61 |     const sectionBtn = page.getByRole("button", { name: /業務與銷售/ });
  62 |     await expect(sectionBtn).toBeVisible();
  63 | 
  64 |     // Deals link should initially be visible
  65 |     const dealsLink = page.getByRole("link", { name: /商機 Pipeline/ });
  66 |     await expect(dealsLink).toBeVisible();
  67 | 
  68 |     // Click to collapse
  69 |     await sectionBtn.click();
> 70 |     await expect(dealsLink).toBeHidden();
     |                             ^ Error: expect(locator).toBeHidden() failed
  71 | 
  72 |     // Click again to expand
  73 |     await sectionBtn.click();
  74 |     await expect(dealsLink).toBeVisible();
  75 |   });
  76 | });
  77 | 
```