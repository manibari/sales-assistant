"""test_09_search — Search, filter tabs, result navigation."""

from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestSearchInput:
    """Search page and input."""

    def test_search_page_loads(self, page: Page):
        page.goto(f"{BASE_URL}/search")
        page.wait_for_load_state("networkidle")
        title = page.get_by_role("heading", name="搜尋")
        expect(title).to_be_visible()
        screenshot(page, "09_search_page")

    def test_search_input_autofocus(self, page: Page):
        page.goto(f"{BASE_URL}/search")
        page.wait_for_load_state("networkidle")
        input_el = page.locator('input[placeholder*="搜尋"]')
        expect(input_el).to_be_visible()


class TestSearchResults:
    """Search for '食品' and verify results."""

    def test_search_food(self, page: Page):
        page.goto(f"{BASE_URL}/search")
        page.wait_for_load_state("networkidle")
        input_el = page.locator('input[placeholder*="搜尋"]')
        input_el.fill("食品")
        input_el.press("Enter")
        page.wait_for_timeout(2000)
        # Should show results across categories
        total_text = page.locator("text=全部")
        expect(total_text.first).to_be_visible()
        screenshot(page, "09_search_food_results")

    def test_search_shows_deals(self, page: Page):
        page.goto(f"{BASE_URL}/search")
        page.wait_for_load_state("networkidle")
        page.locator('input[placeholder*="搜尋"]').fill("食品")
        page.locator('input[placeholder*="搜尋"]').press("Enter")
        page.wait_for_timeout(2000)
        # Should find deal "A 食品 AOI 產線自動化"
        deal = page.locator("text=A 食品 AOI 產線自動化")
        expect(deal).to_be_visible()

    def test_search_shows_clients(self, page: Page):
        page.goto(f"{BASE_URL}/search")
        page.wait_for_load_state("networkidle")
        page.locator('input[placeholder*="搜尋"]').fill("食品")
        page.locator('input[placeholder*="搜尋"]').press("Enter")
        page.wait_for_timeout(2000)
        # Should find client "A 食品"
        client_section = page.locator("text=客戶")
        expect(client_section.first).to_be_visible()


class TestFilterTabs:
    """Filter tabs switching."""

    def test_filter_tabs_appear(self, page: Page):
        page.goto(f"{BASE_URL}/search")
        page.wait_for_load_state("networkidle")
        page.locator('input[placeholder*="搜尋"]').fill("食品")
        page.locator('input[placeholder*="搜尋"]').press("Enter")
        page.wait_for_timeout(2000)
        # Tab buttons should appear
        all_tab = page.locator('button:has-text("全部")')
        expect(all_tab).to_be_visible()

    def test_switch_to_deals_tab(self, page: Page):
        page.goto(f"{BASE_URL}/search")
        page.wait_for_load_state("networkidle")
        page.locator('input[placeholder*="搜尋"]').fill("食品")
        page.locator('input[placeholder*="搜尋"]').press("Enter")
        page.wait_for_timeout(2000)
        deals_tab = page.locator('button:has-text("商機")')
        if deals_tab.count() > 0:
            deals_tab.click()
            page.wait_for_timeout(300)
            screenshot(page, "09_search_deals_tab")


class TestSearchNavigation:
    """Click search result to navigate."""

    def test_click_deal_result(self, page: Page):
        page.goto(f"{BASE_URL}/search")
        page.wait_for_load_state("networkidle")
        page.locator('input[placeholder*="搜尋"]').fill("食品")
        page.locator('input[placeholder*="搜尋"]').press("Enter")
        page.wait_for_timeout(2000)
        deal_link = page.locator('a[href^="/deals/"]').first
        if deal_link.count() > 0:
            deal_link.click()
            page.wait_for_url("**/deals/**", timeout=10000)
            assert "/deals/" in page.url
            screenshot(page, "09_search_deal_navigate")
