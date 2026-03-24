#!/usr/bin/env python3
"""Analyze unmatched tenders to discover new keyword candidates.

Runs after tender_scraper.py. Reads the day's fetch results,
finds frequent terms in titles that DON'T match current keywords,
and writes candidates to keywords.yml for human review.

Usage:
    python scripts/tender_keyword_analyzer.py              # analyze today
    python scripts/tender_keyword_analyzer.py --days 3     # analyze last 3 days
    python scripts/tender_keyword_analyzer.py --auto       # auto-promote if threshold met
"""

import argparse
import logging
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KEYWORDS_PATH = PROJECT_ROOT / "materials" / "tenders" / "keywords.yml"

# Minimum occurrences to become a candidate
MIN_CANDIDATE_COUNT = 3
# Auto-promote threshold: seen N+ times across M+ days
AUTO_PROMOTE_COUNT = 10
AUTO_PROMOTE_DAYS = 3

# Terms to always ignore (too generic or noisy)
STOPWORDS = {
    "工程", "採購", "案", "委託", "服務", "計畫", "年度", "年",
    "115", "114", "113", "116", "117", "118",
    "第", "期", "及", "暨", "等", "項", "之", "含", "新",
    "設備", "維護", "更新", "建置", "設計", "施工", "監造",
    "臺", "市", "區", "縣", "鄉", "鎮", "局", "處", "所",
    "公司", "股份", "有限", "國立", "財團法人",
}


def load_keywords_config() -> dict:
    """Load keywords.yml config."""
    if KEYWORDS_PATH.exists():
        with open(KEYWORDS_PATH) as f:
            return yaml.safe_load(f) or {}
    return {"active": {}, "candidates": {}, "rejected": []}


def save_keywords_config(config: dict) -> None:
    """Save keywords.yml config."""
    with open(KEYWORDS_PATH, "w") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def get_active_keywords(config: dict) -> list[str]:
    """Flatten all active keywords into a single list."""
    keywords = []
    for category_keywords in (config.get("active") or {}).values():
        if isinstance(category_keywords, list):
            keywords.extend(category_keywords)
    return keywords


def extract_terms(title: str) -> list[str]:
    """Extract meaningful terms from a tender title.

    Uses a mix of:
    - Chinese character n-grams (2-4 chars)
    - English words/acronyms (2+ chars)
    """
    terms = []

    # English words/acronyms (uppercase)
    for m in re.finditer(r'[A-Za-z]{2,}', title):
        word = m.group().upper()
        if word not in STOPWORDS and len(word) >= 3:
            terms.append(word)

    # Chinese 2-gram, 3-gram, 4-gram
    chinese = re.sub(r'[^\u4e00-\u9fff]', '', title)
    for n in (2, 3, 4):
        for i in range(len(chinese) - n + 1):
            gram = chinese[i:i+n]
            if gram not in STOPWORDS:
                terms.append(gram)

    return terms


def analyze_unmatched(tenders: list[dict], active_keywords: list[str], rejected: list[str]) -> dict[str, dict]:
    """Find frequent terms in unmatched tender titles."""
    term_counts: Counter = Counter()
    term_titles: dict[str, list[str]] = defaultdict(list)

    for t in tenders:
        title = t.get("title", "")
        category = t.get("category", "")
        text = f"{title} {category}".lower()

        # Skip if already matched by active keywords
        if any(kw.lower() in text for kw in active_keywords):
            continue

        # Extract and count terms
        terms = extract_terms(title)
        seen = set()
        for term in terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                term_counts[term] += 1
                if len(term_titles[term]) < 3:
                    term_titles[term].append(title[:60])

    # Filter: minimum count, not rejected, not already active
    active_lower = {kw.lower() for kw in active_keywords}
    rejected_lower = {r.lower() for r in (rejected or [])}

    candidates = {}
    for term, count in term_counts.most_common(50):
        if count < MIN_CANDIDATE_COUNT:
            break
        if term.lower() in active_lower or term.lower() in rejected_lower:
            continue
        candidates[term] = {
            "count": count,
            "first_seen": date.today().isoformat(),
            "sample_titles": term_titles[term][:3],
        }

    return candidates


def run(days: int = 1, auto_promote: bool = False):
    """Main analysis pipeline."""
    config = load_keywords_config()
    active_keywords = get_active_keywords(config)
    rejected = config.get("rejected") or []

    logger.info("Active keywords: %d, Rejected: %d", len(active_keywords), len(rejected))

    # Collect tenders from scraper's daily logs (already fetched)
    # We read from case files + INDEX to find what was NOT matched
    # Actually, we need the raw listings. Use the scraper's fetch function.
    from scripts.tender_scraper import fetch_tenders_by_date, _wait_for_network

    if not _wait_for_network():
        logger.error("No network, skipping analysis")
        return

    all_tenders = []
    for i in range(days):
        target = date.today() - timedelta(days=i)
        listings = fetch_tenders_by_date(target)
        for listing in listings:
            brief = listing.get("brief", {})
            tender_type = brief.get("type", "")
            if any(skip in tender_type for skip in ["決標", "無法決標", "定期彙送"]):
                continue
            all_tenders.append({
                "title": brief.get("title", ""),
                "category": brief.get("category", ""),
            })

    logger.info("Analyzing %d tenders (excl 決標)", len(all_tenders))

    # Find candidates
    new_candidates = analyze_unmatched(all_tenders, active_keywords, rejected)
    logger.info("Found %d new keyword candidates", len(new_candidates))

    # Merge with existing candidates (accumulate counts)
    existing_candidates = config.get("candidates") or {}
    if not isinstance(existing_candidates, dict):
        existing_candidates = {}

    for term, info in new_candidates.items():
        if term in existing_candidates:
            old = existing_candidates[term]
            if isinstance(old, dict):
                old["count"] = old.get("count", 0) + info["count"]
                # Track unique days seen
                days_seen = old.get("days_seen", 1) + 1
                old["days_seen"] = days_seen
            else:
                existing_candidates[term] = info
                existing_candidates[term]["days_seen"] = 1
        else:
            info["days_seen"] = 1
            existing_candidates[term] = info

    # Auto-promote if threshold met
    promoted = []
    if auto_promote:
        to_remove = []
        for term, info in existing_candidates.items():
            if not isinstance(info, dict):
                continue
            if info.get("count", 0) >= AUTO_PROMOTE_COUNT and info.get("days_seen", 0) >= AUTO_PROMOTE_DAYS:
                # Add to active keywords under "auto_discovered" category
                if "auto_discovered" not in config["active"]:
                    config["active"]["auto_discovered"] = []
                config["active"]["auto_discovered"].append(term)
                promoted.append(term)
                to_remove.append(term)
        for term in to_remove:
            del existing_candidates[term]
        if promoted:
            logger.info("Auto-promoted %d keywords: %s", len(promoted), promoted)

    config["candidates"] = existing_candidates
    save_keywords_config(config)

    # Summary
    logger.info("Candidates in queue: %d", len(existing_candidates))
    if new_candidates:
        logger.info("Top new candidates:")
        for term, info in sorted(new_candidates.items(), key=lambda x: -x[1]["count"])[:10]:
            logger.info("  %s (%d hits) — e.g. %s", term, info["count"], info["sample_titles"][0][:40] if info["sample_titles"] else "")
    if promoted:
        logger.info("Auto-promoted: %s", ", ".join(promoted))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tender keyword analyzer")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--auto", action="store_true", help="Auto-promote high-confidence keywords")
    args = parser.parse_args()

    run(days=args.days, auto_promote=args.auto)
