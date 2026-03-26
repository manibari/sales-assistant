"""Centralized prompt registry for Nexus sales assistant.

All AI prompts are defined in this package and re-exported here
for easy import: `from services.nexus.prompts import INTEL_PARSE_PROMPT`
"""

from services.nexus.prompts.intel_parse import INTEL_PARSE_PROMPT
from services.nexus.prompts.followup import FOLLOWUP_PROMPT
from services.nexus.prompts.business_card import BUSINESS_CARD_PROMPT
from services.nexus.prompts.summarize import INTEL_SUMMARIZE_PROMPT
from services.nexus.prompts.meddic import MEDDIC_AI_PROMPT
from services.nexus.prompts.tender_analyze import TENDER_ANALYZE_PROMPT
from services.nexus.prompts.tender_chat import TENDER_CHAT_PROMPT
from services.nexus.prompts.tender_generate import TENDER_GENERATE_PROMPT
from services.nexus.prompts.pitch import PITCH_SYSTEM_PROMPT
from services.nexus.prompts.visit_plan import VISIT_PLAN_SYSTEM_PROMPT
from services.nexus.prompts.knowledge_extract import KNOWLEDGE_SUMMARIZE_PROMPT

__all__ = [
    "INTEL_PARSE_PROMPT",
    "FOLLOWUP_PROMPT",
    "BUSINESS_CARD_PROMPT",
    "INTEL_SUMMARIZE_PROMPT",
    "MEDDIC_AI_PROMPT",
    "TENDER_ANALYZE_PROMPT",
    "TENDER_CHAT_PROMPT",
    "TENDER_GENERATE_PROMPT",
    "PITCH_SYSTEM_PROMPT",
    "VISIT_PLAN_SYSTEM_PROMPT",
    "KNOWLEDGE_SUMMARIZE_PROMPT",
]
