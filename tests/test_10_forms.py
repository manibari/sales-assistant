"""test_10_forms — New deal and new meeting form validation."""

from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestNewDealForm:
    """New deal form at /deals/new."""

    def test_form_loads(self, page: Page):
        page.goto(f"{BASE_URL}/deals/new")
        page.wait_for_load_state("networkidle")
        title = page.get_by_role("heading", name="建立商機")
        expect(title).to_be_visible()
        screenshot(page, "10_new_deal_form")

    def test_submit_disabled_without_required_fields(self, page: Page):
        page.goto(f"{BASE_URL}/deals/new")
        page.wait_for_load_state("networkidle")
        submit_btn = page.locator('button:has-text("建立商機")')
        expect(submit_btn).to_be_disabled()

    def test_submit_disabled_with_only_name(self, page: Page):
        page.goto(f"{BASE_URL}/deals/new")
        page.wait_for_load_state("networkidle")
        name_input = page.locator('input[placeholder*="A 食品"]')
        name_input.fill("Test Deal")
        submit_btn = page.locator('button:has-text("建立商機")')
        # Still disabled because no client selected
        expect(submit_btn).to_be_disabled()

    def test_submit_enabled_with_required_fields(self, page: Page):
        page.goto(f"{BASE_URL}/deals/new")
        page.wait_for_load_state("networkidle")
        # Select client
        select = page.locator("select").first
        page.wait_for_timeout(1000)  # Wait for clients to load
        select.select_option(index=1)
        # Fill name
        name_input = page.locator('input[placeholder*="A 食品"]')
        name_input.fill("Test Deal E2E")
        submit_btn = page.locator('button:has-text("建立商機")')
        expect(submit_btn).to_be_enabled()

    def test_create_deal_redirects(self, page: Page):
        page.goto(f"{BASE_URL}/deals/new")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        # Select client
        page.locator("select").first.select_option(index=1)
        # Fill name
        page.locator('input[placeholder*="A 食品"]').fill("E2E Test Deal")
        # Submit
        page.locator('button:has-text("建立商機")').click()
        page.wait_for_url("**/deals/**", timeout=10000)
        assert "/deals/" in page.url
        screenshot(page, "10_new_deal_created")


class TestNewMeetingForm:
    """New meeting form at /calendar/meeting/new."""

    def test_form_loads(self, page: Page):
        page.goto(f"{BASE_URL}/calendar/meeting/new")
        page.wait_for_load_state("networkidle")
        title = page.locator("text=新增會議")
        expect(title).to_be_visible()
        screenshot(page, "10_new_meeting_form")

    def test_submit_disabled_without_required_fields(self, page: Page):
        page.goto(f"{BASE_URL}/calendar/meeting/new")
        page.wait_for_load_state("networkidle")
        submit_btn = page.locator('button:has-text("排定會議")')
        expect(submit_btn).to_be_disabled()

    def test_submit_enabled_with_required_fields(self, page: Page):
        page.goto(f"{BASE_URL}/calendar/meeting/new")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        # Select deal
        page.locator("select").first.select_option(index=1)
        # Fill title
        page.locator('input[placeholder*="A 食品"]').fill("E2E Test Meeting")
        # Fill date
        page.locator('input[type="date"]').fill("2026-04-01")
        submit_btn = page.locator('button:has-text("排定會議")')
        expect(submit_btn).to_be_enabled()

    def test_create_meeting_redirects(self, page: Page):
        page.goto(f"{BASE_URL}/calendar/meeting/new")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        # Fill form
        page.locator("select").first.select_option(index=1)
        page.locator('input[placeholder*="A 食品"]').fill("E2E Test Meeting")
        page.locator('input[type="date"]').fill("2026-04-01")
        # Submit
        page.locator('button:has-text("排定會議")').click()
        page.wait_for_url("**/calendar**", timeout=10000)
        assert "/calendar" in page.url
        screenshot(page, "10_new_meeting_created")
