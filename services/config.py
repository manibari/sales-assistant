"""Centralized config loader for external YAML files (rules, prompts).

Uses functools.lru_cache so each file is read only once per process.

Public API:
    get_meddic_gate_rules() -> dict
    get_ai_prompt() -> str
"""

import yaml
from functools import lru_cache


@lru_cache(maxsize=1)
def get_meddic_gate_rules() -> dict:
    """Load MEDDIC gating rules from rules.yml."""
    try:
        with open("rules.yml", "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
            return rules.get("meddic_gate_rules", {})
    except FileNotFoundError:
        print("WARNING: rules.yml not found. MEDDIC gating will be disabled.")
        return {}


@lru_cache(maxsize=1)
def get_ai_prompt() -> str:
    """Load AI smart log system prompt from prompts.yml."""
    try:
        with open("prompts.yml", "r", encoding="utf-8") as f:
            prompts = yaml.safe_load(f)
            return prompts.get("ai_smart_log", "")
    except FileNotFoundError:
        print("ERROR: prompts.yml not found.")
        return ""
