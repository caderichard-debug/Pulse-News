#!/bin/bash
# Quick test run - just the summaries

echo "🚀 Quick Test Summary"
echo "===================="
echo ""

# Frontend Unit
echo "📦 Frontend Unit Tests:"
cd frontend
npm test -- --passWithNoTests --silent 2>&1 | grep -E "Test Suites:|Tests:"
cd ..
echo ""

# Frontend E2E
echo "🎭 Frontend E2E Tests:"
cd frontend
npx playwright test --reporter=line 2>&1 | grep -E "passed|failed"
cd ..
echo ""

# Backend
echo "🐍 Backend Tests:"
docker-compose exec -T backend pytest tests/ -q 2>&1 | tail -3
echo ""
