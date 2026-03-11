#!/bin/bash
# Trigger daily digest via the backend API.
# Sends to all /register'ed Telegram chats.
# Usage: cron runs this at 08:00 daily.

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

curl -s -X POST "${BACKEND_URL}/api/nx/telegram/daily-digest" \
  -o /dev/null -w "daily-digest: HTTP %{http_code}\n"
