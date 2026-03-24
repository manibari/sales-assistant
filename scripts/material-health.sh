#!/bin/bash
# Material Health Check — headless agent runner
# Triggered by LaunchAgent: com.sk.agent.sales.material-health
# Schedule: Sunday 09:00
#
# Usage: sk-agent-run ~/Documents/Projects/sales-assistant scripts/material-health.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATE=$(date +%Y-%m-%d)

# Source exec-lib for dashboard run recording
RIVENDELL_DIR="$HOME/Documents/Projects/rivendell"
if [ -f "$RIVENDELL_DIR/bin/sk-exec-lib" ]; then
  export SK_EXEC_REPO_DIR="$RIVENDELL_DIR"
  source "$RIVENDELL_DIR/bin/sk-exec-lib"
fi

echo "=== Material Health Check — ${DATE} ==="
echo "Project: ${PROJECT_DIR}"

start_epoch=$(date +%s)

claude -p "Run the material-health skill: check all materials/ for missing frontmatter, expired subsidies, stale company info, and INDEX consistency. Write the report to materials/HEALTH_REPORT.md. Output a summary when done." \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --verbose \
  --max-turns 15 \
  2>"${PROJECT_DIR}/materials/health-stderr-${DATE}.log" | \
  tee "${PROJECT_DIR}/materials/health-${DATE}.jsonl" \
  && run_exit=0 || run_exit=$?

end_epoch=$(date +%s)

# Record to dashboard DB (if exec-lib available)
if type _sk_exec_record_run &>/dev/null; then
  _sk_exec_record_run "sales-assistant" "material-health" \
    "$start_epoch" "$end_epoch" "$run_exit" "" "" "" "" "" ""
fi

echo "=== Done ==="
exit "$run_exit"
