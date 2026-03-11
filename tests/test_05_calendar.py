"""test_05_calendar — Month navigation, today highlight, date click, meeting card."""

from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestMonthNavigation:
    """Month header and prev/next buttons."""

    def test_calendar_page_loads(self, page: Page):
        page.goto(f"{BASE_URL}/calendar")
        page.wait_for_load_state("networkidle")
        title = page.get_by_role("heading", name="行事曆")
        expect(title).to_be_visible()
        screenshot(page, "05_calendar_page")

    def test_prev_month(self, page: Page):
        page.goto(f"{BASE_URL}/calendar")
        page.wait_for_load_state("networkidle")
        # Get current month text
        month_header = page.locator("h2").first
        original_text = month_header.inner_text()
        # Click prev — find buttons within the month header's parent container
        header_row = month_header.locator("..")
        prev_btn = header_row.locator("button").first
        prev_btn.click()
        page.wait_for_timeout(500)
        new_text = month_header.inner_text()
        assert new_text != original_text, "Month should change after clicking prev"

    def test_next_month(self, page: Page):
        page.goto(f"{BASE_URL}/calendar")
        page.wait_for_load_state("networkidle")
        month_header = page.locator("h2").first
        original_text = month_header.inner_text()
        # Click next — last button in the month header's parent container
        header_row = month_header.locator("..")
        next_btn = header_row.locator("button").last
        next_btn.click()
        page.wait_for_timeout(500)
        new_text = month_header.inner_text()
        assert new_text != original_text, "Month should change after clicking next"


class TestTodayHighlight:
    """Today's date should have special styling."""

    def test_today_has_highlight(self, page: Page):
        page.goto(f"{BASE_URL}/calendar")
        page.wait_for_load_state("networkidle")
        # Today's button should have blue-500/10 background class
        from datetime import datetime
        today = datetime.now().day
        # Find the button with today's number
        day_buttons = page.locator(".grid.grid-cols-7 button")
        found_today = False
        for i in range(day_buttons.count()):
            btn = day_buttons.nth(i)
            text = btn.inner_text().strip()
            if text == str(today):
                classes = btn.get_attribute("class") or ""
                if "bg-blue" in classes:
                    found_today = True
                    break
        assert found_today, f"Today ({today}) should have blue highlight"


class TestDateClick:
    """Click a date to show day detail."""

    def test_click_date_shows_detail(self, page: Page):
        page.goto(f"{BASE_URL}/calendar")
        page.wait_for_load_state("networkidle")
        # Click first available day button
        day_buttons = page.locator(".grid.grid-cols-7 button")
        if day_buttons.count() > 0:
            day_buttons.first.click()
            page.wait_for_timeout(500)
            # Should show a date string header or "no events" message
            detail = page.locator("text=/\\d{4}-\\d{2}-\\d{2}/")
            expect(detail.first).to_be_visible()
            screenshot(page, "05_calendar_day_detail")


class TestMeetingCardNavigation:
    """Click meeting card to navigate to meeting detail."""

    def test_event_dots_or_meetings_exist(self, page: Page):
        page.goto(f"{BASE_URL}/calendar")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        # Event dots depend on meetingsByMonth API returning data
        # Check for dots OR verify the API works by clicking today
        from datetime import datetime
        today = datetime.now()
        day_buttons = page.locator(".grid.grid-cols-7 button")
        for i in range(day_buttons.count()):
            btn = day_buttons.nth(i)
            if btn.inner_text().strip() == str(today.day):
                btn.click()
                break
        page.wait_for_timeout(1000)
        # After clicking today, should see meeting or "no events"
        has_meeting = page.locator('a[href^="/calendar/meeting/"]').count() > 0
        has_no_events = page.get_by_text("無事項").count() > 0
        assert has_meeting or has_no_events, "Should show either a meeting or 'no events' message"
        screenshot(page, "05_calendar_today_events")

    def test_click_today_shows_meeting(self, page: Page):
        page.goto(f"{BASE_URL}/calendar")
        page.wait_for_load_state("networkidle")
        from datetime import datetime
        today = datetime.now()
        date_str = f"{today.year}-{str(today.month).zfill(2)}-{str(today.day).zfill(2)}"
        # Click today's date
        day_buttons = page.locator(".grid.grid-cols-7 button")
        for i in range(day_buttons.count()):
            btn = day_buttons.nth(i)
            if btn.inner_text().strip() == str(today.day):
                btn.click()
                break
        page.wait_for_timeout(500)
        # Should show meeting card
        meeting_link = page.locator('a[href^="/calendar/meeting/"]')
        if meeting_link.count() > 0:
            meeting_link.first.click()
            page.wait_for_url("**/calendar/meeting/**")
            assert "/calendar/meeting/" in page.url
            screenshot(page, "05_calendar_meeting_detail")
