"""test_04_deal_detail — Deal detail page, MEDDIC, advance, close, side sections."""

import re
from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


def get_first_deal_url(page: Page) -> str:
    """Navigate to deals list and get first deal's URL."""
    page.goto(f"{BASE_URL}/deals")
    page.wait_for_load_state("networkidle")
    first_card = page.locator('a[href^="/deals/"]').filter(
        has=page.locator("h3")
    ).first
    href = first_card.get_attribute("href") or "/deals/1"
    return f"{BASE_URL}{href}"


class TestDealHeader:
    """Deal detail header info."""

    def test_header_shows_deal_info(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        # Should show deal name
        deal_name = page.locator("h2")
        expect(deal_name).to_be_visible()
        # Should show stage badge
        stage_badge = page.locator("text=/L[0-4]/")
        expect(stage_badge.first).to_be_visible()
        screenshot(page, "04_deal_detail_header")

    def test_header_shows_client(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        # Client name should appear
        client_text = page.locator("text=/食品|石化|半導體|製造/")
        expect(client_text.first).to_be_visible()


class TestMeddic:
    """MEDDIC progress bar and editing."""

    def test_meddic_progress_visible(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        meddic = page.locator("text=MEDDIC 進度")
        expect(meddic).to_be_visible()

    def test_meddic_expand(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        # Click to expand MEDDIC
        meddic_btn = page.locator('button:has-text("MEDDIC 進度")')
        meddic_btn.click()
        page.wait_for_timeout(300)
        # Should show MEDDIC fields
        metrics = page.locator("text=Metrics")
        expect(metrics).to_be_visible()
        screenshot(page, "04_meddic_expanded")

    def test_meddic_edit_field(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        # Expand MEDDIC
        page.locator('button:has-text("MEDDIC 進度")').click()
        page.wait_for_timeout(300)
        # Find an empty field's "fill" button
        fill_btns = page.locator('button:has-text("填寫")')
        if fill_btns.count() > 0:
            fill_btns.first.click()
            page.wait_for_timeout(200)
            # Input should appear
            input_field = page.locator('input[placeholder="輸入內容..."]')
            expect(input_field).to_be_visible()
            input_field.fill("Test MEDDIC value")
            screenshot(page, "04_meddic_editing")


class TestDealActions:
    """Advance stage and close deal."""

    def test_advance_button_visible(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        advance_btn = page.locator('button:has-text("推進階段")')
        expect(advance_btn).to_be_visible()

    def test_close_button_opens_modal(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        close_btn = page.locator('button:has-text("關閉")').first
        close_btn.click()
        page.wait_for_timeout(300)
        # Modal should appear
        modal_title = page.locator("text=關閉商機")
        expect(modal_title).to_be_visible()
        screenshot(page, "04_close_modal")

    def test_close_modal_reasons(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.locator('button:has-text("關閉")').first.click()
        page.wait_for_timeout(300)
        # Check reason buttons exist
        for reason in ["預算不足", "時程不合", "選擇競品", "需求消失", "其他"]:
            btn = page.locator(f'button:has-text("{reason}")')
            expect(btn).to_be_visible()

    def test_close_modal_cancel(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.locator('button:has-text("關閉")').first.click()
        page.wait_for_timeout(300)
        cancel_btn = page.locator('button:has-text("取消")')
        cancel_btn.click()
        page.wait_for_timeout(300)
        # Modal should disappear
        modal = page.locator("text=關閉商機")
        expect(modal).to_be_hidden()


class TestDealSideSections:
    """Partners, intel, TBD, files sections."""

    def test_partners_section(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        section = page.locator("text=搭配夥伴")
        expect(section).to_be_visible()

    def test_intel_section(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        section = page.locator("text=相關情報")
        expect(section).to_be_visible()

    def test_tbd_section(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        section = page.locator("text=TBD 清單")
        expect(section).to_be_visible()

    def test_files_section(self, page: Page):
        url = get_first_deal_url(page)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        section = page.locator("text=文件")
        expect(section.first).to_be_visible()
        screenshot(page, "04_deal_side_sections")
