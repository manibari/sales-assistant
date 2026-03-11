"""test_01_global — Theme toggle, sidebar navigation, RWD breakpoints."""

import re

import pytest
from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestThemeToggle:
    """Theme switching: dark -> light -> dark."""

    def test_default_theme_is_dark(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        html = page.locator("html")
        expect(html).to_have_class(re.compile("dark"))
        screenshot(page, "01_theme_dark_default")

    def test_toggle_to_light(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        page.click('button[aria-label="Toggle theme"]')
        page.wait_for_timeout(300)
        html = page.locator("html")
        expect(html).not_to_have_class(re.compile("dark"))
        # Background should change to light
        body = page.locator("body")
        bg = body.evaluate("el => getComputedStyle(el).backgroundColor")
        assert bg != "rgb(2, 6, 23)", f"Background should not be dark slate-950, got {bg}"
        screenshot(page, "01_theme_light")

    def test_toggle_back_to_dark(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        # Toggle to light
        page.click('button[aria-label="Toggle theme"]')
        page.wait_for_timeout(300)
        # Toggle back to dark
        page.click('button[aria-label="Toggle theme"]')
        page.wait_for_timeout(300)
        html = page.locator("html")
        expect(html).to_have_class(re.compile("dark"))
        screenshot(page, "01_theme_dark_restored")


class TestDesktopSidebar:
    """Desktop sidebar should have 7 nav links."""

    NAV_ITEMS = [
        ("/dashboard", "控制台"),
        ("/deals", "商機 Pipeline"),
        ("/calendar", "行事曆"),
        ("/capture", "新增情報"),
        ("/intel", "情報 Feed"),
        ("/contacts", "通訊錄"),
        ("/search", "搜尋"),
    ]

    def test_sidebar_has_7_links(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        sidebar = page.locator("aside")
        links = sidebar.locator("a")
        expect(links).to_have_count(7)

    @pytest.mark.parametrize("href,label", NAV_ITEMS)
    def test_sidebar_navigation(self, page: Page, href: str, label: str):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        link = page.locator(f'aside a[href="{href}"]')
        expect(link).to_be_visible()
        link.click()
        page.wait_for_url(f"**{href}**")
        assert page.url.endswith(href) or href in page.url

    def test_active_link_highlight(self, page: Page):
        page.goto(f"{BASE_URL}/deals")
        page.wait_for_load_state("networkidle")
        link = page.locator('aside a[href="/deals"]')
        classes = link.get_attribute("class") or ""
        assert "text-blue" in classes, f"Active link should have blue text, got: {classes}"


class TestMobileBottomNav:
    """Mobile bottom nav: 5 items including FAB."""

    def test_bottom_nav_visible_on_mobile(self, mobile_page: Page):
        mobile_page.goto(f"{BASE_URL}/dashboard")
        mobile_page.wait_for_load_state("networkidle")
        nav = mobile_page.locator("nav.fixed.bottom-0")
        expect(nav).to_be_visible()
        links = nav.locator("a")
        expect(links).to_have_count(5)
        screenshot(mobile_page, "01_mobile_bottom_nav")

    def test_fab_button(self, mobile_page: Page):
        mobile_page.goto(f"{BASE_URL}/dashboard")
        mobile_page.wait_for_load_state("networkidle")
        fab = mobile_page.locator('nav.fixed.bottom-0 a[href="/capture"]')
        expect(fab).to_be_visible()
        fab.click()
        mobile_page.wait_for_url("**/capture**")
        assert "/capture" in mobile_page.url

    def test_bottom_nav_hidden_on_desktop(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        nav = page.locator("nav.fixed.bottom-0")
        expect(nav).to_be_hidden()


class TestRWD:
    """RWD breakpoint screenshots."""

    def test_desktop_screenshot(self, page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        screenshot(page, "01_rwd_desktop_1280")

    def test_tablet_screenshot(self, tablet_page: Page):
        tablet_page.goto(f"{BASE_URL}/dashboard")
        tablet_page.wait_for_load_state("networkidle")
        screenshot(tablet_page, "01_rwd_tablet_768")

    def test_mobile_screenshot(self, mobile_page: Page):
        mobile_page.goto(f"{BASE_URL}/dashboard")
        mobile_page.wait_for_load_state("networkidle")
        screenshot(mobile_page, "01_rwd_mobile_390")
