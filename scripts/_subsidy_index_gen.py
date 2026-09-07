#!/usr/bin/env python3
"""Regenerate materials/subsidies/INDEX.md and by-industry/*.md from program files.

Markdown program files are the SSOT (see gov-subsidy-scraper skill). Run bare:
    python3 scripts/_subsidy_index_gen.py
"""
from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUB = ROOT / "materials" / "subsidies"
PROGRAMS = SUB / "programs"
BY_IND = SUB / "by-industry"
TODAY = date.today()
URGENT_DAYS = 90
URGENT_CUTOFF = TODAY + timedelta(days=URGENT_DAYS)

INDUSTRY_FILES = {
    "製造業": "manufacturing",
    "科技業": "technology",
    "服務業": "services",
    "零售業": "retail",
    "農業": "agriculture",
    "醫療業": "healthcare",
    "設計業": "design",
    "全產業": "all-industries",
}


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            fm[key.strip()] = [v.strip().strip('"\'') for v in val[1:-1].split(",") if v.strip()]
        else:
            fm[key.strip()] = val.strip('"\'')
    return fm


def load_active() -> list[dict]:
    rows = []
    for p in sorted(PROGRAMS.glob("*.md")):
        fm = parse_frontmatter(p)
        if not fm or fm.get("status", "active") != "active":
            continue
        fm["_file"] = p.name
        rows.append(fm)
    return rows


def sort_key(fm: dict):
    d = fm.get("deadline") or ""
    return (0, d, fm.get("name", "")) if d else (1, "", fm.get("name", ""))


def deadline_cell(fm: dict) -> str:
    d = fm.get("deadline") or ""
    if not d:
        return "長期/隨到隨審"
    try:
        dd = date.fromisoformat(d)
    except ValueError:
        return d
    return f"{d} ⚠️" if dd <= URGENT_CUTOFF else d


def is_urgent(fm: dict) -> bool:
    d = fm.get("deadline") or ""
    try:
        return bool(d) and date.fromisoformat(d) <= URGENT_CUTOFF
    except ValueError:
        return False


def write_index(rows: list[dict]) -> None:
    urgent = sum(1 for r in rows if is_urgent(r))
    lines = [
        "# 政府補助計畫索引 (INDEX)",
        "",
        f"> 自動產生於 {TODAY.isoformat()} by `subsidy-scraper` skill。資料來源：grants.nat.gov.tw / SBIR / SIIR 及各部會公告。",
        f"> **現行有效計畫：{len(rows)} 件**　|　封存（已截止）：見 `programs/archived/`",
        "",
        f"⚠️ = 截止日在 {URGENT_CUTOFF.isoformat()}（含）前，請優先處理（共 {urgent} 件）。",
        "",
        "| 補助名稱 | 主辦機關 | 截止日期 | 適用產業 | 詳情 |",
        "|----------|----------|----------|----------|------|",
    ]
    for r in rows:
        tags = "、".join(r.get("industry_tags") or [])
        lines.append(
            f"| {r.get('name','')} | {r.get('agency','')} | {deadline_cell(r)} | {tags} | [詳情](programs/{r['_file']}) |"
        )
    (SUB / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_by_industry(rows: list[dict]) -> int:
    BY_IND.mkdir(exist_ok=True)
    written = 0
    for tag, slug in INDUSTRY_FILES.items():
        subset = [r for r in rows if tag in (r.get("industry_tags") or [])]
        if not subset:
            continue
        lines = [
            f"# {tag} — 適用政府補助計畫",
            "",
            f"> 自動產生於 {TODAY.isoformat()} by `subsidy-scraper` skill。共 {len(subset)} 件適用計畫。",
            "",
            "| 補助名稱 | 主辦機關 | 截止日期 | 詳情 |",
            "|----------|----------|----------|------|",
        ]
        for r in subset:
            lines.append(
                f"| {r.get('name','')} | {r.get('agency','')} | {deadline_cell(r)} | [詳情](../programs/{r['_file']}) |"
            )
        (BY_IND / f"{slug}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        written += 1
    return written


def main() -> int:
    rows = sorted(load_active(), key=sort_key)
    write_index(rows)
    n = write_by_industry(rows)
    print(f"active={len(rows)} urgent={sum(1 for r in rows if is_urgent(r))} by_industry_files={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
