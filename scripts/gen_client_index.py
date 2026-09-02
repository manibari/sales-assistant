"""Generate materials/clients/INDEX.md from nx_client + nx_deal + customer-intel reports.

Invoked by the crm-projection skill / headless agent. DB is read-only source.
"""

import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # script dir is sys.path[0], not the repo root

from services.nexus.clients import get_all_clients  # noqa: E402

INTEL_INDEX = ROOT / "reports" / "customer-intel" / "INDEX.md"
OUT = ROOT / "materials" / "clients" / "INDEX.md"
TZ = timezone(timedelta(hours=8))


def parse_intel_index() -> dict[str, str]:
    """company name -> report file name"""
    if not INTEL_INDEX.exists():
        return {}
    reports = {}
    for line in INTEL_INDEX.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or "報告檔案" in line:
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 2:
            continue
        m = re.search(r"\]\(([^)]+)\)", cols[1])
        if m:
            reports[cols[0]] = m.group(1)
    return reports


def fmt_money(v) -> str:
    if not v:
        return "—"
    n = float(v)
    if n <= 0:
        return "—"
    return f"{int(n / 10000)} 萬"


def match_intel(name: str, reports: dict[str, str]) -> str | None:
    if name in reports:
        return reports[name]
    # loose match: one contains the other (handles 股份有限公司 suffix variance)
    for company, path in reports.items():
        if name in company or company in name:
            return path
    return None


def main() -> None:
    clients = [c for c in get_all_clients() if c.get("status") == "active"]
    reports = parse_intel_index()
    now = datetime.now(TZ)
    cutoff = now - timedelta(days=30)

    rows = []
    for c in clients:
        rows.append(
            {
                "name": c["name"],
                "industry": c.get("industry") or "—",
                "budget_range": c.get("budget_range") or "—",
                "deal_count": c.get("deal_count") or 0,
                "pipeline": float(c.get("deal_budget_total") or 0),
                "pinned": bool(c.get("pinned")),
                "intel": match_intel(c["name"], reports),
                "created_at": c.get("created_at"),
            }
        )

    # name as final tiebreak keeps the file deterministic across runs (stable diffs)
    rows.sort(key=lambda r: (not r["pinned"], -r["deal_count"], -r["pipeline"], r["name"]))

    total_pipeline = sum(r["pipeline"] for r in rows)
    with_deals = sum(1 for r in rows if r["deal_count"] > 0)
    with_intel = sum(1 for r in rows if r["intel"])

    def is_new(r) -> bool:
        ts = r["created_at"]
        if not ts:
            return False
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return ts >= cutoff

    recent = sum(1 for r in rows if is_new(r))

    lines = [
        "# 客戶索引",
        "",
        "> 自動產生 by `crm-projection` — 請勿手動編輯",
        ">",
        "> 資料來源: nx_client + nx_deal (DB) + customer-intel 報告 (本地)",
        ">",
        f"> 最後更新: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC+08:00",
        "",
        "## 統計",
        "",
        f"- Active 客戶數: **{len(rows)}**",
        f"- 有進行中案件的客戶: **{with_deals}**",
        f"- 有 Intel 報告: **{with_intel}** / {len(rows)}",
        f"- Pipeline 總金額: **{fmt_money(total_pipeline)}** (NT$ {int(total_pipeline):,})",
        f"- 最近 30 天新增: **{recent}**",
        "",
        "## Active 客戶",
        "",
        "> 排序：釘選優先 → 進行中案件數 → Pipeline 金額由高至低",
        "",
        "| 客戶名稱 | 產業 | 預算區間 | 進行中案件 | Pipeline 金額 | Intel 報告 |",
        "|----------|------|----------|-----------|--------------|------------|",
    ]
    for r in rows:
        intel = f"[有](../../reports/customer-intel/{r['intel']})" if r["intel"] else "—"
        lines.append(
            f"| {r['name']} | {r['industry']} | {r['budget_range']} | "
            f"{r['deal_count']} | {fmt_money(r['pipeline'])} | {intel} |"
        )

    # 優先調查順序 = pipeline 金額，與上方表格的排序無關
    missing = sorted(
        (r for r in rows if not r["intel"] and r["pipeline"] > 0),
        key=lambda r: -r["pipeline"],
    )
    lines += [
        "",
        "## 缺少 Intel 報告的客戶（有 Pipeline）",
        "",
        "以下客戶有進行中案件但尚未建立 customer-intel 報告，建議優先調查：",
        "",
        "| 客戶名稱 | 產業 | Pipeline |",
        "|----------|------|----------|",
    ]
    for r in missing:
        lines.append(f"| {r['name']} | {r['industry']} | {fmt_money(r['pipeline'])} |")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("=== CRM Projection Summary ===")
    print(f"Date: {now.strftime('%Y-%m-%d')}")
    print(f"Active clients: {len(rows)}")
    print(f"Clients with deals: {with_deals}")
    print(f"Clients with intel: {with_intel}")
    print(f"Clients missing intel: {len(rows) - with_intel}")
    print(f"Missing intel with pipeline: {len(missing)}")
    print(f"Total pipeline: NT$ {int(total_pipeline):,}")
    print(f"New in last 30 days: {recent}")
    print("INDEX.md updated: Yes")


if __name__ == "__main__":
    main()
