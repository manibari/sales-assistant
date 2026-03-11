"""test_02_dashboard — Dashboard data, sections, navigation links."""

from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestDashboardSummary:
    """Summary card and total actions count."""

    def test_pipeline_overview_visible(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=Pipeline Overview", timeout=10000)
        overview = page.get_by_text("Pipeline Overview")
        expect(overview).to_be_visible()

    def test_pipeline_metrics(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=總 Pipeline", timeout=10000)
        total = page.get_by_text("總 Pipeline")
        expect(total).to_be_visible()
        weighted = page.get_by_text("加權預估")
        expect(weighted).to_be_visible()
        deal_count = page.get_by_text("進行中商機")
        expect(deal_count).to_be_visible()
        screenshot(page, "02_dashboard_pipeline")


class TestTodayMeetings:
    """Today's meetings section."""

    def test_today_meeting_visible(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        section = page.locator("text=今日會議")
        expect(section).to_be_visible()

    def test_meeting_title(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        meeting = page.locator("text=A 食品 — 技術方案討論")
        expect(meeting).to_be_visible()


class TestPushDeals:
    """Deals needing push section."""

    def test_push_section_visible(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        section = page.locator("text=需要推進")
        expect(section).to_be_visible()

    def test_push_deal_names(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        # B petro (20 days) and A food (10 days) should be listed
        b_petro = page.locator("text=B 石化能源監控平台").first
        expect(b_petro).to_be_visible()


class TestDashboardSections:
    """Reminders and TBD sections."""

    def test_reminders_section(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        section = page.locator("text=待處理提醒")
        expect(section).to_be_visible()

    def test_tbd_section(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        section = page.locator("text=待確認事項")
        expect(section).to_be_visible()


class TestDashboardNavigation:
    """Navigation links in dashboard."""

    def test_search_icon_link(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        search_link = page.locator('header a[href="/search"]')
        expect(search_link).to_be_visible()

    def test_new_intel_button(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        btn = page.locator('main a:has-text("新增情報")')
        expect(btn).to_be_visible()
        btn.click()
        page.wait_for_url("**/capture**")
        assert "/capture" in page.url

    def test_deals_list_button(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        btn = page.locator('main a:has-text("商機列表")')
        expect(btn).to_be_visible()
        btn.click()
        page.wait_for_url("**/deals**")
        assert "/deals" in page.url
        screenshot(page, "02_dashboard_nav_to_deals")
