"""Nexus outreach service — cold outreach: case study matching, pitch generation."""

import logging
import os
import re
from pathlib import Path

import yaml

from database.connection import get_connection, rows_to_dicts
from services.ai_provider import generate_ai_response, check_ai_available

logger = logging.getLogger(__name__)

MATERIALS_DIR = Path(__file__).resolve().parent.parent.parent / "materials"
CASE_STUDIES_DIR = MATERIALS_DIR / "case-studies"
SOLUTIONS_DIR = MATERIALS_DIR / "solutions"


# ---------------------------------------------------------------------------
# Read materials from filesystem
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict | None:
    """Parse YAML frontmatter from a markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
        if not match:
            return None
        meta = yaml.safe_load(match.group(1))
        meta["_body"] = match.group(2).strip()
        meta["_file"] = path.name
        return meta
    except Exception as e:
        logger.warning("Failed to parse %s: %s", path, e)
        return None


def get_case_studies(industry: str | None = None) -> list[dict]:
    """Get case studies, optionally filtered by industry."""
    if not CASE_STUDIES_DIR.exists():
        return []
    studies = []
    for f in CASE_STUDIES_DIR.glob("*.md"):
        if f.name == "INDEX.md":
            continue
        meta = _parse_frontmatter(f)
        if not meta:
            continue
        if industry and not _industry_match(meta.get("industry", ""), industry):
            continue
        studies.append(meta)
    return studies


def get_solutions(industry: str | None = None) -> list[dict]:
    """Get solution templates, optionally filtered by target industry."""
    if not SOLUTIONS_DIR.exists():
        return []
    solutions = []
    for f in SOLUTIONS_DIR.rglob("*.md"):
        if f.name == "INDEX.md":
            continue
        meta = _parse_frontmatter(f)
        if not meta:
            continue
        if industry:
            targets = meta.get("target_industry", [])
            if isinstance(targets, list):
                if not any(_industry_match(t, industry) for t in targets):
                    continue
        solutions.append(meta)
    return solutions


def _industry_match(material_industry: str, query: str) -> bool:
    """Fuzzy industry match: 食品製造 matches 食品, food matches food."""
    a = material_industry.lower()
    b = query.lower()
    return b in a or a in b


def get_available_industries() -> list[dict]:
    """List industries that have case studies or solutions."""
    industries: dict[str, dict] = {}

    for cs in get_case_studies():
        ind = cs.get("industry", "其他")
        if ind not in industries:
            industries[ind] = {"industry": ind, "case_studies": 0, "solutions": 0}
        industries[ind]["case_studies"] += 1

    for sol in get_solutions():
        for target in sol.get("target_industry", []):
            if target not in industries:
                industries[target] = {"industry": target, "case_studies": 0, "solutions": 0}
            industries[target]["solutions"] += 1

    return list(industries.values())


# ---------------------------------------------------------------------------
# Target companies from DB
# ---------------------------------------------------------------------------


def get_target_companies(industry: str | None = None) -> list[dict]:
    """Get potential target companies from nx_client, with deal counts."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if industry:
                cur.execute(
                    """SELECT c.id, c.name, c.industry, c.status,
                              (SELECT COUNT(*) FROM nx_deal d
                               WHERE d.client_id = c.id AND d.status = 'active') AS deal_count,
                              (SELECT COUNT(*) FROM nx_contact ct
                               WHERE ct.org_type = 'client' AND ct.org_id = c.id) AS contact_count
                       FROM nx_client c
                       WHERE c.status = 'active'
                         AND c.industry ILIKE %s
                       ORDER BY deal_count DESC, c.name""",
                    (f"%{industry}%",),
                )
            else:
                cur.execute(
                    """SELECT c.id, c.name, c.industry, c.status,
                              (SELECT COUNT(*) FROM nx_deal d
                               WHERE d.client_id = c.id AND d.status = 'active') AS deal_count,
                              (SELECT COUNT(*) FROM nx_contact ct
                               WHERE ct.org_type = 'client' AND ct.org_id = c.id) AS contact_count
                       FROM nx_client c
                       WHERE c.status = 'active'
                       ORDER BY deal_count DESC, c.name"""
                )
            return rows_to_dicts(cur)


def get_contacts_for_client(client_id: int) -> list[dict]:
    """Get contacts for a specific client."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, name, title, phone, email, line_id, role
                   FROM nx_contact
                   WHERE org_type = 'client' AND org_id = %s
                   ORDER BY name""",
                (client_id,),
            )
            return rows_to_dicts(cur)


# ---------------------------------------------------------------------------
# AI Pitch Generation
# ---------------------------------------------------------------------------

_PITCH_SYSTEM_PROMPT = """你是一位 B2B 業務策略顧問，專長於製作陌生開發說帖。

根據提供的案例、方案和目標公司資訊，生成一份簡潔有力的說帖（pitch），包含：

1. **開場切入點**（1-2 句）：針對該產業的痛點，引起對方興趣
2. **案例佐證**（2-3 句）：引用成功案例的具體成果數字
3. **方案亮點**（3-5 個要點）：適合該公司的解決方案重點
4. **行動呼籲**（1 句）：建議的下一步

語氣：專業但親切，避免過度推銷。使用繁體中文。
控制在 300 字以內。"""


def generate_pitch(
    target_company: str,
    target_industry: str,
    case_studies: list[dict],
    solutions: list[dict],
    knowledge_context: str | None = None,
) -> dict:
    """Generate an AI pitch for cold outreach.

    Returns {"pitch": str, "error": str | None}.
    """
    available, msg = check_ai_available()
    if not available:
        return {"pitch": None, "error": msg}

    # Build context
    context_parts = [f"目標公司：{target_company}（{target_industry}）"]

    for cs in case_studies[:2]:
        context_parts.append(
            f"\n案例：{cs.get('client', '?')}（{cs.get('industry', '?')}）"
            f"\n方案：{', '.join(cs.get('solution_type', []))}"
            f"\n成果：{cs.get('outcome', '未提供')}"
            f"\n期間：{cs.get('duration', '?')}"
        )

    for sol in solutions[:2]:
        context_parts.append(
            f"\n方案模板：{sol.get('name', '?')}"
            f"\n預算範圍：{sol.get('typical_budget', '?')}"
            f"\n期間：{sol.get('typical_duration', '?')}"
        )

    if knowledge_context:
        context_parts.append(f"\n相關知識庫摘要：\n{knowledge_context[:1000]}")

    user_text = "\n".join(context_parts)

    try:
        pitch = generate_ai_response(_PITCH_SYSTEM_PROMPT, user_text)
        return {"pitch": pitch, "error": None}
    except Exception as e:
        logger.error("Pitch generation failed: %s", e)
        return {"pitch": None, "error": str(e)}
