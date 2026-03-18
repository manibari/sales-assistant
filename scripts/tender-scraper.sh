#!/bin/bash
# Tender Scraper — Python-based scraper
# Triggered by LaunchAgent: com.sk.agent.sales.tender-scraper
# Schedule: Daily 08:30
#
# Strategy:
#   1. Fetch ALL tenders from today (all types, not just 公開徵求)
#   2. Create case files for new tenders
#   3. Auto-enrich AI/IT-related tenders with full content from pcc.gov.tw
#   4. Archive past-deadline tenders
#   5. Regenerate INDEX.md

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/materials/tenders"
DATE=$(date +%Y-%m-%d)

echo "=== Tender Scraper — ${DATE} ==="
echo "Project: ${PROJECT_DIR}"

cd "${PROJECT_DIR}"
python scripts/tender_scraper.py --days 1 \
  2>&1 | tee "${LOG_DIR}/scraper-${DATE}.log"

echo "=== Done ==="
