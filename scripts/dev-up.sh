#!/bin/bash
# Start development environment

echo "🚀 Starting Pulse Development Environment..."
echo ""

# Start backend services
echo "📡 Starting backend services (PostgreSQL + FastAPI)..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if backend is responding
echo "🔍 Checking backend health..."
curl -s http://localhost:8000/docs > /dev/null && echo "✅ Backend is ready" || echo "⚠️  Backend might not be ready yet"

echo ""
echo "💻 Starting frontend dev server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================="
echo "Development Environment Ready!"
echo "========================================="
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo ""
echo "To stop:"
echo "  - Kill frontend: kill $FRONTEND_PID"
echo "  - Stop backend:  docker-compose down"
echo ""
