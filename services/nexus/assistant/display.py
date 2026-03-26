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


def format_initial_reply(intel_id: int, parsed: dict | None, has_missing: bool) -> str:
    """Format the first reply after intel creation."""
    if not parsed:
        lines = [
            f"📝 情報 #{intel_id} 已建立",
            "",
            "我沒辦法自動判斷分類，請直接告訴我更多細節！",
            "例如：這是哪種類型？（客戶/夥伴/政府補貼）",
            "",
            "輸入 /done 可隨時結束",
        ]
        return "\n".join(lines)

    lines = [
        f"📝 情報 #{intel_id} 已建立",
        f"📋 {format_summary(parsed)}",
    ]
    if has_missing:
        missing = missing_fields(parsed)
        missing_labels = [FIELD_LABELS.get(f, f) for f in missing[:3]]
        lines.append("")
        lines.append(f"還缺少：{' / '.join(missing_labels)}")
        lines.append("直接回覆補充，或輸入 /done 結束")
    else:
        lines.append("")
        lines.append("資訊已很完整！輸入 /done 確認，或繼續補充")
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
