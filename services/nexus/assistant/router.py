"""Intent detection router — classify user input into an Intent."""

import re

from services.nexus.assistant.intents import Intent


# ---------------------------------------------------------------------------
# Keyword patterns (compiled once)
# ---------------------------------------------------------------------------

# Query patterns — "查" "找" "看" "最近" "怎樣" "進度"
_QUERY_PATTERNS = re.compile(
    r"(?:^|\s)(查|找|看|搜尋|搜|列出)"
    r"|最近怎[樣麼]|進度|有什麼|有哪些",
    re.IGNORECASE,
)

# Client query — "查 <company>" or "<company> 最近怎樣"
_QUERY_CLIENT_PATTERNS = re.compile(
    r"(?:^|\s)(?:查|找|看)\s*\S{2,}"  # "查 美珍香"
    r"|(?:\S{2,})\s*(?:最近怎[樣麼]|的?狀況|的?情況)",
    re.IGNORECASE,
)

# Deal query
_QUERY_DEAL_PATTERNS = re.compile(
    r"案子|商機|deal|進度|pipeline",
    re.IGNORECASE,
)

# Tender query
_QUERY_TENDER_PATTERNS = re.compile(
    r"標案|tender|招標|投標",
    re.IGNORECASE,
)

# Subsidy query
_QUERY_SUBSIDY_PATTERNS = re.compile(
    r"補助|subsidy|SBIR|SIIR|計畫.*到期|快到期.*補助",
    re.IGNORECASE,
)

# Schedule query
_QUERY_SCHEDULE_PATTERNS = re.compile(
    r"行程|會議|agenda|schedule|今天|這週|本週|明天|行事曆",
    re.IGNORECASE,
)

# Action patterns — "建" "排" "提醒" "寫" "產生"
_ACTION_CREATE_DEAL_PATTERNS = re.compile(
    r"(?:幫|請)?.*(?:建|開|新增).*(?:案子|商機|deal)",
    re.IGNORECASE,
)

_ACTION_CREATE_MEETING_PATTERNS = re.compile(
    r"(?:排|安排|約|建).*(?:會議|開會|meeting)|(?:會議|開會).*(?:排|安排|約)",
    re.IGNORECASE,
)

_ACTION_CREATE_REMINDER_PATTERNS = re.compile(
    r"提醒|remind",
    re.IGNORECASE,
)

_ACTION_UPDATE_DEAL_PATTERNS = re.compile(
    r"(?:改|更新|調整).*(?:預算|金額|時程|階段|budget)",
    re.IGNORECASE,
)

_ACTION_GENERATE_PITCH_PATTERNS = re.compile(
    r"(?:寫|產生|生成|幫我寫).*(?:說帖|pitch|開發信|提案)",
    re.IGNORECASE,
)

# Capture patterns
_CAPTURE_VISIT_PATTERNS = re.compile(
    r"拜訪|現場|到訪|visit|site visit|出差|跑客戶",
    re.IGNORECASE,
)

_CAPTURE_MEETING_PATTERNS = re.compile(
    r"開會|會議|meeting|電話會|視訊會|con call|線上會",
    re.IGNORECASE,
)

_CAPTURE_SUBSIDY_PATTERNS = re.compile(
    r"補助|SBIR|SIIR|計畫|政府.*案|經濟部|工業局|中小企業",
    re.IGNORECASE,
)

_CAPTURE_LEAD_PATTERNS = re.compile(
    r"想[找做要]|需要|outsource|外包|客製化|需求|RFP|RFQ",
    re.IGNORECASE,
)


def detect_intent(
    text: str,
    input_type: str = "text",
    has_active_conversation: bool = False,
    parsed: dict | None = None,
) -> Intent:
    """Detect user intent from text and context.

    Priority:
    1. Active conversation → FOLLOWUP
    2. Photo input → CAPTURE_CARD
    3. Query keywords → QUERY_*
    4. Action keywords → ACTION_*
    5. Capture keywords → CAPTURE_*
    6. Default → CAPTURE_GENERAL
    """
    # 1. Active conversation — always followup
    if has_active_conversation:
        return Intent.FOLLOWUP

    # 2. Photo → business card
    if input_type == "photo":
        return Intent.CAPTURE_CARD

    if not text:
        return Intent.CAPTURE_GENERAL

    text_stripped = text.strip()

    # 3. Query detection (check before action — "查" takes priority)
    if _QUERY_PATTERNS.search(text_stripped):
        if _QUERY_TENDER_PATTERNS.search(text_stripped):
            return Intent.QUERY_TENDER
        if _QUERY_SUBSIDY_PATTERNS.search(text_stripped):
            return Intent.QUERY_SUBSIDY
        if _QUERY_SCHEDULE_PATTERNS.search(text_stripped):
            return Intent.QUERY_SCHEDULE
        if _QUERY_DEAL_PATTERNS.search(text_stripped):
            return Intent.QUERY_DEAL
        if _QUERY_CLIENT_PATTERNS.search(text_stripped):
            return Intent.QUERY_CLIENT
        return Intent.QUERY_GENERAL

    # Schedule query without explicit "查" — "今天有什麼行程"
    if _QUERY_SCHEDULE_PATTERNS.search(text_stripped):
        return Intent.QUERY_SCHEDULE

    # 4. Action detection
    if _ACTION_CREATE_MEETING_PATTERNS.search(text_stripped):
        return Intent.ACTION_CREATE_MEETING
    if _ACTION_CREATE_DEAL_PATTERNS.search(text_stripped):
        return Intent.ACTION_CREATE_DEAL
    if _ACTION_CREATE_REMINDER_PATTERNS.search(text_stripped):
        return Intent.ACTION_CREATE_REMINDER
    if _ACTION_UPDATE_DEAL_PATTERNS.search(text_stripped):
        return Intent.ACTION_UPDATE_DEAL
    if _ACTION_GENERATE_PITCH_PATTERNS.search(text_stripped):
        return Intent.ACTION_GENERATE_PITCH

    # 5. Capture detection (intel input)
    if _CAPTURE_SUBSIDY_PATTERNS.search(text_stripped):
        return Intent.CAPTURE_SUBSIDY
    if _CAPTURE_VISIT_PATTERNS.search(text_stripped):
        return Intent.CAPTURE_VISIT
    if _CAPTURE_MEETING_PATTERNS.search(text_stripped):
        return Intent.CAPTURE_MEETING
    if _CAPTURE_LEAD_PATTERNS.search(text_stripped):
        return Intent.CAPTURE_LEAD

    # 6. Default — treat as general intel capture
    return Intent.CAPTURE_GENERAL
