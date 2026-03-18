"""Fetch tender detail via g0v API JSON + Playwright for pcc.gov.tw page content."""

import logging
import re
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from pathlib import Path
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent.parent / "materials" / "tenders" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "materials" / "tenders" / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

G0V_API_URL = "https://pcc-api.openfun.app/api/tender?unit_id={unit_id}&job_number={job_number}"
PCC_DETAIL_URL = "https://web.pcc.gov.tw/tps/QueryTender/query/searchTenderDetail?pkPmsMain={pk}"

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


def fetch_pcc_page_content(pcc_url: str) -> dict:
    """Scrape the full tender detail page from pcc.gov.tw using Playwright.

    Returns dict with:
      - page_text: full page text content
      - notice_doc: parsed text from 投標須知 document (if downloadable)
      - download_links: list of {text, href} for downloadable documents
    """
    from playwright.sync_api import sync_playwright

    result = {"page_text": "", "notice_doc": "", "download_links": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=BROWSER_UA,
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
        )

        try:
            page.goto(pcc_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # 1. Get full page text
            result["page_text"] = page.inner_text("body")

            # 2. Find download links (投標須知, 招標文件)
            links = page.eval_on_selector_all(
                "a[href]",
                """els => els.map(e => ({
                    text: e.innerText.trim().substring(0, 80),
                    href: e.href
                }))""",
            )
            doc_links = [
                lk
                for lk in links
                if any(
                    kw in lk["text"]
                    for kw in ["下載", "須知", "文件", "規格", "附件"]
                )
                and "downloadNoticeDocument" in lk.get("href", "")
            ]
            result["download_links"] = doc_links

            # 3. Try to download 投標須知
            for lk in doc_links:
                if "downloadNoticeDocument" not in lk["href"]:
                    continue
                try:
                    with page.expect_download(timeout=15000) as dl_info:
                        page.evaluate(f"window.open('{lk['href']}')")
                    download = dl_info.value
                    fname = download.suggested_filename or "notice.odt"

                    # Parse ODT or read as text
                    tmp_path = str(DOCS_DIR / fname)
                    download.save_as(tmp_path)

                    doc_text = _parse_document(tmp_path)
                    if doc_text:
                        result["notice_doc"] = doc_text
                        logger.info("Downloaded and parsed: %s (%d chars)", fname, len(doc_text))
                    break  # only need first notice doc
                except Exception as e:
                    logger.warning("Failed to download notice doc: %s", e)

        except Exception as e:
            logger.error("Failed to scrape pcc page: %s", e)

        browser.close()

    return result


def _parse_document(file_path: str) -> str:
    """Parse ODT, DOCX, PDF, DOC, or plain text file to extract text content."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".odt":
        return _parse_odt(file_path)
    elif suffix == ".docx":
        return _parse_docx(file_path)
    elif suffix == ".pdf":
        return _parse_pdf(file_path)
    elif suffix == ".doc":
        return _parse_doc_binary(file_path)
    elif suffix in (".txt", ".csv"):
        return path.read_text(encoding="utf-8", errors="replace")
    else:
        # Try formats in order
        for parser in [_parse_odt, _parse_pdf, _parse_docx]:
            try:
                result = parser(file_path)
                if result and len(result) > 50:
                    return result
            except Exception:
                continue
        return ""


def _parse_odt(file_path: str) -> str:
    """Extract text from ODT file, preserving paragraph structure."""
    ns_text = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    paragraphs = []

    with zipfile.ZipFile(file_path) as z:
        with z.open("content.xml") as f:
            tree = ET.parse(f)
            root = tree.getroot()

            # Iterate over paragraph-level elements
            for para in root.iter(f"{{{ns_text}}}p"):
                parts = []
                for elem in para.iter():
                    if elem.text:
                        parts.append(elem.text)
                    if elem.tail:
                        parts.append(elem.tail)
                line = "".join(parts).strip()
                if line:
                    paragraphs.append(line)

            # Also check list items
            for li in root.iter(f"{{{ns_text}}}list-item"):
                parts = []
                for elem in li.iter():
                    if elem.text:
                        parts.append(elem.text)
                    if elem.tail:
                        parts.append(elem.tail)
                line = "".join(parts).strip()
                if line and line not in paragraphs:
                    paragraphs.append(line)

    return "\n".join(paragraphs)


def _parse_pdf(file_path: str) -> str:
    """Extract text from PDF file using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not installed, cannot parse PDF")
        return ""

    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages[:30]:  # limit to 30 pages
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n".join(texts)


def _parse_doc_binary(file_path: str) -> str:
    """Extract text from old .doc binary format.

    Uses a simple approach: read the file and extract readable Chinese/ASCII text.
    """
    try:
        raw = Path(file_path).read_bytes()

        # Try to decode as UTF-16LE (common in .doc)
        # .doc files store text in a binary format, but we can try to extract
        # readable portions by looking for Unicode text runs
        texts = []

        # Method 1: Look for Big5 or UTF-16 text runs
        # Try antiword if available
        import subprocess

        try:
            result = subprocess.run(
                ["textutil", "-convert", "txt", "-stdout", file_path],
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.decode("utf-8", errors="replace")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: extract readable text from binary
        # Try CP950 (Big5) decoding for Traditional Chinese .doc
        try:
            decoded = raw.decode("cp950", errors="replace")
            # Filter to lines with actual Chinese content
            for line in decoded.split("\n"):
                # Keep lines with Chinese characters
                chinese_chars = sum(1 for c in line if "\u4e00" <= c <= "\u9fff")
                if chinese_chars > 2:
                    texts.append(line.strip())
        except Exception:
            pass

        return "\n".join(texts) if texts else ""
    except Exception as e:
        logger.warning("Failed to parse .doc: %s", e)
        return ""


def _parse_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = []
    with zipfile.ZipFile(file_path) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
            for para in tree.iter(f"{{{ns['w']}}}p"):
                parts = []
                for run in para.iter(f"{{{ns['w']}}}t"):
                    if run.text:
                        parts.append(run.text)
                if parts:
                    texts.append("".join(parts))
    return "\n".join(texts)


def enrich_tender_case(unit_id: str, job_number: str) -> dict | None:
    """Fetch full detail for a tender: g0v API + pcc.gov.tw page + notice document.

    Returns enriched dict with all fields from fetch_tender_detail_api()
    plus: page_text, notice_doc, pcc_url.
    """
    # Step 1: Get structured data from g0v API
    detail = fetch_tender_detail_api(unit_id, job_number)
    if not detail:
        logger.warning("g0v API returned no data for %s/%s", unit_id, job_number)
        return None

    # Step 2: Get pcc.gov.tw URL from raw_json
    raw = detail.get("raw_json", {})
    pcc_url = raw.get("url", "") or detail.get("reference_url", "")
    pk_match = re.search(r"pkPmsMain=([^&]+)", pcc_url)

    if pk_match:
        # Step 3: Scrape pcc page + download notice doc
        try:
            pcc_data = fetch_pcc_page_content(pcc_url)
            detail["page_text"] = pcc_data.get("page_text", "")
            detail["notice_doc"] = pcc_data.get("notice_doc", "")
            detail["pcc_url"] = pcc_url
        except Exception as e:
            logger.error("pcc scrape failed for %s: %s", job_number, e)
            detail["page_text"] = ""
            detail["notice_doc"] = ""
            detail["pcc_url"] = pcc_url
    else:
        detail["page_text"] = ""
        detail["notice_doc"] = ""
        detail["pcc_url"] = ""

    return detail


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
