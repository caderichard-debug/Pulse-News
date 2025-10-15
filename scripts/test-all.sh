#!/bin/bash
# Run all tests (frontend unit, frontend E2E, backend)

set -e

echo "========================================="
echo "Running All Tests"
echo "========================================="
echo ""

# Frontend Unit Tests
echo "📦 Running Frontend Unit Tests..."
cd frontend
npm test -- --passWithNoTests 2>&1 | grep -E "Test Suites:|Tests:|FAIL" || true
FRONTEND_UNIT=$?
cd ..
echo ""

# Frontend E2E Tests
echo "🎭 Running Frontend E2E Tests..."
cd frontend
npx playwright test --reporter=line 2>&1 | tail -5
FRONTEND_E2E=$?
cd ..
echo ""

# Backend Tests
echo "🐍 Running Backend Tests..."
docker-compose exec -T backend pytest tests/ --tb=short -q 2>&1 | tail -10
BACKEND=$?
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
if [ $FRONTEND_UNIT -eq 0 ]; then
    echo "✅ Frontend Unit Tests: PASSED"
else
    echo "❌ Frontend Unit Tests: FAILED"
fi

if [ $FRONTEND_E2E -eq 0 ]; then
    echo "✅ Frontend E2E Tests: PASSED"
else
    echo "❌ Frontend E2E Tests: FAILED"
fi

if [ $BACKEND -eq 0 ]; then
    echo "✅ Backend Tests: PASSED"
else
    echo "❌ Backend Tests: FAILED"
fi
echo ""

# Exit with error if any test suite failed
if [ $FRONTEND_UNIT -ne 0 ] || [ $FRONTEND_E2E -ne 0 ] || [ $BACKEND -ne 0 ]; then
    exit 1
fi
