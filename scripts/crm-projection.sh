#!/bin/bash
# CRM Projection — headless agent runner
# Triggered by LaunchAgent: com.sk.agent.sales.crm-projection
# Schedule: Daily 07:00
#
# Usage: sk-agent-run ~/Documents/Projects/sales-assistant scripts/crm-projection.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATE=$(date +%Y-%m-%d)

echo "=== CRM Projection — ${DATE} ==="
echo "Project: ${PROJECT_DIR}"

claude -p "Run the crm-projection skill: query all active clients from nx_client, get their deal pipeline data, cross-reference with reports/customer-intel/INDEX.md, and regenerate materials/clients/INDEX.md. Output a summary when done." \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --verbose \
  --max-turns 15 \
  2>"${PROJECT_DIR}/materials/clients/projection-stderr-${DATE}.log" | \
  tee "${PROJECT_DIR}/materials/clients/projection-${DATE}.jsonl"

echo "=== Done ==="
