#!/bin/bash
# Build frontend for production

set -e

echo "🏗️  Building Frontend for Production..."
echo ""

cd frontend
npm run build

echo ""
echo "✅ Build complete!"
echo "Build output: frontend/.next"
