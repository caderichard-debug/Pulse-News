#!/bin/bash
# Clean build artifacts and caches

echo "🧹 Cleaning build artifacts..."
echo ""

# Frontend
echo "💻 Cleaning frontend..."
rm -rf frontend/.next
rm -rf frontend/node_modules/.cache
rm -rf frontend/playwright-report
rm -rf frontend/test-results
echo "  ✓ Removed .next, caches, and test artifacts"

# Backend
echo "🐍 Cleaning backend..."
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find backend -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
find backend -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  ✓ Removed Python caches"

echo ""
echo "✅ Cleanup complete!"
