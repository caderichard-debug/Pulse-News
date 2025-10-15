#!/bin/bash
# Run only frontend tests (unit + E2E)

set -e

echo "========================================="
echo "Frontend Tests"
echo "========================================="
echo ""

# Unit Tests
echo "📦 Running Unit Tests..."
cd frontend
npm test -- --passWithNoTests
echo ""

# E2E Tests
echo "🎭 Running E2E Tests..."
npx playwright test

echo ""
echo "✅ All frontend tests passed!"
