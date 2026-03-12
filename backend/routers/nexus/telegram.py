"""Telegram Bot webhook — conversational intel capture + AI parse."""

import asyncio
import json
import logging
import os
from pathlib import Path

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request

from services.ai_provider import check_ai_available, generate_ai_response, generate_ai_vision_response
from services.nexus.documents import create_file
from services.nexus.intel import confirm_intel, create_intel, update_intel
from services.nexus.deals import get_deals_by_client, link_intel_to_deal

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"

# ---------------------------------------------------------------------------
# Conversation state (in-memory, keyed by chat_id)
# ---------------------------------------------------------------------------

# { chat_id: { "intel_id": int, "parsed": dict, "raw_history": [str, ...] } }
_conversations: dict[int, dict] = {}

# Post-done state: pending deal creation prompt
# { chat_id: { "intel_id": int, "client_id": int, "client_name": str, "parsed": dict } }
_pending_deal: dict[int, dict] = {}

# Registered chat IDs for daily digest (persisted to file)
_REGISTERED_CHATS_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".telegram_chats.json"


def _load_registered_chats() -> set[int]:
    if _REGISTERED_CHATS_FILE.exists():
        try:
            return set(json.loads(_REGISTERED_CHATS_FILE.read_text()))
        except (json.JSONDecodeError, TypeError):
            pass
    return set()


def _save_registered_chats(chats: set[int]) -> None:
    _REGISTERED_CHATS_FILE.write_text(json.dumps(sorted(chats)))


_registered_chats: set[int] = _load_registered_chats()


# ---------------------------------------------------------------------------
# AI prompts
# ---------------------------------------------------------------------------

INTEL_PARSE_PROMPT = """\
You are an intel classifier for a B2B sales assistant.
The user (our company) sells technology solutions. Extract structured fields from their input.

IMPORTANT context for role classification:
- "client" = a company that BUYS from us or needs our services (they have a problem we solve)
- "partner" = a company we COLLABORATE with to deliver solutions together
- "subsidy" = government subsidy / grant opportunity
- "si" = system integrator
- If someone mentions a company wanting to outsource, find vendors, or needs custom development → they are a "client"
- If someone mentions a company with complementary skills to join forces → they are a "partner"

Return ONLY a JSON object. Do NOT wrap in markdown code fences.
Omit any field you are not confident about — never guess.

Available fields and allowed values:

role: "client" | "partner" | "subsidy" | "si" | "other"
industry: "food" | "petrochemical" | "semiconductor" | "manufacturing" | "tech" | "finance" | "healthcare" | "transportation" | "other"
  If NONE of the above fit well, you may suggest a NEW industry value:
  - Use a short English snake_case key (e.g. "travel_tech", "logistics", "energy", "retail", "education")
  - Also add "industry_label" with the Chinese name (e.g. "旅遊科技", "物流業", "能源業")
  Do NOT use "other" if you can identify a specific industry — suggest a new one instead.
pain_points: array of "automation" | "aoi" | "energy" | "safety" | "erp" | "iot" (client only)
  ("erp" covers system integration, custom development, IT outsourcing needs)
nda_status: "pending" | "in_progress" | "signed" | "not_required" (client only)
mou_status: "pending" | "in_progress" | "signed" | "not_required" (client only)
budget: integer in TWD (e.g. 3000000 for 300萬) (client only)
capabilities: array of "iot" | "vision" | "erp" | "auto_ctrl" | "security" | "ml_ai" (partner only)
team_size: "1-10" | "10-50" | "50-200" | "200+" (partner only)
subsidy_partner: "has_partner" | "searching" | "not_required" | "undecided" (subsidy only)
subsidy_deadline: "within_1m" | "1-3m" | "3m+" | "unknown" (subsidy only)

Subsidy-specific free-form fields (capture when role is "subsidy"):
subsidy_name: official program name (e.g. "中小企業數位轉型計畫", "SBIR 115年度")
agency: issuing government agency (e.g. "經濟部中小及新創企業署", "工業局")
funding_amount: subsidy amount description (e.g. "200萬~300萬", "最高1,000萬")
deadline: application deadline (free text, e.g. "3/31截止", "115年6月30日")
eligibility: who can apply (free text)
scope: what the program covers (free text)

Free-form fields (any string, capture if mentioned):
company_name: the company/organization name (the PRIMARY entity — usually client)
contact_name: contact person's name (at the primary company)
contact_title: their job title
contact_email: email
contact_phone: phone
decision_maker: who makes the buying decision
competitors: other vendors being considered (NOT partners/collaborators!)
next_meeting: next meeting date/time (free text is fine)
timeline: when they want to start
notes: any other important detail

Partner/collaborator fields (capture when a SEPARATE partner company is mentioned alongside client):
partner_name: partner/collaborator company name (e.g. 中華電信, if they are working WITH the client)
partner_contact_name: contact person at the partner company
partner_contact_title: partner contact's job title
partner_contact_email: partner contact's email
partner_contact_phone: partner contact's phone

Deal potential field:
deal_potential: "high" | "medium" | "low" | "none"
  - "high" = clear need + budget + timeline, ready to create a deal
  - "medium" = has interest but unclear budget/timeline
  - "low" = exploratory, no concrete plan
  - "none" = no deal potential (info only, internal reference)
  Infer from context: mentions of budget, timeline, concrete needs → higher potential

IMPORTANT distinctions:
- "合作夥伴" / "partner" / "一起合作" → use partner_name, NOT competitors
- "競爭對手" / "也在談" / "也有報價" → use competitors
- If one company is the client and another helps deliver the solution → second is partner_name

Example 1: "跟台積電開會，他們想做AOI自動化，預算500萬"
→ {"role":"client","company_name":"台積電","industry":"semiconductor","pain_points":["aoi","automation"],"budget":5000000,"deal_potential":"high"}

Example 2: "Sabre 想找外部團隊做客製化開發"
→ {"role":"client","company_name":"Sabre","industry":"tech","pain_points":["erp"]}

Example 3: "跟一家做IoT的新創談合作，他們10人團隊"
→ {"role":"partner","company_name":"","capabilities":["iot"],"team_size":"1-10"}

Example 4: "今天跟王經理聊了，他是鴻海的採購主管，下週三再約"
→ {"role":"client","company_name":"鴻海","industry":"manufacturing","contact_name":"王經理","contact_title":"採購主管","next_meeting":"下週三"}

Example 5: "永豐紙業想做 IOT，目前合作夥伴是中華電信，對方聯絡人是吳欣曄"
→ {"role":"client","company_name":"永豐紙業","industry":"manufacturing","pain_points":["iot"],"partner_name":"中華電信","partner_contact_name":"吳欣曄"}
"""

FOLLOWUP_PROMPT = """\
You are a sharp B2B sales assistant chatbot speaking Traditional Chinese.
You are helping the user capture intel from a sales interaction through natural conversation.

Think like a sales manager debriefing a rep after a meeting — ask practical, actionable follow-ups.

Current intel so far:
{current_json}

The user just said: "{user_msg}"

Do TWO things in your response, separated by exactly "---" on its own line:

PART 1 (above ---): A short, natural reply in Traditional Chinese (2-4 sentences).
- Acknowledge what the user shared
- Ask ONE practical follow-up question based on context. Prioritize questions like:
  • 對方的聯絡人是誰？有拿到名片嗎？（contact_name, contact_title, contact_email, contact_phone）
  • 有約下次會議嗎？大概什麼時候？（next_meeting）
  • 他們的痛點或需求具體是什麼？
  • 預算範圍大概多少？誰是決策者？（decision_maker）
  • 有沒有競爭對手也在談？（competitors）
  • 時程急不急？他們希望什麼時候開始？（timeline）
  • NDA/MOU 狀態？
- Pick the most natural next question based on what's already known and what's missing
- If the info seems pretty complete, say so and suggest /done

PART 2 (below ---): A JSON object with ANY new or updated fields from the user's message.
Return ONLY new/changed fields. Do NOT repeat existing ones. Omit uncertain fields.
Do NOT wrap in markdown code fences.

Structured fields (allowed values):
role: "client" | "partner" | "subsidy" | "si" | "other"
industry: "food" | "petrochemical" | "semiconductor" | "manufacturing" | "tech" | "finance" | "healthcare" | "transportation" | "other"
  (If none fit, suggest a new snake_case key + add "industry_label" with Chinese name)
pain_points: array of "automation" | "aoi" | "energy" | "safety" | "erp" | "iot"
nda_status: "pending" | "in_progress" | "signed" | "not_required"
mou_status: "pending" | "in_progress" | "signed" | "not_required"
budget: integer in TWD
capabilities: array of "iot" | "vision" | "erp" | "auto_ctrl" | "security" | "ml_ai"
team_size: "1-10" | "10-50" | "50-200" | "200+"
subsidy_partner: "has_partner" | "searching" | "not_required" | "undecided"
subsidy_deadline: "within_1m" | "1-3m" | "3m+" | "unknown"

Free-form fields (any string value, capture if mentioned):
contact_name: contact person's name (at the primary company)
contact_title: their job title
contact_email: email address
contact_phone: phone number
company_name: the company/organization name
decision_maker: who makes the buying decision
competitors: other vendors they're considering (NOT partners!)
next_meeting: next meeting date/time (free text like "下週三" is fine)
timeline: when they want to start or deadline
notes: any other important context worth remembering

Partner/collaborator fields (when a SEPARATE partner company is mentioned):
partner_name: partner/collaborator company name
partner_contact_name: contact at the partner company
partner_contact_title: partner contact's job title
partner_contact_email: partner contact's email
partner_contact_phone: partner contact's phone

Subsidy fields (when role is "subsidy"):
subsidy_name: official program name
agency: issuing government agency
funding_amount: subsidy amount description
deadline: application deadline (free text)
eligibility: who can apply
scope: what the program covers

Deal potential field:
deal_potential: "high" | "medium" | "low" | "none"
  - "high" = clear need + budget + timeline, ready to create a deal
  - "medium" = has interest but unclear budget/timeline
  - "low" = exploratory, no concrete plan
  - "none" = no deal potential (info only)
  If deal_potential is missing and role is "client", proactively ask:
  「這個案子有開案的可能性嗎？（高/中/低/無）」
"""


# ---------------------------------------------------------------------------
# Field definitions per role (for missing-field detection)
# ---------------------------------------------------------------------------

_ROLE_FIELDS: dict[str, list[str]] = {
    "client": ["industry", "pain_points", "nda_status", "mou_status", "budget", "deal_potential"],
    "partner": ["capabilities", "team_size"],
    "subsidy": ["subsidy_name", "agency", "funding_amount", "deadline", "subsidy_partner", "subsidy_deadline"],
    "si": [],
    "other": [],
}


def _missing_fields(parsed: dict) -> list[str]:
    """Return field names that are still missing based on role."""
    role = parsed.get("role")
    if not role:
        return ["role"]
    expected = _ROLE_FIELDS.get(role, [])
    return [f for f in expected if f not in parsed]


# ---------------------------------------------------------------------------
# Telegram Bot API helpers
# ---------------------------------------------------------------------------

def _bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    return token


def _webhook_secret() -> str:
    return os.getenv("TELEGRAM_WEBHOOK_SECRET", "")


async def _tg_api(method: str, **kwargs) -> dict:
    """Call Telegram Bot API."""
    url = f"https://api.telegram.org/bot{_bot_token()}/{method}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=kwargs)
        resp.raise_for_status()
        return resp.json()


async def _tg_get_file(file_id: str) -> tuple[str, bytes]:
    """Download a file from Telegram. Returns (file_path, content)."""
    info = await _tg_api("getFile", file_id=file_id)
    file_path = info["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{_bot_token()}/{file_path}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return file_path, resp.content


async def _send_reply(chat_id: int, text: str):
    await _tg_api("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML")


# ---------------------------------------------------------------------------
# AI helpers
# ---------------------------------------------------------------------------

def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences from AI response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
    return text.strip()


BUSINESS_CARD_PROMPT = """\
You are an OCR and business card parser for a B2B sales assistant.
Analyze the image of a business card and extract all visible information.

Return ONLY a JSON object. Do NOT wrap in markdown code fences.
Omit any field you cannot read clearly — never guess.

Extract these fields:
contact_name: person's full name (use original language, e.g. Chinese characters)
contact_title: job title / position
contact_email: email address
contact_phone: phone number(s) — if multiple, use the mobile one
contact_fax: fax number (if any)
company_name: company / organization name (full official name)
company_address: office address
company_website: website URL
line_id: LINE ID (if printed on card)
department: department name
notes: any other text on the card worth noting (e.g. certifications, slogan)

Also infer these if possible from the company/role context:
industry: best-fit from "food" | "petrochemical" | "semiconductor" | "manufacturing" | "tech" | "finance" | "healthcare" | "transportation" | "other"
  If none fit, suggest a snake_case key + add "industry_label" with Chinese name.

Do NOT include "role" — the user will classify this contact as client or partner later.

Example output:
{"contact_name":"王大明","contact_title":"業務經理","company_name":"台灣積體電路製造股份有限公司","contact_phone":"0912-345-678","contact_email":"dm.wang@tsmc.com","industry":"semiconductor"}
"""


async def _auto_parse(raw_input: str) -> dict | None:
    """Initial parse — extract structured fields from first message."""
    available, info = check_ai_available()
    if not available:
        logger.warning("AI not available for auto-parse: %s", info)
        return None
    try:
        response = await asyncio.to_thread(
            generate_ai_response, INTEL_PARSE_PROMPT, raw_input
        )
        return json.loads(_strip_json_fences(response))
    except Exception as e:
        logger.error("AI parse failed: %s", e)
        return None


async def _parse_business_card(image_bytes: bytes, caption: str = "") -> list[dict]:
    """Parse business card image(s) using vision AI. Always returns a list of card dicts."""
    available, info = check_ai_available()
    if not available:
        logger.warning("AI not available for business card parse: %s", info)
        return []
    try:
        user_text = caption or "請辨識這張圖片中所有名片的資訊，每張名片各自回傳一個 JSON object"
        response = await asyncio.to_thread(
            generate_ai_vision_response,
            BUSINESS_CARD_PROMPT + "\n\nIMPORTANT: If the image contains MULTIPLE business cards, return a JSON ARRAY of objects, one per card. If only one card, still return a single JSON object (not an array).",
            user_text,
            image_bytes,
            "image/jpeg",
        )
        result = json.loads(_strip_json_fences(response))
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
        return []
    except Exception as e:
        logger.error("Business card parse failed: %s", e)
        return []


async def _followup_parse(current_parsed: dict, user_msg: str) -> tuple[str, dict]:
    """Follow-up parse — returns (reply_text, new_fields)."""
    available, info = check_ai_available()
    if not available:
        return "⚠️ AI 暫時不可用，請稍後再試", {}

    prompt = FOLLOWUP_PROMPT.format(
        current_json=json.dumps(current_parsed, ensure_ascii=False, indent=2),
        user_msg=user_msg,
    )
    try:
        response = await asyncio.to_thread(
            generate_ai_response,
            "You are a helpful B2B sales assistant.",
            prompt,
        )
        # Split by ---
        if "---" in response:
            reply_part, json_part = response.split("---", 1)
            reply_text = reply_part.strip()
            new_fields = json.loads(_strip_json_fences(json_part))
        else:
            # AI didn't follow format — treat whole thing as reply
            reply_text = response.strip()
            new_fields = {}
        return reply_text, new_fields
    except json.JSONDecodeError:
        # Got reply but JSON part was bad — still return the reply
        return reply_part.strip() if "---" in response else response.strip(), {}
    except Exception as e:
        logger.error("Follow-up parse failed: %s", e)
        return f"⚠️ 解析失敗：{e}", {}


# ---------------------------------------------------------------------------
# Label maps & formatters
# ---------------------------------------------------------------------------

_ROLE_LABELS = {
    "client": "客戶", "partner": "夥伴", "subsidy": "政府補貼",
    "si": "SI", "other": "其他",
}
_KNOWN_INDUSTRIES = {
    "food", "petrochemical", "semiconductor", "manufacturing",
    "tech", "finance", "healthcare", "transportation", "other",
}
_INDUSTRY_LABELS = {
    "food": "食品業", "petrochemical": "石化業", "semiconductor": "半導體",
    "manufacturing": "製造業", "tech": "科技", "finance": "金融",
    "healthcare": "醫療", "transportation": "交通運輸", "other": "其他",
}
# Custom industries added at runtime (persists until server restart)
_custom_industries: dict[str, str] = {}  # { snake_key: "中文 label" }
_PAIN_LABELS = {
    "automation": "產線自動化", "aoi": "AOI", "energy": "能源管理",
    "safety": "安全監控", "erp": "ERP/系統整合", "iot": "IoT",
}
_FIELD_LABELS = {
    "role": "分類", "industry": "產業", "pain_points": "痛點",
    "nda_status": "NDA", "mou_status": "MOU", "budget": "預算",
    "deal_potential": "開案潛力",
    "capabilities": "能力", "team_size": "團隊規模",
    "subsidy_name": "計畫名稱", "agency": "主辦機關", "funding_amount": "補助額度",
    "deadline": "截止日期", "eligibility": "申請資格", "scope": "補助範疇",
    "subsidy_partner": "合作夥伴", "subsidy_deadline": "截止期程",
}


def _get_industry_label(key: str) -> str:
    """Get display label for an industry key (known or custom)."""
    return _INDUSTRY_LABELS.get(key) or _custom_industries.get(key) or key


def _check_new_industry(parsed: dict) -> str | None:
    """If parsed contains an unknown industry, return a confirmation prompt. Also registers the label."""
    ind = parsed.get("industry")
    if not ind or ind in _KNOWN_INDUSTRIES or ind in _custom_industries:
        return None
    # AI suggested a new industry
    label = parsed.pop("industry_label", None) or ind
    _custom_industries[ind] = label
    return f'🆕 偵測到新產業分類：「{label}」（{ind}）\n要使用這個分類嗎？回覆「是」確認，或告訴我正確的產業'


def _format_summary(parsed: dict) -> str:
    """One-line summary of parsed fields."""
    parts = []
    if role := parsed.get("role"):
        parts.append(_ROLE_LABELS.get(role, role))
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
        parts.append(_get_industry_label(ind))
    if pains := parsed.get("pain_points"):
        labels = [_PAIN_LABELS.get(p, p) for p in pains]
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


def _format_initial_reply(intel_id: int, parsed: dict | None, has_missing: bool) -> str:
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
        f"📋 {_format_summary(parsed)}",
    ]
    if has_missing:
        missing = _missing_fields(parsed)
        missing_labels = [_FIELD_LABELS.get(f, f) for f in missing[:3]]
        lines.append("")
        lines.append(f"還缺少：{' / '.join(missing_labels)}")
        lines.append("直接回覆補充，或輸入 /done 結束")
    else:
        lines.append("")
        lines.append("資訊已很完整！輸入 /done 確認，或繼續補充")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Save file helper
# ---------------------------------------------------------------------------

async def _save_attachment(
    file_id: str, file_name: str | None, intel_id: int
) -> None:
    """Download file from Telegram and save to uploads/ + DB."""
    tg_path, content = await _tg_get_file(file_id)
    name = file_name or Path(tg_path).name
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    local_path = UPLOADS_DIR / f"{intel_id}_{name}"
    local_path.write_bytes(content)

    await asyncio.to_thread(
        create_file,
        intel_id=intel_id,
        file_type="attachment",
        file_name=name,
        file_path=str(local_path),
        file_size=len(content),
    )
    logger.info("Saved attachment %s for intel #%d", name, intel_id)


# ---------------------------------------------------------------------------
# Conversation handlers
# ---------------------------------------------------------------------------

async def _auto_create_deal(
    intel_id: int, client_id: int, client_name: str, parsed: dict
) -> dict | None:
    """Auto-create a deal from parsed intel. Returns deal dict or None."""
    from services.nexus.deals import create_deal

    pains = parsed.get("pain_points", [])
    pain_labels = [_PAIN_LABELS.get(p, p) for p in pains[:2]] if pains else []
    deal_name = client_name
    if pain_labels:
        deal_name += f" — {'、'.join(pain_labels)}"

    budget_amount = None
    budget_range = None
    if parsed.get("budget"):
        try:
            budget_amount = float(parsed["budget"])
            if budget_amount < 100_000:
                budget_range = "<100K"
            elif budget_amount < 500_000:
                budget_range = "100-500K"
            elif budget_amount < 1_000_000:
                budget_range = "500K-1M"
            else:
                budget_range = "1M+"
        except (ValueError, TypeError):
            pass

    try:
        deal = await asyncio.to_thread(
            create_deal,
            name=deal_name,
            client_id=client_id,
            budget_range=budget_range,
            budget_amount=budget_amount,
        )
        await asyncio.to_thread(link_intel_to_deal, deal["id"], intel_id)
        return {"id": deal["id"], "name": deal_name}
    except Exception as e:
        logger.error("Auto-create deal failed: %s", e)
        return None


async def _handle_done(chat_id: int) -> None:
    """Finalize the active conversation."""
    from services.nexus.materialize import materialize_intel

    conv = _conversations.pop(chat_id, None)
    if not conv:
        await _send_reply(chat_id, "目前沒有進行中的情報，傳訊息開始新的紀錄！")
        return

    intel_id = conv["intel_id"]
    parsed = conv["parsed"]

    # Re-merge card_base to ensure OCR fields are never lost
    for k, v in conv.get("card_base", {}).items():
        if k not in parsed:
            parsed[k] = v

    parsed_json = json.dumps(parsed, ensure_ascii=False) if parsed else None

    await asyncio.to_thread(confirm_intel, intel_id, parsed_json)

    # Auto-materialize entities
    mat_result = await asyncio.to_thread(materialize_intel, intel_id)

    lines = [
        f"✅ 情報 #{intel_id} 已確認！",
        f"📋 {_format_summary(parsed)}" if parsed else "",
    ]
    # Append materialization results
    if mat_result.get("client"):
        c = mat_result["client"]
        action_label = "已建立" if c["action"] == "created" else "已匹配"
        lines.append(f"🔗 {action_label}客戶「{c['name']}」")
    if mat_result.get("partner"):
        p = mat_result["partner"]
        action_label = "已建立" if p["action"] == "created" else "已匹配"
        lines.append(f"🤝 {action_label}夥伴「{p['name']}」")
    if mat_result.get("subsidy"):
        s = mat_result["subsidy"]
        action_label = "已建立" if s["action"] == "created" else "已匹配"
        lines.append(f"📋 {action_label}補助案「{s['name']}」")
    for c in mat_result.get("contacts", []):
        action_label = "已建立" if c["action"] == "created" else "已匹配"
        lines.append(f"👤 {action_label}聯絡人「{c['name']}」")
    if mat_result.get("fields_indexed", 0) > 0:
        lines.append(f"📊 已索引 {mat_result['fields_indexed']} 個欄位")

    # Auto-link to existing deals + deal creation logic
    client_info = mat_result.get("client")
    partner_info = mat_result.get("partner")
    role = parsed.get("role")

    # Find and auto-link existing deals for matched client or partner
    existing_deals = []
    if client_info:
        existing_deals = await asyncio.to_thread(get_deals_by_client, client_info["id"])
    if existing_deals:
        for d in existing_deals:
            try:
                await asyncio.to_thread(link_intel_to_deal, d["id"], intel_id)
            except Exception:
                pass  # may already be linked
        deal_names = "、".join(f"「{d['name']}」" for d in existing_deals[:3])
        suffix = f"等 {len(existing_deals)} 筆" if len(existing_deals) > 3 else ""
        lines.append(f"🔗 已自動關聯商機：{deal_names}{suffix}")

    # Deal creation based on deal_potential (client role only)
    if role == "client" and client_info:
        dp = parsed.get("deal_potential", "")

        if dp in ("high", "medium"):
            deal_result = await _auto_create_deal(
                intel_id=intel_id,
                client_id=client_info["id"],
                client_name=client_info["name"],
                parsed=parsed,
            )
            if deal_result:
                lines.append(
                    f"💼 已自動建立商機「{deal_result['name']}」(#{deal_result['id']})"
                )
                lines.append(f"   階段：L0 | 開案潛力：{'高' if dp == 'high' else '中'}")
        elif dp == "low":
            _pending_deal[chat_id] = {
                "intel_id": intel_id,
                "client_id": client_info["id"],
                "client_name": client_info["name"],
                "parsed": parsed,
            }
            lines.append("")
            lines.append(f"💼 開案潛力偏低，仍要為「{client_info['name']}」建立新商機嗎？")
            lines.append("回覆「是」建立，或傳新訊息開始下一筆情報")
        elif dp != "none":
            _pending_deal[chat_id] = {
                "intel_id": intel_id,
                "client_id": client_info["id"],
                "client_name": client_info["name"],
                "parsed": parsed,
            }
            if not existing_deals:
                lines.append("")
                lines.append(f"💼 要為「{client_info['name']}」建立商機嗎？")
                lines.append("回覆「是」建立，或傳新訊息開始下一筆情報")
            else:
                lines.append("")
                lines.append("💼 要另外建立新商機嗎？回覆「是」建立，或傳新訊息開始下一筆")
        else:
            lines.append("")
            lines.append("傳新訊息可開始下一筆情報")
    else:
        lines.append("")
        lines.append("傳新訊息可開始下一筆情報")

    await _send_reply(chat_id, "\n".join(l for l in lines if l or l == ""))


async def _handle_deal_response(chat_id: int, text: str) -> bool:
    """Handle response to deal creation prompt. Returns True if handled."""
    pending = _pending_deal.get(chat_id)
    if not pending:
        return False

    low = text.lower().strip()
    if low in ("是", "yes", "ok", "好", "建立", "對"):
        result = await _auto_create_deal(
            intel_id=pending["intel_id"],
            client_id=pending["client_id"],
            client_name=pending["client_name"],
            parsed=pending["parsed"],
        )
        _pending_deal.pop(chat_id, None)
        if result:
            await _send_reply(
                chat_id,
                f"💼 已建立商機「{result['name']}」(#{result['id']})\n"
                f"階段：L0 | 客戶：{pending['client_name']}\n\n"
                f"傳新訊息可開始下一筆情報",
            )
        else:
            await _send_reply(chat_id, "⚠️ 建立商機失敗，請稍後重試\n傳新訊息可開始下一筆情報")
        return True

    elif low in ("否", "no", "不", "不用", "跳過", "skip"):
        _pending_deal.pop(chat_id, None)
        await _send_reply(chat_id, "好的，跳過建立商機。\n傳新訊息可開始下一筆情報")
        return True

    # Not a yes/no answer — clear pending and let it fall through as new intel
    return False


async def _handle_cancel(chat_id: int) -> None:
    """Cancel the active conversation (keep as draft)."""
    conv = _conversations.pop(chat_id, None)
    if not conv:
        await _send_reply(chat_id, "目前沒有進行中的情報")
        return
    await _send_reply(chat_id, f"已取消。情報 #{conv['intel_id']} 保留為草稿")


async def _handle_status(chat_id: int) -> None:
    """Show current conversation status."""
    conv = _conversations.get(chat_id)
    if not conv:
        await _send_reply(chat_id, "目前沒有進行中的情報，傳訊息開始新的紀錄！")
        return

    parsed = conv["parsed"]
    missing = _missing_fields(parsed)
    missing_labels = [_FIELD_LABELS.get(f, f) for f in missing]

    lines = [
        f"📝 情報 #{conv['intel_id']} 進行中",
        f"📋 {_format_summary(parsed)}",
    ]
    if missing_labels:
        lines.append(f"❓ 還缺少：{' / '.join(missing_labels)}")
    else:
        lines.append("✅ 資訊已完整，輸入 /done 確認")
    await _send_reply(chat_id, "\n".join(lines))


def _format_card_raw(card: dict) -> str:
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


async def _handle_new_intel(chat_id: int, text: str, message: dict) -> None:
    """Create a new intel and start conversation."""
    # Create intel
    has_photo = bool(message.get("photo"))
    input_type = "photo" if has_photo else "text"
    raw = text or ("(名片/照片)" if has_photo else "(file)")

    intel = await asyncio.to_thread(create_intel, raw_input=raw, input_type=input_type)
    intel_id = intel["id"]

    # Handle attachments + vision parse for photos
    image_bytes: bytes | None = None
    if photos := message.get("photo"):
        file_id = photos[-1]["file_id"]
        await _save_attachment(file_id, None, intel_id)
        # Download image for vision parsing
        try:
            _, image_bytes = await _tg_get_file(file_id)
        except Exception as e:
            logger.error("Failed to download photo for vision: %s", e)
    elif doc := message.get("document"):
        await _save_attachment(doc["file_id"], doc.get("file_name"), intel_id)

    # AI initial parse — use vision for photos, text parse for text
    parsed: dict = {}
    if image_bytes:
        await _send_reply(chat_id, "🔍 正在辨識圖片...")
        cards = await _parse_business_card(image_bytes, text or "")

        if len(cards) > 1:
            # Multiple business cards — create separate intel for each extra card
            raw_parts = []
            for i, card in enumerate(cards):
                card_label = _format_card_raw(card)
                raw_parts.append(f"--- 名片 {i+1} ---\n{card_label}")

            raw = "📇 名片辨識（共 {} 張）\n\n{}".format(len(cards), "\n\n".join(raw_parts))
            await asyncio.to_thread(update_intel, intel_id, raw_input=raw)

            # First card goes to current intel
            parsed = cards[0]

            # Create separate intel for remaining cards
            extra_lines = []
            for card in cards[1:]:
                card_raw = "📇 名片辨識\n" + _format_card_raw(card)
                extra_intel = await asyncio.to_thread(
                    create_intel, raw_input=card_raw, input_type="photo"
                )
                await asyncio.to_thread(
                    update_intel, extra_intel["id"],
                    parsed_json=json.dumps(card, ensure_ascii=False),
                )
                name = card.get("contact_name", "?")
                company = card.get("company_name", "")
                extra_lines.append(f"  #{extra_intel['id']} {name}" + (f"（{company}）" if company else ""))
            await _send_reply(
                chat_id,
                f"📇 偵測到 {len(cards)} 張名片！\n"
                f"其他 {len(cards)-1} 張已存為草稿：\n" + "\n".join(extra_lines) +
                "\n\n先處理第 1 張，其他可之後用 /done 逐一確認"
            )

        elif len(cards) == 1:
            parsed = cards[0]
            raw = "📇 名片辨識\n" + _format_card_raw(parsed)
            await asyncio.to_thread(update_intel, intel_id, raw_input=raw)
            logger.info("Card parse result for intel #%d: %s", intel_id, json.dumps(parsed, ensure_ascii=False))

    elif text:
        parsed = await _auto_parse(text) or {}

    # Save to DB (as draft with partial parsed_json)
    if parsed:
        await asyncio.to_thread(
            update_intel, intel_id,
            parsed_json=json.dumps(parsed, ensure_ascii=False),
        )

    # Check for new industry suggestion
    industry_prompt = _check_new_industry(parsed) if parsed else None

    # Detect if this was a business card (has contact_name but no role)
    is_card = bool(parsed.get("contact_name") and not parsed.get("role"))

    # Start conversation
    # Save card-parsed fields separately so they can never be lost by followup AI
    card_base = dict(parsed) if is_card else {}

    _conversations[chat_id] = {
        "intel_id": intel_id,
        "parsed": parsed,
        "card_base": card_base,  # immutable card OCR fields
        "raw_history": [raw] if text else [],
        "pending_industry_confirm": bool(industry_prompt),
        "pending_role_confirm": is_card,
    }

    if is_card:
        # Business card flow: show parsed info and ask role first
        reply = (
            f"📇 名片辨識完成！情報 #{intel_id}\n"
            f"📋 {_format_summary(parsed)}\n\n"
            f"這位是「客戶」還是「夥伴」？\n"
            f"回覆：客戶 / 夥伴 / 其他"
        )
    else:
        has_missing = bool(_missing_fields(parsed))
        reply = _format_initial_reply(intel_id, parsed if parsed else None, has_missing)
    if industry_prompt:
        reply += "\n\n" + industry_prompt
    await _send_reply(chat_id, reply)


async def _handle_followup(chat_id: int, text: str) -> None:
    """Process a follow-up message in an active conversation."""
    conv = _conversations[chat_id]
    intel_id = conv["intel_id"]

    # --- Handle pending role confirmation (business card flow) ---
    if conv.get("pending_role_confirm"):
        low = text.strip().lower()
        role_map = {
            "客戶": "client", "client": "client",
            "夥伴": "partner", "partner": "partner", "合作夥伴": "partner",
            "其他": "other", "other": "other",
            "si": "si", "補助": "subsidy", "subsidy": "subsidy",
        }
        matched_role = role_map.get(low)
        if matched_role:
            conv["parsed"]["role"] = matched_role
            conv["pending_role_confirm"] = False
            await asyncio.to_thread(
                update_intel, intel_id,
                parsed_json=json.dumps(conv["parsed"], ensure_ascii=False),
            )
            role_label = _ROLE_LABELS.get(matched_role, matched_role)
            missing = _missing_fields(conv["parsed"])
            missing_labels = [_FIELD_LABELS.get(f, f) for f in missing[:3]]
            reply = f"✅ 已設定為「{role_label}」\n📋 {_format_summary(conv['parsed'])}"
            if missing_labels:
                reply += f"\n\n還缺少：{' / '.join(missing_labels)}\n繼續補充或輸入 /done 結束"
            else:
                reply += "\n\n資訊已很完整！輸入 /done 確認，或繼續補充"
            await _send_reply(chat_id, reply)
            return
        else:
            # Not a recognized role — remind user
            await _send_reply(chat_id, "請回覆：客戶 / 夥伴 / 其他")
            return

    # --- Handle pending industry confirmation ---
    if conv.get("pending_industry_confirm"):
        low = text.lower().strip()
        current_ind = conv["parsed"].get("industry", "")
        if low in ("是", "yes", "ok", "確認", "對"):
            # Confirmed — keep the industry as-is
            conv["pending_industry_confirm"] = False
            await asyncio.to_thread(
                update_intel, intel_id,
                parsed_json=json.dumps(conv["parsed"], ensure_ascii=False),
            )
            await _send_reply(
                chat_id,
                f"✅ 已確認產業：{_get_industry_label(current_ind)}\n\n"
                f"📋 目前：{_format_summary(conv['parsed'])}\n"
                f"繼續補充或輸入 /done 結束",
            )
            return
        elif low in ("否", "no", "不是", "不對"):
            # Rejected — remove industry, ask again
            conv["parsed"].pop("industry", None)
            _custom_industries.pop(current_ind, None)
            conv["pending_industry_confirm"] = False
            await _send_reply(chat_id, "好的，請告訴我正確的產業是什麼？")
            return
        else:
            # Treat as a new industry name from user
            new_key = text.strip().lower().replace(" ", "_")
            _custom_industries[new_key] = text.strip()
            conv["parsed"]["industry"] = new_key
            conv["pending_industry_confirm"] = False
            await asyncio.to_thread(
                update_intel, intel_id,
                parsed_json=json.dumps(conv["parsed"], ensure_ascii=False),
            )
            await _send_reply(
                chat_id,
                f"✅ 已設定產業：{text.strip()}（{new_key}）\n\n"
                f"📋 目前：{_format_summary(conv['parsed'])}\n"
                f"繼續補充或輸入 /done 結束",
            )
            return

    conv["raw_history"].append(text)

    # Append to raw_input in DB
    full_raw = "\n---\n".join(conv["raw_history"])
    await asyncio.to_thread(update_intel, intel_id, raw_input=full_raw)

    # AI follow-up parse
    reply_text, new_fields = await _followup_parse(conv["parsed"], text)

    # Merge new fields
    if new_fields:
        for k, v in new_fields.items():
            conv["parsed"][k] = v

    # Re-merge card_base fields (never lose OCR-extracted data)
    card_base = conv.get("card_base", {})
    for k, v in card_base.items():
        if k not in conv["parsed"]:
            conv["parsed"][k] = v

    if new_fields or card_base:
        # Update DB
        await asyncio.to_thread(
            update_intel, intel_id,
            parsed_json=json.dumps(conv["parsed"], ensure_ascii=False),
        )

    # Check for new industry from follow-up
    industry_prompt = _check_new_industry(conv["parsed"])
    if industry_prompt:
        conv["pending_industry_confirm"] = True

    # Build reply
    lines = [reply_text]
    if conv["parsed"]:
        lines.append(f"\n📋 目前：{_format_summary(conv['parsed'])}")
    if industry_prompt:
        lines.append("\n" + industry_prompt)
    await _send_reply(chat_id, "\n".join(lines))


# ---------------------------------------------------------------------------
# Daily digest
# ---------------------------------------------------------------------------

async def _handle_today(chat_id: int) -> None:
    """Send daily digest to chat."""
    from services.nexus.daily_digest import build_daily_digest, format_digest_telegram

    data = await asyncio.to_thread(build_daily_digest)
    text = format_digest_telegram(data)
    await _send_reply(chat_id, text)


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
):
    # Verify secret
    secret = _webhook_secret()
    if secret and x_telegram_bot_api_secret_token != secret:
        raise HTTPException(status_code=403, detail="Invalid secret token")

    body = await request.json()
    message = body.get("message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = (message.get("text") or message.get("caption") or "").strip()

    try:
        # --- Commands ---
        if text.startswith("/"):
            cmd = text.split()[0].lower()
            if cmd in ("/done", "/確認"):
                await _handle_done(chat_id)
            elif cmd in ("/cancel", "/取消"):
                await _handle_cancel(chat_id)
            elif cmd in ("/status", "/狀態"):
                await _handle_status(chat_id)
            elif cmd == "/start":
                await _send_reply(
                    chat_id,
                    "👋 你好！我是你的情報助理。\n\n"
                    "直接傳訊息、照片或檔案給我，我會幫你建立情報並自動分類。\n\n"
                    "指令：\n"
                    "/done — 確認並儲存情報\n"
                    "/cancel — 取消目前情報\n"
                    "/status — 查看目前進度\n"
                    "/new — 強制開始新情報\n"
                    "/today — 今日待辦摘要\n"
                    "/register — 啟用每日自動推送\n"
                    "/unregister — 關閉自動推送",
                )
            elif cmd in ("/today", "/待辦"):
                await _handle_today(chat_id)
            elif cmd == "/register":
                _registered_chats.add(chat_id)
                _save_registered_chats(_registered_chats)
                await _send_reply(chat_id, f"✅ 已註冊每日推送 (chat_id: {chat_id})")
            elif cmd == "/unregister":
                _registered_chats.discard(chat_id)
                _save_registered_chats(_registered_chats)
                await _send_reply(chat_id, "已取消每日推送")
            elif cmd == "/new":
                # Force start new (abandon current if any)
                _conversations.pop(chat_id, None)
                _pending_deal.pop(chat_id, None)
                await _send_reply(chat_id, "好的，傳訊息開始新的情報！")
            else:
                await _send_reply(chat_id, "未知指令。可用：/done /cancel /status /new /today /register")
            return {"ok": True}

        # --- Pending deal creation prompt ---
        if chat_id in _pending_deal and text:
            handled = await _handle_deal_response(chat_id, text)
            if handled:
                return {"ok": True}
            # Not a yes/no → clear pending, fall through to new intel
            _pending_deal.pop(chat_id, None)

        # --- Active conversation: follow-up ---
        if chat_id in _conversations:
            if text:
                await _handle_followup(chat_id, text)
            elif message.get("photo") or message.get("document"):
                # Attachment in follow-up — save to existing intel
                conv = _conversations[chat_id]
                intel_id = conv["intel_id"]
                if photos := message.get("photo"):
                    await _save_attachment(photos[-1]["file_id"], None, intel_id)
                elif doc := message.get("document"):
                    await _save_attachment(doc["file_id"], doc.get("file_name"), intel_id)
                await _send_reply(chat_id, f"📎 檔案已加到情報 #{intel_id}")
            return {"ok": True}

        # --- No active conversation: start new ---
        if text or message.get("photo") or message.get("document"):
            await _handle_new_intel(chat_id, text, message)
        else:
            await _send_reply(chat_id, "⚠️ 不支援的訊息類型，請傳文字、照片或檔案")

    except Exception as e:
        logger.exception("Telegram webhook processing error")
        await _send_reply(chat_id, f"❌ 處理失敗：{e}")

    return {"ok": True}


# ---------------------------------------------------------------------------
# Management endpoints
# ---------------------------------------------------------------------------

@router.get("/webhook/info")
async def webhook_info():
    """Query current webhook status from Telegram."""
    result = await _tg_api("getWebhookInfo")
    return result.get("result", result)


@router.post("/webhook/setup")
async def webhook_setup(webhook_url: str = Query(...)):
    """Register webhook URL with Telegram."""
    params: dict = {"url": webhook_url}
    secret = _webhook_secret()
    if secret:
        params["secret_token"] = secret
    result = await _tg_api("setWebhook", **params)
    return result


@router.post("/daily-digest")
async def send_daily_digest(chat_id: int | None = Query(None)):
    """Send daily digest. Called by cron or manually.

    - With chat_id param: send to that specific chat
    - Without: broadcast to all /register'ed chats
    """
    from services.nexus.daily_digest import build_daily_digest, format_digest_telegram

    data = await asyncio.to_thread(build_daily_digest)
    text = format_digest_telegram(data)

    targets: list[int] = []
    if chat_id:
        targets = [chat_id]
    else:
        targets = sorted(_registered_chats)

    if not targets:
        raise HTTPException(400, "No targets: pass chat_id or /register in Telegram first")

    for t in targets:
        await _send_reply(t, text)

    return {"ok": True, "date": data["date"], "sent_to": targets}
