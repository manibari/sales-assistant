"""SPMS constants — status codes, action types, and state machine transitions."""

# Status codes: code -> display name
STATUS_CODES = {
    "S01": "開發",
    "S02": "追蹤",
    "S03": "提案",
    "S04": "立案",
    "T01": "POC 執行",
    "T02": "POC 完成",
    "C01": "議價",
    "C02": "條款",
    "C03": "審查",
    "C04": "簽約",
    "D01": "規劃",
    "D02": "開發",
    "D03": "驗收",
    "LOST": "遺失",
    "HOLD": "擱置",
}

# Work log action types
ACTION_TYPES = ["會議", "提案", "開發", "文件", "郵件"]

# Statuses excluded from work log project selector
INACTIVE_STATUSES = {"D03", "LOST", "HOLD"}

# Valid state transitions: current_status -> list of allowed next statuses
VALID_TRANSITIONS = {
    "S01": ["S02", "LOST", "HOLD"],
    "S02": ["S03", "LOST", "HOLD"],
    "S03": ["S04", "LOST", "HOLD"],
    "S04": ["T01", "C01", "LOST", "HOLD"],
    "T01": ["T02", "LOST", "HOLD"],
    "T02": ["C01", "LOST", "HOLD"],
    "C01": ["C02", "LOST", "HOLD"],
    "C02": ["C03", "LOST", "HOLD"],
    "C03": ["C04", "LOST", "HOLD"],
    "C04": ["D01"],
    "D01": ["D02"],
    "D02": ["D03"],
    "D03": [],
    "LOST": [],
    "HOLD": [],
}
