#!/usr/bin/env bash
# run_qa.sh — One-click QA runner: seed → start servers → pytest → cleanup
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCREENSHOTS_DIR="$SCRIPT_DIR/screenshots"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${GREEN}=== Project Nexus QA Runner ===${NC}"
echo ""

# 1. Seed database
echo -e "${YELLOW}[1/4] Seeding database...${NC}"
cd "$PROJECT_ROOT"
python -m database.seed_rich
echo ""

# 2. Start servers
echo -e "${YELLOW}[2/4] Starting servers...${NC}"

# Start FastAPI
cd "$PROJECT_ROOT"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 &
API_PID=$!

# Start Next.js
cd "$PROJECT_ROOT/frontend"
npx next dev --port 3000 &
NEXT_PID=$!

# Wait for servers to be ready
echo "  Waiting for API (port 8001)..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
        echo "  API ready."
        break
    fi
    sleep 1
done

echo "  Waiting for Next.js (port 3000)..."
for i in $(seq 1 60); do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "  Next.js ready."
        break
    fi
    sleep 1
done
echo ""

# 3. Run tests
echo -e "${YELLOW}[3/4] Running tests...${NC}"
mkdir -p "$SCREENSHOTS_DIR"
cd "$PROJECT_ROOT"
python -m pytest tests/ -v --tb=short "$@"
TEST_EXIT=$?
echo ""

# 4. Cleanup
echo -e "${YELLOW}[4/4] Stopping servers...${NC}"
kill $API_PID 2>/dev/null || true
kill $NEXT_PID 2>/dev/null || true
wait $API_PID 2>/dev/null || true
wait $NEXT_PID 2>/dev/null || true

echo ""
if [ $TEST_EXIT -eq 0 ]; then
    echo -e "${GREEN}=== ALL TESTS PASSED ===${NC}"
else
    echo -e "${RED}=== SOME TESTS FAILED ===${NC}"
fi
echo "Screenshots saved to: $SCREENSHOTS_DIR"

exit $TEST_EXIT
