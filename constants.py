"""SPMS constants — status codes, action types, task statuses, and state machine transitions."""

# Pre-sale status codes (L0-L7)
PRESALE_STATUS_CODES = {
    "L0": "客戶開發",
    "L1": "等待追蹤",
    "L2": "提案",
    "L3": "確認意願",
    "L4": "執行 POC",
    "L5": "完成 POC",
    "L6": "議價",
    "L7": "簽約",
}

# Post-sale status codes (P0-P2)
POSTSALE_STATUS_CODES = {
    "P0": "規劃",
    "P1": "執行",
    "P2": "驗收",
}

# All status codes (including special states)
STATUS_CODES = {
    **PRESALE_STATUS_CODES,
    **POSTSALE_STATUS_CODES,
    "LOST": "遺失",
    "HOLD": "擱置",
}

# Project task statuses
TASK_STATUSES = {
    "planned": "規劃中",
    "in_progress": "進行中",
    "completed": "已完成",
}

# Work log action types
ACTION_TYPES = ["會議", "提案", "開發", "文件", "郵件"]

# Statuses excluded from work log project selector
INACTIVE_STATUSES = {"L7", "P2", "LOST", "HOLD"}

# Pre-sale transitions
PRESALE_TRANSITIONS = {
    "L0": ["L1", "LOST", "HOLD"],
    "L1": ["L2", "LOST", "HOLD"],
    "L2": ["L3", "LOST", "HOLD"],
    "L3": ["L4", "LOST", "HOLD"],
    "L4": ["L5", "LOST", "HOLD"],
    "L5": ["L6", "LOST", "HOLD"],
    "L6": ["L7", "LOST", "HOLD"],
    "L7": ["P0"],  # Auto-transition to post-sale P0
}

# Post-sale transitions
POSTSALE_TRANSITIONS = {
    "P0": ["P1"],
    "P1": ["P2"],
    "P2": [],      # Post-sale terminal
}

# All valid transitions (for transition_status)
VALID_TRANSITIONS = {
    **PRESALE_TRANSITIONS,
    **POSTSALE_TRANSITIONS,
    "LOST": [],
    "HOLD": [],
}
