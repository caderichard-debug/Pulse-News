#!/bin/bash

# Pulse News Aggregator - Quick Start Script
# This script sets up and starts the development environment

set -e  # Exit on error

echo "🚀 Starting Pulse News Aggregator..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚙️  Please edit .env with your API keys before continuing."
    echo ""
    echo "Required:"
    echo "  - ANTHROPIC_API_KEY (get from https://console.anthropic.com/)"
    echo "  - RESEND_API_KEY (get from https://resend.com/)"
    echo ""
    read -p "Press Enter after updating .env, or Ctrl+C to exit..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "🐳 Building Docker containers..."
docker-compose build

echo ""
echo "🏗️  Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 5

echo ""
echo "📊 Running database migrations..."
docker-compose exec backend alembic upgrade head

echo ""
echo "🌱 Seeding initial data..."
docker-compose exec backend python -m app.seed_data

echo ""
echo "✅ Pulse is ready!"
echo ""
echo "📍 Services:"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Frontend:     http://localhost:3000"
echo "   PostgreSQL:   localhost:5432"
echo ""
echo "📝 Next steps:"
echo "   1. Test the API:    curl http://localhost:8000/health"
echo "   2. View logs:       docker-compose logs -f"
echo "   3. Stop services:   docker-compose down"
echo ""
echo "🔧 Development commands:"
echo "   - Create migration:     docker-compose exec backend alembic revision --autogenerate -m \"description\""
echo "   - Apply migrations:     docker-compose exec backend alembic upgrade head"
echo "   - Access DB:            docker-compose exec db psql -U postgres -d news_db"
echo "   - Backend shell:        docker-compose exec backend python"
echo ""
echo "Happy coding! 🎉"
