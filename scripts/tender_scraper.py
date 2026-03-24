#!/usr/bin/env python3
"""Tender scraper — fetch government tenders from g0v API.

Strategy:
  1. Fetch ALL tenders from today's listing (all types, not just 公開徵求)
  2. Dedup against existing case files
  3. Create case files for new tenders
  4. Auto-enrich tenders matching AI/IT keywords with full content from pcc.gov.tw
  5. Archive past-deadline tenders
  6. Regenerate INDEX.md

Usage:
  python scripts/tender_scraper.py              # Today's tenders
  python scripts/tender_scraper.py --days 3     # Last 3 days
  python scripts/tender_scraper.py --enrich     # Also enrich matching tenders
"""

import argparse
import logging
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import requests
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CASES_DIR = PROJECT_ROOT / "materials" / "tenders" / "cases"
ARCHIVED_DIR = CASES_DIR / "archived"
INDEX_PATH = PROJECT_ROOT / "materials" / "tenders" / "INDEX.md"
BY_CATEGORY_DIR = PROJECT_ROOT / "materials" / "tenders" / "by-category"

G0V_LIST_URL = "https://pcc-api.openfun.app/api/listbydate"
G0V_TENDER_URL = "https://pcc-api.openfun.app/api/tender"

# Keywords loaded from keywords.yml (data-driven, not hardcoded).
# Fallback to hardcoded if yml not found.
def _load_keywords() -> list[str]:
    keywords_path = PROJECT_ROOT / "materials" / "tenders" / "keywords.yml"
    if keywords_path.exists():
        try:
            data = yaml.safe_load(keywords_path.read_text())
            keywords = []
            for cat_list in (data.get("active") or {}).values():
                if isinstance(cat_list, list):
                    keywords.extend(cat_list)
            if keywords:
                return keywords
        except Exception:
            pass
    # Fallback
    return [
        "人工智慧", "AI", "機器學習", "深度學習", "資訊系統", "軟體開發",
        "系統整合", "雲端", "資訊服務", "數位轉型", "資安", "資訊安全",
    ]

ENRICH_KEYWORDS = _load_keywords()

# Tender types to fetch (broadened from original 公開徵求 only)
TENDER_TYPES = [
    "公開取得報價單或企劃書",
    "公開招標",
    "公開徵求",
    "選擇性招標",
]


def _wait_for_network(host: str = "pcc-api.openfun.app", max_wait: int = 120) -> bool:
    """Wait until DNS resolves (handles launchd starting before network is ready)."""
    import socket
    import time as _time

    for attempt in range(max_wait // 10):
        try:
            socket.getaddrinfo(host, 443)
            return True
        except socket.gaierror:
            if attempt == 0:
                logger.warning("[network] DNS not ready, waiting...")
            _time.sleep(10)
    logger.error("[network] DNS still not available after %ds", max_wait)
    return False


def _fetch_with_retry(url: str, params: dict, max_retries: int = 3) -> requests.Response | None:
    """Fetch with exponential backoff for 429/5xx errors."""
    import time as _time

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                wait = 2 ** (attempt + 2)  # 4s, 8s, 16s
                logger.warning("[fetch] 429 rate limited, waiting %ds (attempt %d/%d)", wait, attempt + 1, max_retries)
                _time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.ConnectionError as e:
            wait = 2 ** (attempt + 1)
            logger.warning("[fetch] Connection error, retrying in %ds: %s", wait, e)
            _time.sleep(wait)
        except Exception as e:
            logger.error("[fetch] Unexpected error: %s", e)
            return None
    return None


def fetch_tenders_by_date(target_date: date) -> list[dict]:
    """Fetch tender listings for a given date from g0v API."""
    date_str = target_date.strftime("%Y%m%d")
    all_tenders = []
    page = 0

    while True:
        resp = _fetch_with_retry(G0V_LIST_URL, {"date": date_str, "page": page})
        if not resp:
            logger.error("Failed to fetch page %d for %s after retries", page, date_str)
            break

        try:
            data = resp.json()
        except Exception as e:
            logger.error("Invalid JSON on page %d for %s: %s", page, date_str, e)
            break

        records = data.get("records", [])
        if not records:
            break

        all_tenders.extend(records)
        logger.info("[fetch] page %d → %d records (total: %d)", page, len(records), len(all_tenders))
        page += 1

        if page >= 20:  # safety limit
            logger.warning("[fetch] hit page limit (20)")
            break

    logger.info("Fetched %d tenders for %s", len(all_tenders), date_str)
    return all_tenders


def fetch_tender_detail(unit_id: str, job_number: str) -> dict | None:
    """Fetch detailed tender info from g0v API."""
    from services.nexus.tender_detail_parser import fetch_tender_detail_api

    return fetch_tender_detail_api(unit_id, job_number)


def get_existing_job_numbers() -> set[str]:
    """Get set of job_numbers already in case files."""
    existing = set()
    for p in CASES_DIR.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        if text.startswith("---"):
            try:
                fm = yaml.safe_load(text.split("---", 2)[1])
                if fm and fm.get("job_number"):
                    existing.add(str(fm["job_number"]))
            except Exception:
                pass
    return existing


def should_enrich(title: str, category: str = "") -> bool:
    """Check if a tender matches our interest keywords for auto-enrichment."""
    text = f"{title} {category}".lower()
    return any(kw.lower() in text for kw in ENRICH_KEYWORDS)


def create_case_file(detail: dict, tags: list[str] | None = None) -> Path | None:
    """Create a markdown case file from tender detail."""
    job_number = detail.get("job_number", "")
    name = detail.get("name", "")
    if not job_number or not name:
        return None

    # Generate filename
    safe_name = re.sub(r"[^\w\u4e00-\u9fff]", "", name)[:20]
    filename = f"{job_number}-{safe_name}.md"
    filepath = CASES_DIR / filename

    if filepath.exists():
        return filepath

    # Auto-generate tags if not provided
    if tags is None:
        tags = _auto_tag(name, detail.get("category", ""))

    # Build frontmatter
    budget_raw = detail.get("budget", "")
    budget_val = None
    if budget_raw:
        nums = re.findall(r"[\d,]+", budget_raw.replace("(未公開)", ""))
        if nums:
            budget_val = int(nums[0].replace(",", ""))

    fm = {
        "title": name,
        "unit_name": detail.get("agency", ""),
        "job_number": job_number,
        "unit_id": str(detail.get("raw_json", {}).get("unit_id", "")),
        "type": detail.get("tender_type", ""),
        "category": detail.get("category", ""),
        "budget": budget_val,
        "deadline": detail.get("deadline"),
        "opening_date": detail.get("opening_date"),
        "contact_name": detail.get("contact_name"),
        "contact_phone": detail.get("contact_phone"),
        "contact_email": detail.get("contact_email"),
        "source_url": f"https://pcc-api.openfun.app/api/tender?unit_id={detail.get('raw_json', {}).get('unit_id', '')}&job_number={job_number}"
        if detail.get("raw_json")
        else "",
        "scraped_date": date.today().isoformat(),
        "status": "active",
        "tags": tags,
    }

    # Extract unit_id from raw_json if available
    if detail.get("raw_json"):
        raw = detail["raw_json"]
        if isinstance(raw, dict):
            # Try to find unit_id from the API response structure
            pass

    # Build markdown body
    budget_display = f"NT${budget_val:,}" if budget_val else budget_raw or "未公開"
    deadline_display = detail.get("deadline_raw", detail.get("deadline", "未定"))
    opening_display = detail.get("opening_raw", detail.get("opening_date", ""))

    body = f"""# {name}

## 基本資訊

| 欄位 | 內容 |
|------|------|
| 招標機關 | {detail.get('agency', '')} |
| 標案案號 | {job_number} |
| 招標方式 | {detail.get('tender_type', '')} |
| 採購類別 | {detail.get('category', '')} |
| 預算金額 | {budget_display} |
| 截止日期 | {deadline_display} |
| 開標日期 | {opening_display} |

## 聯絡資訊

- **聯絡人**: {detail.get('contact_name', 'N/A')}
- **電話**: {detail.get('contact_phone', 'N/A')}
- **Email**: {detail.get('contact_email', 'N/A')}
- **地址**: {detail.get('address', '')}

## 案件說明

{detail.get('scope_summary', detail.get('category', ''))}
"""

    if detail.get("qualification"):
        body += f"\n## 資格要求\n\n{detail['qualification']}\n"

    if detail.get("notes"):
        body += f"\n## 備註\n\n{detail['notes']}\n"

    # Write file
    content = f"---\n{yaml.dump(fm, allow_unicode=True, default_flow_style=False)}---\n\n{body}"
    filepath.write_text(content, encoding="utf-8")
    logger.info("Created: %s", filepath.name)
    return filepath


def _auto_tag(name: str, category: str) -> list[str]:
    """Generate tags from tender name and category."""
    tags = []
    text = f"{name} {category}"

    tag_map = {
        "資安": ["資安"], "ISMS": ["ISMS", "資安"], "資訊安全": ["資安"],
        "AI": ["AI"], "人工智慧": ["AI"], "機器學習": ["AI", "ML"],
        "影像辨識": ["影像辨識", "AI"], "電腦視覺": ["電腦視覺", "AI"],
        "大語言": ["LLM", "AI"], "LLM": ["LLM", "AI"], "GPT": ["LLM", "AI"],
        "自然語言": ["NLP", "AI"], "聊天機器人": ["Chatbot", "AI"],
        "系統維護": ["系統維護"], "軟體開發": ["軟體開發"],
        "資料庫": ["資料庫"], "雲端": ["雲端"],
        "網站": ["網站"], "平台": ["平台"],
        "消防": ["消防"], "教育": ["教育"],
        "醫療": ["醫療"], "衛生": ["衛生"],
        "交通": ["交通"], "環保": ["環保"],
    }

    for keyword, t_list in tag_map.items():
        if keyword in text:
            tags.extend(t_list)

    return list(dict.fromkeys(tags))[:8]  # dedupe, limit 8


def archive_past_deadline():
    """Move past-deadline tenders to archived status."""
    today = date.today()
    archived_count = 0

    for p in CASES_DIR.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue

        try:
            parts = text.split("---", 2)
            fm = yaml.safe_load(parts[1])
        except Exception:
            continue

        if not fm or fm.get("status") != "active":
            continue

        deadline_str = fm.get("deadline")
        if not deadline_str:
            continue

        try:
            dl = datetime.strptime(str(deadline_str), "%Y-%m-%d").date()
            if dl < today:
                fm["status"] = "archived"
                updated = f"---\n{yaml.dump(fm, allow_unicode=True, default_flow_style=False)}---\n{parts[2]}"
                p.write_text(updated, encoding="utf-8")
                archived_count += 1
                logger.info("Archived: %s (deadline %s)", p.name, deadline_str)
        except (ValueError, TypeError):
            pass

    return archived_count


def regenerate_index():
    """Regenerate INDEX.md from all case files."""
    active = []
    archived = []

    for p in sorted(CASES_DIR.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        try:
            fm = yaml.safe_load(text.split("---", 2)[1])
        except Exception:
            continue

        if not fm:
            continue

        budget_raw = fm.get("budget")
        if isinstance(budget_raw, (int, float)):
            budget_display = f"NT${int(budget_raw):,}"
        else:
            budget_display = "未公開"

        entry = {
            "name": fm.get("title", ""),
            "agency": fm.get("unit_name", ""),
            "category": fm.get("category", ""),
            "deadline": str(fm.get("deadline", "")),
            "budget": budget_display,
            "budget_val": int(budget_raw) if isinstance(budget_raw, (int, float)) else 0,
            "status": fm.get("status", "active"),
            "file": f"cases/{p.name}",
            "has_notice": "## 投標須知" in text,
        }

        if entry["status"] == "active":
            active.append(entry)
        else:
            archived.append(entry)

    # Sort active by deadline ASC
    active.sort(key=lambda e: e["deadline"] or "9999")
    archived.sort(key=lambda e: e["deadline"] or "9999", reverse=True)

    total_budget = sum(e["budget_val"] for e in active)

    lines = [
        "# 政府標案 — 等標期內案件",
        "",
        "> 自動產生，請勿手動編輯。由 tender_scraper.py 每日更新。",
        f"> 最後更新：{date.today().isoformat()}",
        "",
        f"## 等標期內案件（{len(active)} 件）",
        "",
        "| 標案名稱 | 招標機關 | 採購類別 | 截止日期 | 預算金額 | 內文 | 詳情 |",
        "|----------|---------|---------|---------|---------|------|------|",
    ]

    for e in active:
        notice = "✓" if e["has_notice"] else ""
        lines.append(
            f"| {e['name'][:30]} | {e['agency']} | {e['category'][:10]} | {e['deadline']} | {e['budget']} | {notice} | [詳情]({e['file']}) |"
        )

    lines.extend([
        "",
        f"## 已歸檔案件（{len(archived)} 件）",
        "",
        "| 標案名稱 | 招標機關 | 截止日期 | 歸檔原因 |",
        "|----------|---------|---------|---------|",
    ])

    for e in archived:
        lines.append(f"| {e['name'][:30]} | {e['agency']} | {e['deadline']} | 已過截止 |")

    lines.extend([
        "",
        "## 統計摘要",
        "",
        f"- 等標期內案件：**{len(active)} 件**",
        f"- 已歸檔案件：**{len(archived)} 件**",
        f"- 預算總計（已公開）：NT${total_budget:,}",
    ])

    if active:
        nearest = active[0]
        lines.append(f"- 最近截止：{nearest['deadline']}（{nearest['agency']} {nearest['name'][:15]}）")

    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Regenerated INDEX.md: %d active, %d archived", len(active), len(archived))


def fetch_pcc_open_requests(existing: set[str]) -> list[dict]:
    """Fetch 公開徵求 listings from pcc.gov.tw (not available in g0v API).

    Returns list of new tenders (filtered by keywords, deduped).
    """
    from services.nexus.tender_detail_parser import scrape_pcc_listings

    logger.info("[pcc 公開徵求] Scraping pcc.gov.tw for 公開徵求 listings (等標期內)...")
    listings = scrape_pcc_listings(
        tender_type="公開徵求",
        date_type="isNow",  # 等標期內 — all currently open
        max_pages=20,       # up to 1000 items (typical ~900)
    )

    new_tenders = []
    for item in listings:
        job_number = item.get("job_number", "")
        if not job_number or job_number in existing:
            continue

        name = item.get("name", "")
        nature = item.get("nature", "")

        if not should_enrich(name, nature):
            continue

        new_tenders.append({
            "job_number": job_number,
            "unit_id": "",  # pcc doesn't give unit_id directly
            "title": name,
            "tender_type": "公開徵求廠商提供參考資料",
            "category": nature,
            "unit_name": item.get("agency", ""),
            "detail_url": item.get("detail_url", ""),
        })
        existing.add(job_number)

    logger.info("[pcc 公開徵求] New keyword-matching tenders: %d (from %d total)", len(new_tenders), len(listings))
    return new_tenders


def run(days: int = 1, do_enrich: bool = True):
    """Main scraper pipeline."""
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVED_DIR.mkdir(parents=True, exist_ok=True)

    # Wait for network (launchd may start before WiFi/DNS is ready)
    if not _wait_for_network():
        logger.error("Aborting: no network connectivity")
        return

    existing = get_existing_job_numbers()
    logger.info("Existing cases: %d", len(existing))

    # Step 1a: Fetch tender listings from g0v API
    logger.info("[step 1/5] Fetching tender listings from g0v (days=%d)...", days)
    new_tenders = []
    for i in range(days):
        target = date.today() - timedelta(days=i)
        logger.info("[step 1/5] Fetching date: %s", target.isoformat())
        listings = fetch_tenders_by_date(target)

        for listing in listings:
            job_number = listing.get("job_number", "")
            if not job_number or job_number in existing:
                continue

            brief = listing.get("brief", {})
            title = brief.get("title", "")
            tender_type = brief.get("type", "")
            unit_id = listing.get("unit_id", "")
            category = brief.get("category", "")

            # Skip non-bidding announcements (決標, 無法決標, etc.)
            if any(skip in tender_type for skip in ["決標", "無法決標", "定期彙送"]):
                continue

            # Only keep tenders that match our interest keywords
            if not should_enrich(title, category):
                continue

            new_tenders.append({
                "job_number": job_number,
                "unit_id": unit_id,
                "title": title,
                "tender_type": tender_type,
                "category": category,
                "unit_name": listing.get("unit_name", ""),
            })
            existing.add(job_number)

    logger.info("New tenders from g0v: %d", len(new_tenders))

    # Step 1b: Also fetch 公開徵求 from pcc.gov.tw (better coverage)
    pcc_tenders = fetch_pcc_open_requests(existing)
    new_tenders.extend(pcc_tenders)

    logger.info("Total new tenders (g0v + pcc): %d", len(new_tenders))

    # Step 2: Fetch detail and create case files
    logger.info("[step 2/5] Creating case files for %d new tenders...", len(new_tenders))
    created = 0
    enrich_queue = []

    for idx, t in enumerate(new_tenders, 1):
        logger.info("[step 2/5] (%d/%d) %s — %s", idx, len(new_tenders), t["job_number"], t["title"][:40])

        detail = None
        if t.get("unit_id"):
            # Has unit_id → try g0v API for structured detail
            detail = fetch_tender_detail(t["unit_id"], t["job_number"])

        if not detail:
            # No unit_id or g0v failed → create minimal case (enrich will backfill via pcc)
            detail = {
                "name": t["title"],
                "agency": t.get("unit_name", ""),
                "job_number": t["job_number"],
                "tender_type": t["tender_type"],
                "category": t["category"],
                "raw_json": {"unit_id": t.get("unit_id", "")},
            }

        if "raw_json" not in detail:
            detail["raw_json"] = {}
        detail["raw_json"]["unit_id"] = t.get("unit_id", "")

        filepath = create_case_file(detail)
        if filepath:
            created += 1

            # Check if this tender should be enriched
            if should_enrich(t["title"], t["category"]):
                enrich_queue.append(t["job_number"])

    logger.info("Created %d new case files", created)

    # Step 3: Auto-enrich matching tenders
    if do_enrich and enrich_queue:
        logger.info("[step 3/5] Auto-enriching %d tenders...", len(enrich_queue))
        from services.nexus.tenders import enrich_tender

        for idx, job_number in enumerate(enrich_queue, 1):
            logger.info("[step 3/5] (%d/%d) enriching %s", idx, len(enrich_queue), job_number)
            try:
                result = enrich_tender(job_number)
                logger.info("Enriched %s: %d sections added", job_number, result.get("sections_added", 0))
            except Exception as e:
                logger.error("Enrich failed for %s: %s", job_number, e)

    # Step 4: Archive past-deadline tenders
    logger.info("[step 4/5] Archiving past-deadline tenders...")
    archived = archive_past_deadline()
    logger.info("[step 4/5] Archived %d tenders", archived)

    # Step 5: Regenerate INDEX.md
    logger.info("[step 5/5] Regenerating INDEX.md...")
    regenerate_index()

    # Summary
    print(f"\n=== Tender Scraper Summary ===")
    print(f"  New tenders found: {len(new_tenders)}")
    print(f"  Case files created: {created}")
    print(f"  Auto-enriched: {len(enrich_queue)}")
    print(f"  Archived: {archived}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tender scraper")
    parser.add_argument("--days", type=int, default=1, help="Number of days to look back")
    parser.add_argument("--no-enrich", action="store_true", help="Skip auto-enrichment")
    args = parser.parse_args()

    run(days=args.days, do_enrich=not args.no_enrich)
