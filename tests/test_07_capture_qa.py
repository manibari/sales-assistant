"""test_07_capture_qa — Intel capture text input, file upload, + Q&A flow."""

from playwright.sync_api import Page, expect
from conftest import BASE_URL, screenshot


class TestCaptureInput:
    """Capture page text input."""

    def test_capture_page_loads(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        title = page.get_by_role("heading", name="新增情報")
        expect(title).to_be_visible()
        screenshot(page, "07_capture_page")

    def test_textarea_input(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        textarea = page.locator("textarea")
        expect(textarea).to_be_visible()
        textarea.fill("測試情報：今天拜訪 Z 公司，對方有興趣。")
        assert textarea.input_value() == "測試情報：今天拜訪 Z 公司，對方有興趣。"

    def test_submit_disabled_when_empty(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        submit_btn = page.locator('button:has-text("送出情報")')
        expect(submit_btn).to_be_disabled()

    def test_submit_enabled_with_text(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        textarea = page.locator("textarea")
        textarea.fill("Test input")
        submit_btn = page.locator('button:has-text("送出情報")')
        expect(submit_btn).to_be_enabled()


class TestCaptureFileUpload:
    """File attachment on capture page."""

    def test_attach_file_button_visible(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        attach_btn = page.locator('button:has-text("附加文件")')
        expect(attach_btn).to_be_visible()
        screenshot(page, "07_capture_attach_btn")

    def test_open_file_panel(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        page.locator('button:has-text("附加文件")').click()
        # Should show file panel with link input and file picker
        link_input = page.locator('input[type="url"]')
        expect(link_input).to_be_visible()
        file_input = page.locator('input[type="file"]')
        expect(file_input).to_be_attached()
        screenshot(page, "07_capture_file_panel")

    def test_close_file_panel(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        page.locator('button:has-text("附加文件")').click()
        # Panel should be visible
        expect(page.locator('text=新增附件')).to_be_visible()
        # Close it
        page.locator('text=新增附件').locator("..").locator("button").click()
        page.wait_for_timeout(300)
        # Attach button should re-appear
        expect(page.locator('button:has-text("附加文件")')).to_be_visible()

    def test_add_link_attachment(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        page.locator('button:has-text("附加文件")').click()
        # Enter a link
        link_input = page.locator('input[type="url"]')
        link_input.fill("https://drive.google.com/file/d/test123")
        # Click the link submit button (the blue Link2 icon button)
        page.locator('input[type="url"]').locator("..").locator("button").click()
        page.wait_for_timeout(300)
        # Should show attached file in list
        file_item = page.locator("text=Google Drive 文件")
        expect(file_item).to_be_visible()
        # Should show attachment count
        expect(page.locator("text=附件 (1)")).to_be_visible()
        screenshot(page, "07_capture_link_attached")

    def test_remove_attachment(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        # Add a link
        page.locator('button:has-text("附加文件")').click()
        page.locator('input[type="url"]').fill("https://example.com/doc.pdf")
        page.locator('input[type="url"]').locator("..").locator("button").click()
        page.wait_for_timeout(300)
        # Should show attachment
        expect(page.locator("text=附件 (1)")).to_be_visible()
        # Remove it via X button
        page.locator("text=doc.pdf").locator("..").locator("button").click()
        page.wait_for_timeout(300)
        # Attachment list should be gone
        expect(page.locator("text=附件")).not_to_be_visible()


class TestCaptureSubmitToQa:
    """Submit intel and redirect to Q&A."""

    def test_submit_redirects_to_qa(self, page: Page):
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        textarea = page.locator("textarea")
        textarea.fill("E2E Test: 測試情報輸入，對方對 IoT 有興趣。")
        submit_btn = page.locator('button:has-text("送出情報")')
        submit_btn.click()
        # Wait for navigation to Q&A page
        page.wait_for_url("**/capture/qa**", timeout=10000)
        assert "/capture/qa" in page.url
        assert "id=" in page.url
        screenshot(page, "07_qa_redirect")


class TestQaFlow:
    """Q&A flow questions and interactions."""

    def _enter_qa(self, page: Page):
        """Helper to submit intel and arrive at Q&A."""
        page.goto(f"{BASE_URL}/capture")
        page.wait_for_load_state("networkidle")
        page.locator("textarea").fill("QA flow test intel")
        page.locator('button:has-text("送出情報")').click()
        page.wait_for_url("**/capture/qa**", timeout=10000)
        page.wait_for_load_state("networkidle")

    def test_role_question_appears(self, page: Page):
        self._enter_qa(page)
        question = page.locator("text=他是什麼角色？")
        expect(question).to_be_visible()
        screenshot(page, "07_qa_role_question")

    def test_select_client_shows_client_questions(self, page: Page):
        self._enter_qa(page)
        # Select "client"
        client_btn = page.locator('button:has-text("客戶")')
        client_btn.click()
        # Wait for industry question to appear after state update
        page.wait_for_selector("text=什麼產業？", timeout=5000)
        question = page.locator("text=什麼產業？")
        expect(question).to_be_visible()
        screenshot(page, "07_qa_client_industry")

    def test_single_select_auto_advance(self, page: Page):
        self._enter_qa(page)
        # Select client -> auto advance
        page.locator('button:has-text("客戶")').click()
        page.wait_for_selector("text=什麼產業？", timeout=5000)
        # Select industry -> auto advance to pain_points
        page.locator('button:has-text("食品業")').click()
        page.wait_for_selector("text=已知痛點？", timeout=5000)
        # Should now show pain points (multiSelect)
        question = page.locator("text=已知痛點？")
        expect(question).to_be_visible()

    def test_multi_select_confirm_button(self, page: Page):
        self._enter_qa(page)
        page.locator('button:has-text("客戶")').click()
        page.wait_for_selector("text=什麼產業？", timeout=5000)
        page.locator('button:has-text("食品業")').click()
        page.wait_for_selector("text=已知痛點？", timeout=5000)
        # Now at pain_points (multiSelect)
        page.locator('button:has-text("產線自動化")').click()
        page.locator('button:has-text("品質檢測 (AOI)")').click()
        # Confirm button should appear
        confirm_btn = page.locator('button:has-text("確認")')
        expect(confirm_btn).to_be_visible()
        screenshot(page, "07_qa_multi_select")

    def test_skip_creates_tbd(self, page: Page):
        self._enter_qa(page)
        # Skip the role question
        skip_btn = page.locator('button:has-text("稍後再說")')
        expect(skip_btn).to_be_visible()
        skip_btn.click()
        page.wait_for_timeout(1000)
        # Should reach completion
        done_text = page.locator("text=情報已確認")
        expect(done_text).to_be_visible()
        screenshot(page, "07_qa_skip_done")

    def test_complete_flow(self, page: Page):
        self._enter_qa(page)
        # Client -> food -> select pain points -> NDA -> MOU -> budget -> done
        page.locator('button:has-text("客戶")').click()
        page.wait_for_selector("text=什麼產業？", timeout=5000)
        page.locator('button:has-text("食品業")').click()
        page.wait_for_selector("text=已知痛點？", timeout=5000)
        # Pain points multiselect
        page.locator('button:has-text("產線自動化")').click()
        page.locator('button:has-text("確認")').click()
        page.wait_for_selector("text=NDA", timeout=5000)
        # NDA
        page.locator('button:has-text("已簽署")').click()
        page.wait_for_selector("text=MOU", timeout=5000)
        # MOU
        page.locator('button:has-text("不需要")').click()
        page.wait_for_selector("text=預算", timeout=5000)
        # Budget
        page.locator('button:has-text("100K - 500K")').click()
        page.wait_for_selector("text=情報已確認", timeout=5000)
        # Should see completion
        done_text = page.locator("text=情報已確認")
        expect(done_text).to_be_visible()
        # Check action buttons
        add_more = page.locator('button:has-text("再加一筆")')
        view_intel = page.locator('button:has-text("查看情報")')
        expect(add_more).to_be_visible()
        expect(view_intel).to_be_visible()
        screenshot(page, "07_qa_complete")
