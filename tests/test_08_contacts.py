"""test_08_contacts — Client/partner tab switching, data display."""

from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestClientTab:
    """Clients tab data."""

    def test_contacts_page_loads(self, page: Page):
        page.goto(f"{BASE_URL}/contacts")
        page.wait_for_load_state("networkidle")
        title = page.get_by_role("heading", name="通訊錄")
        expect(title).to_be_visible()
        screenshot(page, "08_contacts_page")

    def test_clients_tab_active_by_default(self, page: Page):
        page.goto(f"{BASE_URL}/contacts")
        page.wait_for_load_state("networkidle")
        client_tab = page.locator('button:has-text("客戶")')
        classes = client_tab.get_attribute("class") or ""
        assert "border-blue-500" in classes, "Clients tab should be active by default"

    def test_four_clients_displayed(self, page: Page):
        page.goto(f"{BASE_URL}/contacts")
        page.wait_for_load_state("networkidle")
        # Check each client name from seed
        for name in ["A 食品", "B 石化", "C 半導體", "D 製造"]:
            client = page.locator(f"text={name}")
            expect(client).to_be_visible()

    def test_client_shows_industry_and_budget(self, page: Page):
        page.goto(f"{BASE_URL}/contacts")
        page.wait_for_load_state("networkidle")
        # A Food should show industry/budget info
        card = page.locator("text=/food.*100-500K/")
        expect(card.first).to_be_visible()


class TestPartnerTab:
    """Partners tab data."""

    def test_switch_to_partners_tab(self, page: Page):
        page.goto(f"{BASE_URL}/contacts")
        page.wait_for_load_state("networkidle")
        partner_tab = page.locator('button:has-text("夥伴")')
        partner_tab.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        screenshot(page, "08_contacts_partners")

    def test_four_partners_displayed(self, page: Page):
        page.goto(f"{BASE_URL}/contacts")
        page.wait_for_load_state("networkidle")
        page.locator('button:has-text("夥伴")').click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        for name in ["Vision 科技", "IoT 系統", "宏碁智雲", "Delta Edge"]:
            partner = page.locator(f"text={name}")
            expect(partner).to_be_visible()

    def test_trust_level_badge(self, page: Page):
        page.goto(f"{BASE_URL}/contacts")
        page.wait_for_load_state("networkidle")
        page.locator('button:has-text("夥伴")').click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        # Should show trust badges
        verified = page.locator("text=已驗證")
        assert verified.count() >= 1, "Should show at least one verified badge"
        # Core team badge
        core = page.locator("text=核心班底")
        expect(core).to_be_visible()
