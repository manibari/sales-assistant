#!/bin/bash
# Subsidy Scraper — headless agent runner
# Triggered by LaunchAgent: com.sk.agent.sales.subsidy-scraper
# Schedule: Monday & Thursday 08:00
#
# Usage: sk-agent-run ~/Documents/Projects/sales-assistant scripts/subsidy-scraper.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/materials/subsidies"
DATE=$(date +%Y-%m-%d)

# Source exec-lib for dashboard run recording
RIVENDELL_DIR="$HOME/Documents/Projects/rivendell"
if [ -f "$RIVENDELL_DIR/bin/sk-exec-lib" ]; then
  export SK_EXEC_REPO_DIR="$RIVENDELL_DIR"
  source "$RIVENDELL_DIR/bin/sk-exec-lib"
fi

echo "=== Subsidy Scraper — ${DATE} ==="
echo "Project: ${PROJECT_DIR}"

start_epoch=$(date +%s)

claude -p "Run the subsidy-scraper skill: scrape all configured sources (grants.nat.gov.tw, SBIR, SIIR), dedup against existing nx_subsidy records, create new subsidies, close expired ones, and regenerate materials/subsidies/INDEX.md and by-industry files. Output a summary when done." \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --verbose \
  --max-turns 30 \
  2>"${LOG_DIR}/scraper-stderr-${DATE}.log" | \
  tee "${LOG_DIR}/scraper-${DATE}.jsonl" \
  && run_exit=0 || run_exit=$?

end_epoch=$(date +%s)

# Record to dashboard DB (if exec-lib available)
if type _sk_exec_record_run &>/dev/null; then
  _sk_exec_record_run "sales-assistant" "subsidy-scraper" \
    "$start_epoch" "$end_epoch" "$run_exit" "" "" "" "" "" ""
fi

echo "=== Done ==="
exit "$run_exit"
