#!/bin/bash
# Material Health Check — headless agent runner
# Triggered by LaunchAgent: com.sk.agent.sales.material-health
# Schedule: Sunday 09:00
#
# Usage: sk-agent-run ~/Documents/Projects/sales-assistant scripts/material-health.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATE=$(date +%Y-%m-%d)

echo "=== Material Health Check — ${DATE} ==="
echo "Project: ${PROJECT_DIR}"

claude -p "Run the material-health skill: check all materials/ for missing frontmatter, expired subsidies, stale company info, and INDEX consistency. Write the report to materials/HEALTH_REPORT.md. Output a summary when done." \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --verbose \
  --max-turns 15 \
  2>"${PROJECT_DIR}/materials/health-stderr-${DATE}.log" | \
  tee "${PROJECT_DIR}/materials/health-${DATE}.jsonl"

echo "=== Done ==="
