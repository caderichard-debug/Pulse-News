#!/bin/bash
# Run linters

echo "🔍 Running Linters..."
echo ""

# Backend (if you add linting later)
echo "🐍 Backend:"
echo "  (No linter configured yet)"
echo ""

# Frontend
echo "💻 Frontend:"
cd frontend
npm run lint
cd ..

echo ""
echo "✅ Linting complete!"
