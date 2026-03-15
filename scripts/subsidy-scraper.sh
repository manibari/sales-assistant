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

echo "=== Subsidy Scraper — ${DATE} ==="
echo "Project: ${PROJECT_DIR}"

claude -p "Run the subsidy-scraper skill: scrape all configured sources (grants.nat.gov.tw, SBIR, SIIR), dedup against existing nx_subsidy records, create new subsidies, close expired ones, and regenerate materials/subsidies/INDEX.md and by-industry files. Output a summary when done." \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --max-turns 30 \
  2>"${LOG_DIR}/scraper-stderr-${DATE}.log" | \
  tee "${LOG_DIR}/scraper-${DATE}.jsonl"

echo "=== Done ==="
