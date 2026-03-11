"""test_03_deals — Pipeline list, view toggle, card colors, collapse."""

from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestDealsList:
    """Deal cards rendering."""

    def test_deals_page_loads(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        title = page.get_by_role("heading", name="商機 Pipeline")
        expect(title).to_be_visible()
        screenshot(page, "03_deals_list")

    def test_active_deal_cards(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        # 4 active deals (d1-d4); d5 is closed and may not show
        cards = page.locator('a[href^="/deals/"]').filter(
            has=page.locator("h3")
        )
        count = cards.count()
        assert count >= 4, f"Expected at least 4 deal cards, got {count}"


class TestViewToggle:
    """Urgency/stage view toggle."""

    def test_toggle_to_stage_view(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        toggle_btn = page.locator('button:has-text("階段")')
        expect(toggle_btn).to_be_visible()
        toggle_btn.click()
        page.wait_for_timeout(500)
        # Should now show stage headers
        stage_header = page.locator("text=L0 潛在").first
        expect(stage_header).to_be_visible()
        screenshot(page, "03_deals_stage_view")

    def test_toggle_cycles_views(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        # Default view=urgency, button shows next: "階段"
        # Click to stage view, button should show next: "時間軸"
        page.locator('button:has-text("階段")').click()
        page.wait_for_selector('button:has-text("時間軸")', timeout=5000)
        # Click to timeline view, button should show next: "緊急度"
        page.locator('button:has-text("時間軸")').click()
        page.wait_for_selector('button:has-text("緊急度")', timeout=5000)
        screenshot(page, "03_deals_view_cycle")


class TestCardColors:
    """Card left border color based on idle days."""

    def test_red_card_over_14_days(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        # B petro has 20 days idle -> red border
        b_card = page.locator('a:has-text("B 石化能源監控平台")')
        classes = b_card.get_attribute("class") or ""
        assert "border-l-red-500" in classes, f"Expected red border for 20-day idle deal, got: {classes}"

    def test_amber_card_over_7_days(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        # A food has 10 days idle -> amber border
        a_card = page.locator('a:has-text("A 食品 AOI 產線自動化")')
        classes = a_card.get_attribute("class") or ""
        assert "border-l-amber-500" in classes, f"Expected amber border for 10-day idle deal, got: {classes}"


class TestStageCollapse:
    """Stage grouping and collapse toggle."""

    def test_collapse_stage_group(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        # Switch to stage view
        page.locator('button:has-text("階段")').click()
        page.wait_for_timeout(500)
        # Find a stage header button and click to collapse
        stage_btn = page.locator('button:has-text("L1 接觸中")')
        if stage_btn.count() > 0:
            stage_btn.click()
            page.wait_for_timeout(300)
            screenshot(page, "03_deals_collapsed")


class TestDealCardNavigation:
    """Click card to navigate to deal detail."""

    def test_click_deal_card(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        first_card = page.locator('a[href^="/deals/"]').filter(
            has=page.locator("h3")
        ).first
        href = first_card.get_attribute("href")
        first_card.click()
        page.wait_for_url("**/deals/**")
        assert href and href in page.url
        screenshot(page, "03_deal_card_click")
