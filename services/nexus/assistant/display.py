"""Display helpers — label maps, formatters, field validation.

Extracted from telegram.py to share between engine handlers and adapters.
"""

# ---------------------------------------------------------------------------
# Field definitions per role (for missing-field detection)
# ---------------------------------------------------------------------------

ROLE_FIELDS: dict[str, list[str]] = {
    "client": [
        "industry",
        "pain_points",
        "nda_status",
        "mou_status",
        "budget",
        "deal_potential",
    ],
    "partner": ["capabilities", "team_size"],
    "subsidy": [
        "subsidy_name",
        "agency",
        "funding_amount",
        "deadline",
        "subsidy_partner",
        "subsidy_deadline",
    ],
    "si": [],
    "other": [],
}


def missing_fields(parsed: dict) -> list[str]:
    """Return field names that are still missing based on role."""
    role = parsed.get("role")
    if not role:
        return ["role"]
    expected = ROLE_FIELDS.get(role, [])
    return [f for f in expected if f not in parsed]


# ---------------------------------------------------------------------------
# Label maps
# ---------------------------------------------------------------------------

ROLE_LABELS = {
    "client": "客戶",
    "partner": "夥伴",
    "subsidy": "政府補貼",
    "si": "SI",
    "other": "其他",
}

KNOWN_INDUSTRIES = {
    "food",
    "petrochemical",
    "semiconductor",
    "manufacturing",
    "tech",
    "finance",
    "healthcare",
    "transportation",
    "other",
}

INDUSTRY_LABELS = {
    "food": "食品業",
    "petrochemical": "石化業",
    "semiconductor": "半導體",
    "manufacturing": "製造業",
    "tech": "科技",
    "finance": "金融",
    "healthcare": "醫療",
    "transportation": "交通運輸",
    "other": "其他",
}

# Custom industries added at runtime (persists until server restart)
custom_industries: dict[str, str] = {}  # { snake_key: "中文 label" }

PAIN_LABELS = {
    "automation": "產線自動化",
    "aoi": "AOI",
    "energy": "能源管理",
    "safety": "安全監控",
    "erp": "ERP/系統整合",
    "iot": "IoT",
}

FIELD_LABELS = {
    "role": "分類",
    "industry": "產業",
    "pain_points": "痛點",
    "nda_status": "NDA",
    "mou_status": "MOU",
    "budget": "預算",
    "deal_potential": "開案潛力",
    "capabilities": "能力",
    "team_size": "團隊規模",
    "subsidy_name": "計畫名稱",
    "agency": "主辦機關",
    "funding_amount": "補助額度",
    "deadline": "截止日期",
    "eligibility": "申請資格",
    "scope": "補助範疇",
    "subsidy_partner": "合作夥伴",
    "subsidy_deadline": "截止期程",
}


def get_industry_label(key: str) -> str:
    """Get display label for an industry key (known or custom)."""
    return INDUSTRY_LABELS.get(key) or custom_industries.get(key) or key


def check_new_industry(parsed: dict) -> str | None:
    """If parsed contains an unknown industry, return a confirmation prompt."""
    ind = parsed.get("industry")
    if not ind or ind in KNOWN_INDUSTRIES or ind in custom_industries:
        return None
    label = parsed.pop("industry_label", None) or ind
    custom_industries[ind] = label
    return (
        f"🆕 偵測到新產業分類：「{label}」（{ind}）\n"
        "要使用這個分類嗎？回覆「是」確認，或告訴我正確的產業"
    )


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def format_summary(parsed: dict) -> str:
    """One-line summary of parsed fields."""
    parts = []
    if role := parsed.get("role"):
        parts.append(ROLE_LABELS.get(role, role))
    if sn := parsed.get("subsidy_name"):
        parts.append(sn)
    if co := parsed.get("company_name"):
        parts.append(co)
    if ag := parsed.get("agency"):
        parts.append(f"機關：{ag}")
    if fa := parsed.get("funding_amount"):
        parts.append(f"額度：{fa}")
    if dl := parsed.get("deadline"):
        parts.append(f"截止：{dl}")
    if ind := parsed.get("industry"):
        parts.append(get_industry_label(ind))
    if pains := parsed.get("pain_points"):
        labels = [PAIN_LABELS.get(p, p) for p in pains]
        parts.append(f"痛點：{'、'.join(labels)}")
    if budget := parsed.get("budget"):
        wan = int(budget) / 10000
        parts.append(f"預算：{wan:.0f}萬")
    if caps := parsed.get("capabilities"):
        parts.append(f"能力：{'、'.join(caps)}")
    if ts := parsed.get("team_size"):
        parts.append(f"團隊：{ts}人")
    if dp := parsed.get("deal_potential"):
        dp_labels = {"high": "高", "medium": "中", "low": "低", "none": "無"}
        parts.append(f"開案潛力：{dp_labels.get(dp, dp)}")
    if cn := parsed.get("contact_name"):
        ct = parsed.get("contact_title", "")
        ce = parsed.get("contact_email", "")
        cp = parsed.get("contact_phone", "")
        detail = f"聯絡人：{cn}"
        if ct:
            detail += f"（{ct}）"
        extras = [x for x in (cp, ce) if x]
        if extras:
            detail += f" {' / '.join(extras)}"
        parts.append(detail)
    if nm := parsed.get("next_meeting"):
        parts.append(f"下次會議：{nm}")
    return " | ".join(parts) if parts else "（無解析結果）"


_FIRST_QUESTION_MAP: dict[str, str] = {
    "role": "這是客戶、夥伴、還是政府補助的情報？",
    "company_name": "這是哪家公司？",
    "contact_name": "對方聯絡人是誰？",
    "industry": "他們是什麼產業？",
    "pain_points": "他們的痛點或需求是什麼？",
    "budget": "預算大概多少？",
    "deal_potential": "你覺得成案機會高嗎？",
    "nda_status": "NDA 簽了嗎？",
    "mou_status": "MOU 簽了嗎？",
    "subsidy_name": "計畫名稱是什麼？",
    "agency": "主辦機關是哪個？",
    "deadline": "截止日期是什麼時候？",
    "funding_amount": "補助額度大概多少？",
    "capabilities": "他們主要能力是什麼？",
    "team_size": "團隊多大？",
}


def format_initial_reply(intel_id: int, parsed: dict | None, has_missing: bool) -> str:
    """Format the first reply after intel creation — always ask a specific question."""
    if not parsed:
        lines = [
            f"📝 情報 #{intel_id} 已建立",
            "",
            "收到了，先幫你記下來。",
            "這是哪種類型的情報？（客戶 / 夥伴 / 政府補貼）",
        ]
        return "\n".join(lines)

    lines = [
        f"📝 情報 #{intel_id} 已建立",
        f"📋 {format_summary(parsed)}",
    ]
    if has_missing:
        missing = missing_fields(parsed)
        # Ask the first missing field directly
        first_missing = missing[0] if missing else None
        question = _FIRST_QUESTION_MAP.get(first_missing, "")
        remaining = [FIELD_LABELS.get(f, f) for f in missing[1:3]]
        lines.append("")
        if question:
            lines.append(question)
        if remaining:
            lines.append(f"（之後還想知道：{' / '.join(remaining)}）")
    else:
        lines.append("")
        lines.append("資訊蠻完整的，還有什麼要補充的嗎？沒有的話輸入 /done 就好")
    return "\n".join(lines)


def format_card_raw(card: dict) -> str:
    """Format a parsed business card dict into readable text."""
    parts = []
    if card.get("company_name"):
        parts.append(f"公司：{card['company_name']}")
    if card.get("contact_name"):
        parts.append(f"姓名：{card['contact_name']}")
    if card.get("contact_title"):
        parts.append(f"職稱：{card['contact_title']}")
    if card.get("contact_phone"):
        parts.append(f"電話：{card['contact_phone']}")
    if card.get("contact_email"):
        parts.append(f"Email：{card['contact_email']}")
    if card.get("line_id"):
        parts.append(f"LINE：{card['line_id']}")
    if card.get("department"):
        parts.append(f"部門：{card['department']}")
    return "\n".join(parts) if parts else "（無法辨識）"
