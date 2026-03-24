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

# Source exec-lib for dashboard run recording
RIVENDELL_DIR="$HOME/Documents/Projects/rivendell"
if [ -f "$RIVENDELL_DIR/bin/sk-exec-lib" ]; then
  export SK_EXEC_REPO_DIR="$RIVENDELL_DIR"
  source "$RIVENDELL_DIR/bin/sk-exec-lib"
fi

echo "=== Tender Scraper — ${DATE} ==="
echo "Project: ${PROJECT_DIR}"

start_epoch=$(date +%s)

cd "${PROJECT_DIR}"
python3 scripts/tender_scraper.py --days 1 \
  2>&1 | tee "${LOG_DIR}/scraper-${DATE}.log" \
  && run_exit=0 || run_exit=$?

end_epoch=$(date +%s)

# Record to dashboard DB (if exec-lib available)
if type _sk_exec_record_run &>/dev/null; then
  _sk_exec_record_run "sales-assistant" "tender-scraper" \
    "$start_epoch" "$end_epoch" "$run_exit" "" "" "" "" "" ""
fi

# Run keyword analysis (discover new candidates from unmatched tenders)
if [ "$run_exit" -eq 0 ] && [ -f "${PROJECT_DIR}/scripts/tender_keyword_analyzer.py" ]; then
  echo "=== Keyword Analysis ==="
  python3 "${PROJECT_DIR}/scripts/tender_keyword_analyzer.py" --auto 2>&1 \
    | tee -a "${LOG_DIR}/keyword-analysis-${DATE}.log" || true
fi

echo "=== Done ==="
exit "$run_exit"
