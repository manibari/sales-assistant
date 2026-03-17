"""Fetch tender detail via g0v API JSON + Playwright screenshot for user-provided URLs."""

import json
import re
from pathlib import Path
from datetime import datetime

import requests

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent.parent / "materials" / "tenders" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

G0V_API_URL = "https://pcc-api.openfun.app/api/tender?unit_id={unit_id}&job_number={job_number}"

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _roc_to_iso(text: str) -> str | None:
    """Convert ROC date like '115/03/24 17:00' to '2026-03-24'."""
    m = re.search(r"(\d{2,3})/(\d{1,2})/(\d{1,2})", text)
    if m:
        year = int(m.group(1)) + 1911
        return f"{year}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def fetch_tender_detail_api(unit_id: str, job_number: str) -> dict | None:
    """Fetch structured tender data from g0v API and extract key fields."""
    url = G0V_API_URL.format(unit_id=unit_id, job_number=job_number)
    try:
        resp = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    if not data or "records" not in data:
        return None

    records = data["records"]
    if not records:
        return None

    # Use the latest record — detail keys are flat with colon separators
    latest = records[-1]
    d = latest.get("detail", {})

    def g(key: str) -> str:
        return str(d.get(key, "") or "")

    deadline_raw = g("領投開標:截止投標")
    deadline_iso = _roc_to_iso(deadline_raw) if deadline_raw else None
    opening_raw = g("領投開標:開標時間")

    budget_raw = g("採購資料:預算金額")
    budget_public = g("採購資料:預算金額是否公開")

    return {
        "name": g("採購資料:標案名稱") or latest.get("brief", {}).get("title", ""),
        "agency": g("機關資料:機關名稱") or data.get("unit_name", ""),
        "job_number": g("採購資料:標案案號") or data.get("job_number", job_number),
        "tender_type": g("招標資料:招標方式"),
        "category": g("採購資料:標的分類") or latest.get("brief", {}).get("category", ""),
        "budget": budget_raw if budget_public == "是" else f"(未公開) {budget_raw}".strip(),
        "deadline": deadline_iso,
        "deadline_raw": deadline_raw,
        "opening_date": _roc_to_iso(opening_raw),
        "opening_raw": opening_raw,
        "opening_location": g("領投開標:開標地點"),
        "contact_name": g("機關資料:聯絡人"),
        "contact_phone": g("機關資料:聯絡電話"),
        "contact_email": g("機關資料:電子郵件信箱"),
        "scope_summary": g("採購資料:標的分類"),
        "qualification": g("其他:廠商資格摘要"),
        "evaluation_method": g("招標資料:決標方式"),
        "contract_period": g("其他:履約期限"),
        "location": g("其他:履約地點"),
        "address": g("機關資料:機關地址"),
        "bid_submission": g("領投開標:收受投標文件地點"),
        "electronic_bid": g("領投開標:是否提供電子投標"),
        "deposit_required": g("領投開標:是否須繳納押標金"),
        "notes": g("其他:附加說明"),
        "reference_url": d.get("url", "") or latest.get("url", ""),
        "raw_json": d,
    }


def capture_tender_screenshots(url: str) -> list[str]:
    """Capture screenshots of any tender page URL (pcc.gov.tw, etc.).

    Use this for user-provided URLs that need visual parsing.
    For API-based scraping, use fetch_tender_detail_api() instead.

    Returns list of screenshot file paths.
    """
    from playwright.sync_api import sync_playwright

    slug = re.sub(r"[^\w]", "_", url.split("/")[-1][:30])
    timestamp = datetime.now().strftime("%Y%m%d")
    paths: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=BROWSER_UA,
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
        )
        page = ctx.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            full_path = str(SCREENSHOTS_DIR / f"{slug}_{timestamp}_full.png")
            page.screenshot(path=full_path, full_page=True)
            paths.append(full_path)

            page_height = page.evaluate("document.body.scrollHeight")
            if page_height > 2000:
                viewport_h = 900
                sections = min((page_height // viewport_h) + 1, 5)
                for i in range(sections):
                    y = i * viewport_h
                    page.evaluate(f"window.scrollTo(0, {y})")
                    page.wait_for_timeout(500)
                    section_path = str(SCREENSHOTS_DIR / f"{slug}_{timestamp}_s{i+1}.png")
                    page.screenshot(path=section_path)
                    paths.append(section_path)

        except Exception:
            pass

        browser.close()

    return paths


def build_vision_prompt() -> str:
    """Return the prompt for AI vision parsing of tender screenshots."""
    return """分析這張政府採購標案的截圖，提取以下資訊（用繁體中文回覆）：

1. **標案名稱**（完整名稱）
2. **招標機關**
3. **標案案號**
4. **招標方式**（公開招標/公開徵求/限制性招標等）
5. **採購類別**（勞務/財物/工程 + 細項）
6. **預算金額**（如有公開）
7. **截止投標日期**（轉為西元 YYYY-MM-DD 格式）
8. **開標日期**
9. **聯絡人**（姓名、電話、Email）
10. **需求規格摘要**（簡述標案要做什麼，150字以內）
11. **資格條件**（投標廠商需具備什麼資格）
12. **評選方式**（最低標/最有利標/評分及格最低標等）
13. **履約期限**（合約期間）
14. **其他重要條件**（分包限制、保證金、電子投標等）

如果某個欄位在截圖中找不到，回覆「未顯示」。

請用以下 YAML 格式回覆：
```yaml
name: "..."
agency: "..."
job_number: "..."
tender_type: "..."
category: "..."
budget: "..."
deadline: "YYYY-MM-DD"
opening_date: "YYYY-MM-DD"
contact_name: "..."
contact_phone: "..."
contact_email: "..."
scope_summary: "..."
qualification: "..."
evaluation_method: "..."
contract_period: "..."
other_conditions: "..."
```"""
