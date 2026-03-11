"""test_06_intel — Intel feed list, status badges."""

from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestIntelList:
    """Intel feed should show all items."""

    def test_intel_page_loads(self, page: Page):
        page.goto(f"{BASE_URL}/intel")
        page.wait_for_load_state("networkidle")
        title = page.get_by_role("heading", name="情報 Feed")
        expect(title).to_be_visible()
        screenshot(page, "06_intel_page")

    def test_intel_count(self, page: Page):
        page.goto(f"{BASE_URL}/intel")
        page.wait_for_load_state("networkidle")
        # Should have 5 intel items from seed
        cards = page.locator(".rounded-xl").filter(
            has=page.locator("text=/已確認|草稿/")
        )
        count = cards.count()
        assert count >= 5, f"Expected at least 5 intel items, got {count}"


class TestIntelStatusBadge:
    """Status badges: confirmed (green), draft (amber)."""

    def test_confirmed_badge(self, page: Page):
        page.goto(f"{BASE_URL}/intel")
        page.wait_for_load_state("networkidle")
        confirmed = page.locator("text=已確認")
        assert confirmed.count() >= 4, f"Expected at least 4 confirmed badges, got {confirmed.count()}"

    def test_draft_badge(self, page: Page):
        page.goto(f"{BASE_URL}/intel")
        page.wait_for_load_state("networkidle")
        draft = page.locator("text=草稿")
        assert draft.count() >= 1, f"Expected at least 1 draft badge, got {draft.count()}"

    def test_confirmed_badge_is_green(self, page: Page):
        page.goto(f"{BASE_URL}/intel")
        page.wait_for_load_state("networkidle")
        badge = page.locator("text=已確認").first
        classes = badge.get_attribute("class") or ""
        assert "text-green" in classes, f"Confirmed badge should be green, got: {classes}"

    def test_draft_badge_is_amber(self, page: Page):
        page.goto(f"{BASE_URL}/intel")
        page.wait_for_load_state("networkidle")
        badge = page.locator("text=草稿").first
        classes = badge.get_attribute("class") or ""
        assert "text-amber" in classes, f"Draft badge should be amber, got: {classes}"
