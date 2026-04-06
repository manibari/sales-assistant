#!/bin/bash
# Knowledge Sync — hourly RAG rebuild
# Triggered by LaunchAgent: com.sk.agent.sales.knowledge-sync
# Schedule: Every hour at :15
#
# Calls the memory syncAll API to rebuild knowledge from parsed files.
# The knowledge_worker (embedded in FastAPI) handles file parsing separately.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%H:%M)
LOG_DIR="${PROJECT_DIR}/logs"
mkdir -p "$LOG_DIR"

# Source exec-lib for dashboard run recording (optional — skip on failure)
RIVENDELL_DIR="$HOME/Documents/Projects/rivendell"
if [ -f "$RIVENDELL_DIR/bin/sk-exec-lib" ]; then
  export SK_EXEC_REPO_DIR="$RIVENDELL_DIR"
  set +e
  source "$RIVENDELL_DIR/bin/sk-exec-lib" 2>/dev/null || true
  set -e
fi

echo "=== Knowledge Sync — ${DATE} ${TIMESTAMP} ==="
echo "Project: ${PROJECT_DIR}"

start_epoch=$(date +%s)

# Call the syncAll API endpoint
BACKEND_URL="http://127.0.0.1:8002"
response=$(curl -s -X POST "${BACKEND_URL}/api/nx/memory/sync-all" \
  -H "Content-Type: application/json" \
  -d '{}' \
  --max-time 120 \
  2>&1) && run_exit=0 || run_exit=$?

echo "Response: ${response}"

end_epoch=$(date +%s)

# Record to dashboard DB (if exec-lib available)
if type _sk_exec_record_run &>/dev/null; then
  _sk_exec_record_run "sales-assistant" "knowledge-sync" \
    "$start_epoch" "$end_epoch" "$run_exit" "" "" "" "" "" ""
fi

echo "=== Done (exit: ${run_exit}) ==="
exit "$run_exit"
