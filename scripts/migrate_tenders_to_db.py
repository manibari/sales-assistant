#!/usr/bin/env python3
"""Migrate tender markdown files → nx_tender DB table.

Scans materials/tenders/cases/*.md, parses frontmatter, and UPSERTs into nx_tender.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.nexus.tender_db import sync_all_markdown


def main():
    print("Starting tender markdown → DB migration...")
    result = sync_all_markdown()
    print(f"Done: {result['synced']} synced, {result['errors']} errors, {result['total']} total files")


if __name__ == "__main__":
    main()
