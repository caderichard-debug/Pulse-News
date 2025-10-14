#!/bin/bash
# Stop development environment

echo "🛑 Stopping Pulse Development Environment..."
echo ""

# Stop docker services
echo "📡 Stopping backend services..."
docker-compose down

# Kill any node processes (frontend dev server)
echo "💻 Stopping frontend dev server..."
pkill -f "next dev" || echo "No frontend dev server running"

echo ""
echo "✅ Development environment stopped"
