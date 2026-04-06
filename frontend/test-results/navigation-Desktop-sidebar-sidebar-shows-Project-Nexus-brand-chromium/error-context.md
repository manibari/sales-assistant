# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navigation.spec.ts >> Desktop sidebar >> sidebar shows Project Nexus brand
- Location: tests/e2e/navigation.spec.ts:23:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Project Nexus')
Expected: visible
Error: strict mode violation: getByText('Project Nexus') resolved to 2 elements:
    1) <h1 class="text-lg font-bold text-slate-900 dark:text-slate-50 tracking-tight">Project Nexus</h1> aka getByRole('heading', { name: 'Project Nexus' })
    2) <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">系統管理員 · Project Nexus</p> aka getByText('系統管理員 · Project Nexus')

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('Project Nexus')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
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
          - button "業務與銷售" [ref=e21] [cursor=pointer]:
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
        - generic [ref=e87]:
          - button "系統管理" [ref=e88] [cursor=pointer]:
            - img [ref=e90]
            - generic [ref=e92]: 系統管理
          - generic [ref=e93]:
            - link "使用者管理" [ref=e94] [cursor=pointer]:
              - /url: /admin/users
              - img [ref=e95]
              - text: 使用者管理
            - link "搜尋" [ref=e100] [cursor=pointer]:
              - /url: /search
              - img [ref=e101]
              - text: 搜尋
            - link "設定" [ref=e104] [cursor=pointer]:
              - /url: /settings
              - img [ref=e105]
              - text: 設定
      - generic [ref=e108]:
        - generic [ref=e109]:
          - paragraph [ref=e110]: 管理員
          - paragraph [ref=e111]: 管理員
        - button "登出" [ref=e112] [cursor=pointer]:
          - img [ref=e113]
    - main [ref=e117]:
      - generic [ref=e119]:
        - generic [ref=e120]:
          - heading "歡迎回來，管理員" [level=1] [ref=e121]
          - paragraph [ref=e122]: 系統管理員 · Project Nexus
        - generic [ref=e123]:
          - generic [ref=e124]:
            - generic [ref=e125]: 📈
            - heading "業務與銷售" [level=2] [ref=e126]
          - generic [ref=e127]:
            - link "控制台 Pipeline 總覽、行動提醒、今日會議" [ref=e128] [cursor=pointer]:
              - /url: /dashboard
              - generic [ref=e129]:
                - img [ref=e131]
                - generic [ref=e136]:
                  - paragraph [ref=e137]: 控制台
                  - paragraph [ref=e138]: Pipeline 總覽、行動提醒、今日會議
            - link "商機管理 Deal Pipeline、MEDDIC 評估、階段推進" [ref=e139] [cursor=pointer]:
              - /url: /deals
              - generic [ref=e140]:
                - img [ref=e142]
                - generic [ref=e145]:
                  - paragraph [ref=e146]: 商機管理
                  - paragraph [ref=e147]: Deal Pipeline、MEDDIC 評估、階段推進
            - link "行事曆 會議管理、行程安排" [ref=e148] [cursor=pointer]:
              - /url: /calendar
              - generic [ref=e149]:
                - img [ref=e151]
                - generic [ref=e153]:
                  - paragraph [ref=e154]: 行事曆
                  - paragraph [ref=e155]: 會議管理、行程安排
            - link "關係網 客戶、合作夥伴、聯絡人" [ref=e156] [cursor=pointer]:
              - /url: /contacts
              - generic [ref=e157]:
                - img [ref=e159]
                - generic [ref=e163]:
                  - paragraph [ref=e164]: 關係網
                  - paragraph [ref=e165]: 客戶、合作夥伴、聯絡人
            - link "陌開工作台 冷開發工作流程" [ref=e166] [cursor=pointer]:
              - /url: /outreach
              - generic [ref=e167]:
                - img [ref=e169]
                - generic [ref=e173]:
                  - paragraph [ref=e174]: 陌開工作台
                  - paragraph [ref=e175]: 冷開發工作流程
        - generic [ref=e176]:
          - generic [ref=e177]:
            - generic [ref=e178]: ⚡
            - heading "情報與研究" [level=2] [ref=e179]
          - generic [ref=e180]:
            - link "情報系統 情資紀錄、AI 分析、知識庫" [ref=e181] [cursor=pointer]:
              - /url: /intel
              - generic [ref=e182]:
                - img [ref=e184]
                - generic [ref=e186]:
                  - paragraph [ref=e187]: 情報系統
                  - paragraph [ref=e188]: 情資紀錄、AI 分析、知識庫
            - link "知識庫 文件解析、知識檢索" [ref=e189] [cursor=pointer]:
              - /url: /knowledge
              - generic [ref=e190]:
                - img [ref=e192]
                - generic [ref=e200]:
                  - paragraph [ref=e201]: 知識庫
                  - paragraph [ref=e202]: 文件解析、知識檢索
            - link "補助案 政府補助追蹤、截止日管理" [ref=e203] [cursor=pointer]:
              - /url: /subsidies
              - generic [ref=e204]:
                - img [ref=e206]
                - generic [ref=e208]:
                  - paragraph [ref=e209]: 補助案
                  - paragraph [ref=e210]: 政府補助追蹤、截止日管理
            - link "政府標案 標案搜尋、投標追蹤" [ref=e211] [cursor=pointer]:
              - /url: /tenders
              - generic [ref=e212]:
                - img [ref=e214]
                - generic [ref=e220]:
                  - paragraph [ref=e221]: 政府標案
                  - paragraph [ref=e222]: 標案搜尋、投標追蹤
        - generic [ref=e223]:
          - generic [ref=e224]:
            - generic [ref=e225]: ⚖️
            - heading "法務與行政" [level=2] [ref=e226]
          - generic [ref=e227]:
            - link "文件追蹤 NDA、MOU、合約文件管理" [ref=e228] [cursor=pointer]:
              - /url: /documents
              - generic [ref=e229]:
                - img [ref=e231]
                - generic [ref=e235]:
                  - paragraph [ref=e236]: 文件追蹤
                  - paragraph [ref=e237]: NDA、MOU、合約文件管理
            - generic [ref=e239]:
              - img [ref=e241]
              - generic [ref=e244]:
                - paragraph [ref=e245]: 報價單
                - paragraph [ref=e246]: 建立與管理報價文件
              - generic [ref=e247]: 即將開放
            - generic [ref=e249]:
              - img [ref=e251]
              - generic [ref=e255]:
                - paragraph [ref=e256]: 合約管理
                - paragraph [ref=e257]: 合約建立、簽署追蹤
              - generic [ref=e258]: 即將開放
        - generic [ref=e259]:
          - generic [ref=e260]:
            - generic [ref=e261]: 💰
            - heading "財務管理" [level=2] [ref=e262]
          - generic [ref=e263]:
            - generic [ref=e265]:
              - img [ref=e267]
              - generic [ref=e270]:
                - paragraph [ref=e271]: 發票管理
                - paragraph [ref=e272]: 開立發票、付款追蹤
              - generic [ref=e273]: 即將開放
            - generic [ref=e275]:
              - img [ref=e277]
              - generic [ref=e280]:
                - paragraph [ref=e281]: 帳款管理
                - paragraph [ref=e282]: 應收帳款、請款追蹤
              - generic [ref=e283]: 即將開放
        - generic [ref=e284]:
          - generic [ref=e285]:
            - generic [ref=e286]: ⚙️
            - heading "系統管理" [level=2] [ref=e287]
          - generic [ref=e288]:
            - link "使用者管理 新增帳號、設定角色權限" [ref=e289] [cursor=pointer]:
              - /url: /admin/users
              - generic [ref=e290]:
                - img [ref=e292]
                - generic [ref=e297]:
                  - paragraph [ref=e298]: 使用者管理
                  - paragraph [ref=e299]: 新增帳號、設定角色權限
            - link "系統設定 整合設定、AI 引擎、通知" [ref=e300] [cursor=pointer]:
              - /url: /settings
              - generic [ref=e301]:
                - img [ref=e303]
                - generic [ref=e306]:
                  - paragraph [ref=e307]: 系統設定
                  - paragraph [ref=e308]: 整合設定、AI 引擎、通知
  - button [ref=e309] [cursor=pointer]:
    - img [ref=e310]
  - button "Open Next.js Dev Tools" [ref=e317] [cursor=pointer]:
    - img [ref=e318]
  - alert [ref=e321]
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
> 24 |     await expect(page.getByText("Project Nexus")).toBeVisible();
     |                                                   ^ Error: expect(locator).toBeVisible() failed
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
  70 |     await expect(dealsLink).toBeHidden();
  71 | 
  72 |     // Click again to expand
  73 |     await sectionBtn.click();
  74 |     await expect(dealsLink).toBeVisible();
  75 |   });
  76 | });
  77 | 
```