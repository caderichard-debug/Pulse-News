.PHONY: help test test-quick test-frontend test-backend test-unit test-e2e
.PHONY: dev-up dev-down dev-restart logs logs-backend logs-db
.PHONY: db-reset db-migrate db-upgrade db-downgrade db-shell
.PHONY: build lint clean shell

# Default target
help:
	@echo "Pulse Development Commands"
	@echo "=========================="
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests (unit + E2E + backend)"
	@echo "  make test-quick     - Quick test summary"
	@echo "  make test-frontend  - Frontend tests only (unit + E2E)"
	@echo "  make test-backend   - Backend tests only"
	@echo "  make test-unit      - Frontend unit tests only"
	@echo "  make test-e2e       - Frontend E2E tests only"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up         - Start all services"
	@echo "  make dev-down       - Stop all services"
	@echo "  make dev-restart    - Restart all services"
	@echo "  make logs           - Follow all logs"
	@echo "  make logs-backend   - Follow backend logs"
	@echo "  make logs-db        - Follow database logs"
	@echo ""
	@echo "Database:"
	@echo "  make db-reset       - Reset database (⚠️  deletes all data)"
	@echo "  make db-migrate     - Create new migration"
	@echo "  make db-upgrade     - Apply pending migrations"
	@echo "  make db-downgrade   - Rollback one migration"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo ""
	@echo "Build & Quality:"
	@echo "  make build          - Build frontend for production"
	@echo "  make lint           - Run linters"
	@echo "  make clean          - Clean build artifacts"
	@echo ""
	@echo "Utilities:"
	@echo "  make shell          - Open backend Python shell"
	@echo ""

# Testing targets
test:
	@echo "========================================="
	@echo "Running All Tests"
	@echo "========================================="
	@echo ""
	@echo "📦 Frontend Unit Tests..."
	@cd frontend && npm test -- --passWithNoTests 2>&1 | grep -E "Test Suites:|Tests:|FAIL" || true
	@echo ""
	@echo "🎭 Frontend E2E Tests..."
	@cd frontend && npx playwright test --reporter=line 2>&1 | tail -5
	@echo ""
	@echo "🐍 Backend Tests..."
	@docker-compose exec -T backend pytest tests/ --tb=short -q 2>&1 | tail -10

test-quick:
	@echo "🚀 Quick Test Summary"
	@echo "===================="
	@echo ""
	@echo "📦 Frontend Unit Tests:"
	@cd frontend && npm test -- --passWithNoTests --silent 2>&1 | grep -E "Test Suites:|Tests:"
	@echo ""
	@echo "🎭 Frontend E2E Tests:"
	@cd frontend && npx playwright test --reporter=line 2>&1 | grep -E "passed|failed"
	@echo ""
	@echo "🐍 Backend Tests:"
	@docker-compose exec -T backend pytest tests/ -q 2>&1 | tail -3

test-frontend:
	@echo "📦 Running Frontend Unit Tests..."
	@cd frontend && npm test -- --passWithNoTests
	@echo ""
	@echo "🎭 Running Frontend E2E Tests..."
	@cd frontend && npx playwright test

test-backend:
	@echo "🐍 Running Backend Tests..."
	@docker-compose exec -T backend pytest tests/ -v

test-unit:
	@echo "📦 Running Frontend Unit Tests..."
	@cd frontend && npm test -- --passWithNoTests

test-e2e:
	@echo "🎭 Running Frontend E2E Tests..."
	@cd frontend && npx playwright test

# Development targets
dev-up:
	@echo "🚀 Starting Pulse Development Environment..."
	@docker-compose up -d
	@echo "⏳ Waiting for services..."
	@sleep 5
	@curl -s http://localhost:8000/docs > /dev/null && echo "✅ Backend ready at http://localhost:8000" || echo "⚠️  Backend starting..."
	@echo ""
	@echo "Frontend dev server:"
	@echo "  cd frontend && npm run dev"

dev-down:
	@echo "🛑 Stopping services..."
	@docker-compose down
	@pkill -f "next dev" || true
	@echo "✅ Stopped"

dev-restart: dev-down dev-up

logs:
	@docker-compose logs -f --tail=100

logs-backend:
	@docker logs news_backend -f --tail=100

logs-db:
	@docker logs news_db -f --tail=100

# Database targets
db-reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Continue? (yes/no): " confirm && [ "$$confirm" = "yes" ] || (echo "Cancelled" && exit 1)
	@docker-compose down
	@docker volume rm pulse_postgres_data || true
	@docker-compose up -d
	@sleep 5
	@docker-compose exec -T backend alembic upgrade head
	@echo "✅ Database reset complete"

db-migrate:
	@read -p "Migration message: " msg && \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

db-upgrade:
	@echo "⬆️  Applying migrations..."
	@docker-compose exec backend alembic upgrade head
	@echo "✅ Done"

db-downgrade:
	@echo "⬇️  Rolling back one migration..."
	@docker-compose exec backend alembic downgrade -1
	@echo "✅ Done"

db-shell:
	@docker-compose exec db psql -U postgres -d news_db

# Build & quality targets
build:
	@echo "🏗️  Building frontend..."
	@cd frontend && npm run build
	@echo "✅ Build complete: frontend/.next"

lint:
	@echo "🔍 Running linters..."
	@cd frontend && npm run lint
	@echo "✅ Linting complete"

clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf frontend/.next
	@rm -rf frontend/node_modules/.cache
	@rm -rf frontend/playwright-report
	@rm -rf frontend/test-results
	@find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find backend -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find backend -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Utility targets
shell:
	@docker-compose exec backend bash
