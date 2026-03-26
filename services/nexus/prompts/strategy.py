"""Context-aware follow-up strategy — dynamic prompt generation based on intent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.nexus.assistant.intents import Intent


# ---------------------------------------------------------------------------
# Priority field definitions per intent
# ---------------------------------------------------------------------------

_INTENT_PRIORITY_FIELDS: dict[str, list[str]] = {
    "capture_visit": [
        "next_meeting", "contact_name", "pain_points",
        "visit_outcome", "meeting_time", "decision_maker",
    ],
    "capture_meeting": [
        "pain_points", "budget", "decision_maker",
        "timeline", "competitors", "next_meeting",
    ],
    "capture_lead": [
        "budget", "timeline", "decision_maker",
        "competitors", "pain_points", "contact_name",
    ],
    "capture_card": [
        "role", "pain_points", "next_meeting",
        "company_name", "contact_title",
    ],
    "capture_subsidy": [
        "subsidy_name", "agency", "deadline",
        "funding_amount", "eligibility", "scope",
    ],
    "capture_general": [
        "role", "company_name", "contact_name",
        "pain_points", "budget", "next_meeting",
    ],
}

# Default fallback
_DEFAULT_PRIORITY = [
    "role", "company_name", "contact_name",
    "pain_points", "budget", "decision_maker",
]

# Field → Chinese label for prompt generation
_FIELD_LABELS_ZH: dict[str, str] = {
    "role": "分類（客戶/夥伴/補助）",
    "company_name": "公司名稱",
    "contact_name": "聯絡人姓名",
    "contact_title": "聯絡人職稱",
    "contact_email": "聯絡人 Email",
    "contact_phone": "聯絡人電話",
    "pain_points": "痛點/需求",
    "budget": "預算",
    "decision_maker": "決策者",
    "competitors": "競爭對手",
    "next_meeting": "下次會議",
    "meeting_time": "會議時間",
    "timeline": "期望時程",
    "nda_status": "NDA 狀態",
    "mou_status": "MOU 狀態",
    "deal_potential": "開案潛力",
    "visit_outcome": "拜訪結果",
    "subsidy_name": "計畫名稱",
    "agency": "主辦機關",
    "deadline": "截止日期",
    "funding_amount": "補助額度",
    "eligibility": "申請資格",
    "scope": "補助範疇",
}

# Intent → Chinese description for prompt context
_INTENT_LABELS_ZH: dict[str, str] = {
    "capture_visit": "拜訪筆記",
    "capture_meeting": "會議紀錄",
    "capture_lead": "商機線索",
    "capture_card": "名片資訊",
    "capture_subsidy": "補助資訊",
    "capture_general": "一般情報",
}


def get_priority_fields(intent: Intent, parsed: dict) -> list[str]:
    """Return prioritized list of fields to ask about, based on intent and known data.

    Fields already present in parsed are deprioritized (moved to end).
    """
    priority = _INTENT_PRIORITY_FIELDS.get(intent.value, _DEFAULT_PRIORITY)

    # Special case: visit with next_meeting but no time → ask time first
    if intent.value == "capture_visit":
        if parsed.get("next_meeting") and not parsed.get("meeting_time"):
            priority = ["meeting_time"] + [f for f in priority if f != "meeting_time"]

    to_ask = [f for f in priority if not parsed.get(f)]
    already_known = [f for f in priority if parsed.get(f)]
    return to_ask + already_known


def build_dynamic_followup_prompt(
    intent: Intent,
    parsed: dict,
    chat_history: list[dict],
    user_msg: str,
) -> str:
    """Build an intent-aware system prompt for the follow-up AI call.

    This wraps the base FOLLOWUP_PROMPT with additional intent-specific context
    that tells the AI what to prioritize asking about.
    """
    from services.nexus.prompts.followup import FOLLOWUP_PROMPT

    priority = get_priority_fields(intent, parsed)
    to_ask = [f for f in priority if not parsed.get(f)]

    # Build intent context block
    intent_label = _INTENT_LABELS_ZH.get(intent.value, "情報")
    context_lines = [f"[系統提示] 這筆情報的類型是「{intent_label}」。"]

    if to_ask:
        top_fields = to_ask[:3]
        labels = [_FIELD_LABELS_ZH.get(f, f) for f in top_fields]
        context_lines.append(
            f"目前最需要補齊的資訊（依重要性排序）：{' → '.join(labels)}"
        )
        context_lines.append(
            f"你必須在回覆中追問「{labels[0]}」。不要只是確認已知資訊，要主動問出缺少的。"
            f"用自然的口語方式問，不要像問卷調查。"
        )
    else:
        context_lines.append(
            "核心資訊已到位。確認使用者沒有要補充的，再建議 /done。"
            "例如：「還有什麼要補充的嗎？沒有的話我就存起來了」"
        )

    # Build chat history section
    chat_history_section = ""
    if chat_history:
        recent = chat_history[-6:]
        lines = []
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "AI"
            lines.append(f"{role}: {msg.get('text', '')}")
        chat_history_section = (
            "Previous conversation (DO NOT repeat questions already asked):\n"
            + "\n".join(lines)
        )

    # Inject intent context before the standard followup prompt
    intent_context = "\n".join(context_lines)

    prompt = FOLLOWUP_PROMPT.format(
        current_json=json.dumps(parsed, ensure_ascii=False, indent=2),
        user_msg=user_msg,
        chat_history_section=(
            f"{intent_context}\n\n{chat_history_section}"
            if chat_history_section
            else f"{intent_context}\n\n(First message.)"
        ),
    )
    return prompt
