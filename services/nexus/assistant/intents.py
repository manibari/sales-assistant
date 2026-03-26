"""Intent definitions for the assistant engine."""

from enum import Enum


class Intent(Enum):
    """All possible user intents recognized by the assistant."""

    # === Capture (intel input) ===
    CAPTURE_VISIT = "capture_visit"          # "美珍香 現場 拜訪 3/26"
    CAPTURE_MEETING = "capture_meeting"      # "跟台積電開會 預算500萬"
    CAPTURE_LEAD = "capture_lead"            # "Sabre 想找外部團隊做客製化"
    CAPTURE_CARD = "capture_card"            # [photo] business card
    CAPTURE_SUBSIDY = "capture_subsidy"      # "SBIR 115年度"
    CAPTURE_GENERAL = "capture_general"      # unclassified intel

    # === Query ===
    QUERY_CLIENT = "query_client"            # "美珍香 最近怎樣" "查 台積電"
    QUERY_DEAL = "query_deal"               # "智瀚的案子進度"
    QUERY_TENDER = "query_tender"            # "最近有什麼標案"
    QUERY_SUBSIDY = "query_subsidy"          # "有什麼補助快到期"
    QUERY_SCHEDULE = "query_schedule"        # "今天有什麼行程" "這週的會議"
    QUERY_GENERAL = "query_general"          # general question

    # === Action ===
    ACTION_CREATE_DEAL = "action_create_deal"          # "幫美珍香建一個案子"
    ACTION_CREATE_MEETING = "action_create_meeting"    # "排 3/28 下午兩點開會"
    ACTION_CREATE_REMINDER = "action_create_reminder"  # "提醒我下週一聯絡王經理"
    ACTION_UPDATE_DEAL = "action_update_deal"          # "智瀚的案子預算改成200萬"
    ACTION_GENERATE_PITCH = "action_generate_pitch"    # "幫我寫一份美珍香的開發說帖"

    # === System ===
    COMMAND = "command"                      # /done, /cancel, /status, /today
    FOLLOWUP = "followup"                    # reply in active conversation

    @property
    def category(self) -> str:
        """Return the intent category: capture, query, action, or system."""
        name = self.value
        if name.startswith("capture_"):
            return "capture"
        if name.startswith("query_"):
            return "query"
        if name.startswith("action_"):
            return "action"
        return "system"
