#!/usr/bin/env python3
"""Output the current keyword count (metric for autoresearch)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.tender_scraper import _load_keywords

kws = _load_keywords()
print(len(kws))
