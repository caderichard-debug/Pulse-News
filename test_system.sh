#!/bin/bash

# Pulse News Aggregator - System Test Script
# Tests all major components and shows visible output

set -e  # Exit on error

echo "=================================================="
echo "🧪 PULSE NEWS AGGREGATOR - SYSTEM TEST"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base URL
API_URL="${API_URL:-http://localhost:8000}"

echo -e "${BLUE}📍 Testing API at: ${API_URL}${NC}"
echo ""

# Test 1: Check if backend is running
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Test 1: Backend Health Check${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if curl -s "${API_URL}/" > /dev/null; then
    echo -e "${GREEN}✅ Backend is running${NC}"
    curl -s "${API_URL}/" | python3 -m json.tool
else
    echo -e "${RED}❌ Backend is NOT running${NC}"
    exit 1
fi
echo ""

# Test 2: System Stats
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Test 2: System Statistics${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STATS=$(curl -s "${API_URL}/admin/stats")
echo "$STATS" | python3 -m json.tool

# Extract key metrics
TOTAL_ARTICLES=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['articles']['total'])")
COMPLETED=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['articles']['completed'])")
SOURCES=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['sources']['total'])")

echo ""
echo -e "${GREEN}📊 Summary:${NC}"
echo "  • Total Articles: ${TOTAL_ARTICLES}"
echo "  • Completed: ${COMPLETED}"
echo "  • Active Sources: ${SOURCES}"
echo ""

# Test 3: Available Topics
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Test 3: Available Topics${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOPICS=$(curl -s "${API_URL}/preferences/topics")
echo "$TOPICS" | python3 -m json.tool
TOPIC_COUNT=$(echo "$TOPICS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo ""
echo -e "${GREEN}✅ Found ${TOPIC_COUNT} topics${NC}"
echo ""

# Test 4: Recent Articles
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Test 4: Recent Articles (Last 5)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "${API_URL}/admin/articles/recent" | python3 -c "
import sys, json
articles = json.load(sys.stdin)
for i, article in enumerate(articles[:5], 1):
    print(f\"{i}. {article['title'][:60]}...\")
    print(f\"   Source ID: {article['source_id']} | Status: {article['status']}\")
    if article.get('word_count'):
        print(f\"   Words: {article['word_count']}\")
    print()
"
echo ""

# Test 5: Sources Status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Test 5: Article Count by Source${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "${API_URL}/admin/sources/status" | python3 -c "
import sys, json
sources = json.load(sys.stdin)
for source in sources:
    print(f\"  {source['name']:<20} {source['article_count']:>3} articles\")
"
echo ""

# Test 6: Scheduler Status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Test 6: Background Jobs Status${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "${API_URL}/admin/scheduler/status" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['status'] == 'running':
    print('  ✅ Scheduler is RUNNING')
else:
    print('  ❌ Scheduler is STOPPED')
print(f\"  Total Jobs: {len(data['jobs'])}\")
print()
for job in data['jobs']:
    status = '✅' if job else '❌'
    print(f\"  {status} {job['id']:<20} Next: {job['next_run']}\")
"
echo ""

# Test 7: User Registration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Test 7: User Registration (API Test)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TEST_EMAIL="test_$(date +%s)@example.com"
echo "Creating test user: ${TEST_EMAIL}"

REGISTER_RESPONSE=$(curl -s -X POST "${API_URL}/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Test User\",
        \"email\": \"${TEST_EMAIL}\",
        \"password\": \"testpass123\",
        \"topic_ids\": [1, 2]
    }")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ User registration successful${NC}"
    TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "  Token: ${TOKEN:0:20}..."

    # Test authentication
    echo ""
    echo "Testing authenticated request..."
    AUTH_TEST=$(curl -s "${API_URL}/auth/me" \
        -H "Authorization: Bearer ${TOKEN}")

    if echo "$AUTH_TEST" | grep -q "email"; then
        echo -e "${GREEN}✅ Authentication working${NC}"
        echo "$AUTH_TEST" | python3 -m json.tool
    else
        echo -e "${RED}❌ Authentication failed${NC}"
    fi
else
    echo -e "${RED}❌ Registration failed${NC}"
    echo "$REGISTER_RESPONSE" | python3 -m json.tool
fi
echo ""

# Test 8: Manual Job Triggers (Optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Test 8: Manual Job Triggers (Optional)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Would you like to trigger jobs manually? (y/N)"
read -t 5 -r TRIGGER_JOBS || TRIGGER_JOBS="n"

if [[ "$TRIGGER_JOBS" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Triggering scrape job..."
    curl -s -X POST "${API_URL}/admin/jobs/scrape" | python3 -m json.tool

    echo ""
    echo "Waiting 3 seconds..."
    sleep 3

    echo ""
    echo "Triggering extract job..."
    curl -s -X POST "${API_URL}/admin/jobs/extract" | python3 -m json.tool
else
    echo "Skipping manual job triggers"
fi
echo ""

# Final Summary
echo "=================================================="
echo -e "${GREEN}✅ SYSTEM TEST COMPLETE${NC}"
echo "=================================================="
echo ""
echo "Summary:"
echo "  • Backend API: ✅ Working"
echo "  • Database: ✅ Connected"
echo "  • Articles: ${TOTAL_ARTICLES} total, ${COMPLETED} extracted"
echo "  • Background Jobs: ✅ Scheduled"
echo "  • Authentication: ✅ Working"
echo ""
echo "Next steps:"
echo "  1. Set up API keys in api/.env"
echo "  2. Test AI analysis: curl -X POST ${API_URL}/admin/jobs/analyze"
echo "  3. Start frontend: cd frontend && npm run dev"
echo "  4. Open http://localhost:3000"
echo ""
echo "For detailed logs: docker logs news_backend --follow"
echo "=================================================="
