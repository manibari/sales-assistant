"""AI enhancement for outreach — pitch and visit plan generation.

Called by services/nexus/outreach.py.
Data assembly (case studies, solutions, targets) stays in outreach.py.
"""

import logging

from services.ai_provider import generate_ai_response, check_ai_available
from services.nexus.prompts import PITCH_SYSTEM_PROMPT, VISIT_PLAN_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


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
        pitch = generate_ai_response(PITCH_SYSTEM_PROMPT, user_text)
        return {"pitch": pitch, "error": None}
    except Exception as e:
        logger.error("Pitch generation failed: %s", e)
        return {"pitch": None, "error": str(e)}


def generate_visit_plan(
    targets: list[dict],
    region: str | None = None,
    industry: str | None = None,
    case_studies: list[dict] | None = None,
    solutions: list[dict] | None = None,
) -> dict:
    """Generate an AI visit plan for batch outreach.

    Returns {"plan": str, "error": str | None}.
    """
    available, msg = check_ai_available()
    if not available:
        return {"plan": None, "error": msg}

    context_parts = []
    if region:
        context_parts.append(f"目標區域：{region}")
    if industry:
        context_parts.append(f"目標產業：{industry}")

    context_parts.append(f"\n目標公司（{len(targets)} 家）：")
    for t in targets:
        contacts_str = ""
        if t.get("contacts"):
            contacts_str = "；聯絡人：" + ", ".join(
                f"{c['name']}({c.get('title', '')})" for c in t["contacts"][:3]
            )
        context_parts.append(
            f"- {t['name']}（{t.get('industry', '?')}）"
            f"｜{t.get('deal_count', 0)} 商機{contacts_str}"
        )

    if case_studies:
        context_parts.append("\n可用案例：")
        for cs in case_studies[:3]:
            context_parts.append(
                f"- {cs.get('client', '?')}：{cs.get('outcome', '')}"
            )

    if solutions:
        context_parts.append("\n可用方案：")
        for sol in solutions[:3]:
            context_parts.append(f"- {sol.get('name', '?')}")

    user_text = "\n".join(context_parts)

    try:
        plan = generate_ai_response(VISIT_PLAN_SYSTEM_PROMPT, user_text)
        return {"plan": plan, "error": None}
    except Exception as e:
        logger.error("Visit plan generation failed: %s", e)
        return {"plan": None, "error": str(e)}
