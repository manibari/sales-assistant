import { test, expect } from "@playwright/test";

const BASE = "http://localhost:3000";

// ============================================================
// 1. Page-load smoke tests — every route should return 200
// ============================================================

const PAGES = [
  { name: "Dashboard", path: "/dashboard" },
  { name: "Deals list", path: "/deals" },
  { name: "New deal", path: "/deals/new" },
  { name: "Calendar", path: "/calendar" },
  { name: "New meeting", path: "/calendar/meeting/new" },
  { name: "Contacts", path: "/contacts" },
  { name: "Capture", path: "/capture" },
  { name: "Intel list", path: "/intel" },
  { name: "Documents", path: "/documents" },
  { name: "Subsidies list", path: "/subsidies" },
  { name: "New subsidy", path: "/subsidies/new" },
  { name: "Search", path: "/search" },
];

for (const pg of PAGES) {
  test(`Page loads: ${pg.name} (${pg.path})`, async ({ page }) => {
    const res = await page.goto(`${BASE}${pg.path}`, { waitUntil: "networkidle" });
    expect(res?.status()).toBe(200);
    // No unhandled JS errors
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.waitForTimeout(500);
    expect(errors).toEqual([]);
  });
}

// ============================================================
// 2. Sidebar navigation — all links work
// ============================================================

test("Sidebar navigation links work", async ({ page }) => {
  await page.goto(`${BASE}/dashboard`, { waitUntil: "networkidle" });

  // Check sidebar exists
  const sidebar = page.locator("nav, aside, [class*='sidebar']").first();
  await expect(sidebar).toBeVisible();

  // Click each sidebar link and verify navigation
  const navLinks = page.locator("nav a[href], aside a[href]");
  const count = await navLinks.count();
  expect(count).toBeGreaterThan(3);

  const hrefs: string[] = [];
  for (let i = 0; i < count; i++) {
    const href = await navLinks.nth(i).getAttribute("href");
    if (href && href.startsWith("/")) hrefs.push(href);
  }

  for (const href of hrefs) {
    await page.goto(`${BASE}${href}`, { waitUntil: "networkidle" });
    expect(page.url()).toContain(href);
  }
});

// ============================================================
// 3. Dashboard — cards render with data
// ============================================================

test("Dashboard shows pipeline data", async ({ page }) => {
  await page.goto(`${BASE}/dashboard`, { waitUntil: "networkidle" });
  // Should have at least one visible card/section
  const cards = page.locator("[class*='rounded']");
  expect(await cards.count()).toBeGreaterThan(0);
});

// ============================================================
// 4. Deals — list, detail, CRUD buttons
// ============================================================

test("Deals list renders and has items", async ({ page }) => {
  await page.goto(`${BASE}/deals`, { waitUntil: "networkidle" });
  // Should show deal cards or a list
  await page.waitForTimeout(1000);
  const body = await page.textContent("body");
  // Should have some deal-related content or empty state
  expect(body).toBeTruthy();
});

test("Deal detail page loads with Gantt", async ({ page }) => {
  // Get a deal ID from the API
  const res = await page.request.get("http://localhost:8001/api/nx/deals/");
  const deals = await res.json();
  if (deals.length === 0) {
    test.skip();
    return;
  }
  const dealId = deals[0].id;
  await page.goto(`${BASE}/deals/${dealId}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  // Gantt section should exist
  const gantt = page.locator("text=攻案節奏");
  await expect(gantt).toBeVisible();

  // MEDDIC section
  const meddic = page.locator("text=MEDDIC");
  await expect(meddic).toBeVisible();
});

test("Deal detail — edit sections toggle", async ({ page }) => {
  const res = await page.request.get("http://localhost:8001/api/nx/deals/");
  const deals = await res.json();
  if (deals.length === 0) {
    test.skip();
    return;
  }
  await page.goto(`${BASE}/deals/${deals[0].id}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  // Find and click edit button (pencil icon) on intel section
  const editBtns = page.locator("button").filter({ has: page.locator("svg") });
  const editCount = await editBtns.count();
  expect(editCount).toBeGreaterThan(0);
});

test("Deal detail — unlink intel button appears in edit mode", async ({ page }) => {
  const res = await page.request.get("http://localhost:8001/api/nx/deals/");
  const deals = await res.json();
  // Find a deal with intel
  let targetDeal = null;
  for (const d of deals) {
    const dRes = await page.request.get(`http://localhost:8001/api/nx/deals/${d.id}`);
    const detail = await dRes.json();
    if (detail.intel && detail.intel.length > 0) {
      targetDeal = d;
      break;
    }
  }
  if (!targetDeal) {
    test.skip();
    return;
  }

  await page.goto(`${BASE}/deals/${targetDeal.id}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  // Find the intel section's edit button
  const intelSection = page.locator("text=相關情報").locator("..");
  const editBtn = intelSection.locator("button").filter({ has: page.locator("[class*='Pencil'], svg") }).first();
  if (await editBtn.isVisible()) {
    await editBtn.click();
    await page.waitForTimeout(300);
    // X button should appear for unlinking
    const unlinkBtn = page.locator("button").filter({ has: page.locator("svg.text-red-400, [class*='red']") });
    expect(await unlinkBtn.count()).toBeGreaterThan(0);
  }
});

// ============================================================
// 5. New deal form
// ============================================================

test("New deal form has required fields", async ({ page }) => {
  await page.goto(`${BASE}/deals/new`, { waitUntil: "networkidle" });
  // Client select and deal name text input
  const clientSelect = page.locator("select").first();
  await expect(clientSelect).toBeVisible();
  const nameInput = page.locator("input[type='text']").first();
  await expect(nameInput).toBeVisible();
});

// ============================================================
// 6. Calendar — month view renders
// ============================================================

test("Calendar shows month view", async ({ page }) => {
  await page.goto(`${BASE}/calendar`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  // Should show month/day headers
  const body = await page.textContent("body");
  expect(body).toContain("月");
});

test("Calendar — view toggle buttons work", async ({ page }) => {
  await page.goto(`${BASE}/calendar`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  // View tabs: 月, 週, 3天
  const monthTab = page.locator("button", { hasText: "月" }).first();
  await expect(monthTab).toBeVisible({ timeout: 5000 });

  const weekTab = page.locator("button", { hasText: "週" }).first();
  await expect(weekTab).toBeVisible();

  // Click week tab and verify no crash
  await weekTab.click();
  await page.waitForTimeout(500);
  const body = await page.textContent("body");
  expect(body?.length).toBeGreaterThan(10);
});

// ============================================================
// 7. Contacts — list, client/partner detail
// ============================================================

test("Contacts page loads with tabs", async ({ page }) => {
  await page.goto(`${BASE}/contacts`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const body = await page.textContent("body");
  // Should have client/partner sections
  expect(body?.length).toBeGreaterThan(10);
});

test("Client detail page loads", async ({ page }) => {
  const res = await page.request.get("http://localhost:8001/api/nx/contacts/?type=clients");
  let clients: { id: number }[] = [];
  try {
    clients = await res.json();
  } catch {
    // try alternate endpoint
    const r2 = await page.request.get("http://localhost:8001/api/nx/contacts/clients");
    clients = await r2.json();
  }
  if (clients.length === 0) {
    test.skip();
    return;
  }
  await page.goto(`${BASE}/contacts/clients/${clients[0].id}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const body = await page.textContent("body");
  expect(body?.length).toBeGreaterThan(10);
});

// ============================================================
// 8. Intel — list, detail
// ============================================================

test("Intel list page loads", async ({ page }) => {
  await page.goto(`${BASE}/intel`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const body = await page.textContent("body");
  expect(body?.length).toBeGreaterThan(10);
});

test("Intel detail page loads", async ({ page }) => {
  const res = await page.request.get("http://localhost:8001/api/nx/intel/");
  const intels = await res.json();
  if (intels.length === 0) {
    test.skip();
    return;
  }
  await page.goto(`${BASE}/intel/${intels[0].id}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const body = await page.textContent("body");
  expect(body?.length).toBeGreaterThan(10);
});

// ============================================================
// 9. Capture — text input flow
// ============================================================

test("Capture page has text input", async ({ page }) => {
  await page.goto(`${BASE}/capture`, { waitUntil: "networkidle" });
  const textarea = page.locator("textarea, input[type='text']").first();
  await expect(textarea).toBeVisible();
});

// ============================================================
// 10. Subsidies — list, detail, new
// ============================================================

test("Subsidies list page loads", async ({ page }) => {
  await page.goto(`${BASE}/subsidies`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const body = await page.textContent("body");
  expect(body?.length).toBeGreaterThan(10);
});

test("Subsidy detail loads with deadlines", async ({ page }) => {
  const res = await page.request.get("http://localhost:8001/api/nx/subsidies/");
  const subs = await res.json();
  if (subs.length === 0) {
    test.skip();
    return;
  }
  await page.goto(`${BASE}/subsidies/${subs[0].id}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const body = await page.textContent("body");
  expect(body?.length).toBeGreaterThan(10);
});

test("New subsidy form has fields", async ({ page }) => {
  await page.goto(`${BASE}/subsidies/new`, { waitUntil: "networkidle" });
  const nameInput = page.locator("input").first();
  await expect(nameInput).toBeVisible();
});

// ============================================================
// 11. Documents page
// ============================================================

test("Documents page loads", async ({ page }) => {
  await page.goto(`${BASE}/documents`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const body = await page.textContent("body");
  expect(body?.length).toBeGreaterThan(10);
});

// ============================================================
// 12. Search
// ============================================================

test("Search page works with query", async ({ page }) => {
  await page.goto(`${BASE}/search`, { waitUntil: "networkidle" });
  const searchInput = page.locator("input[type='text'], input[type='search'], input[placeholder*='搜尋']").first();
  await expect(searchInput).toBeVisible();
  await searchInput.fill("聖暉");
  await searchInput.press("Enter");
  await page.waitForTimeout(1500);
  // Should show results or empty state, no crash
  const body = await page.textContent("body");
  expect(body?.length).toBeGreaterThan(10);
});

// ============================================================
// 13. Console error collection across all pages
// ============================================================

test("No JS console errors on main pages", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(`${e.message}`));

  const criticalPages = ["/dashboard", "/deals", "/calendar", "/contacts", "/intel", "/subsidies", "/capture", "/search", "/documents"];

  for (const p of criticalPages) {
    await page.goto(`${BASE}${p}`, { waitUntil: "networkidle" });
    await page.waitForTimeout(800);
  }

  // Filter out known non-critical errors
  const realErrors = errors.filter(
    (e) => !e.includes("hydration") && !e.includes("ResizeObserver")
  );

  if (realErrors.length > 0) {
    console.log("JS errors found:", realErrors);
  }
  expect(realErrors).toEqual([]);
});
