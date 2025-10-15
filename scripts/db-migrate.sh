#!/bin/bash
# Create and run database migrations

set -e

ACTION=${1:-upgrade}

case $ACTION in
    "create")
        MESSAGE=${2:-"Auto-generated migration"}
        echo "📝 Creating new migration: $MESSAGE"
        docker-compose exec backend alembic revision --autogenerate -m "$MESSAGE"
        ;;
    "upgrade")
        echo "⬆️  Applying migrations..."
        docker-compose exec backend alembic upgrade head
        ;;
    "downgrade")
        echo "⬇️  Rolling back one migration..."
        docker-compose exec backend alembic downgrade -1
        ;;
    "history")
        echo "📜 Migration history:"
        docker-compose exec backend alembic history
        ;;
    "current")
        echo "📍 Current migration:"
        docker-compose exec backend alembic current
        ;;
    *)
        echo "Usage: $0 {create|upgrade|downgrade|history|current} [message]"
        echo ""
        echo "Examples:"
        echo "  $0 create 'add user preferences'  # Create new migration"
        echo "  $0 upgrade                         # Apply all pending migrations"
        echo "  $0 downgrade                       # Rollback one migration"
        echo "  $0 history                         # Show migration history"
        echo "  $0 current                         # Show current migration"
        exit 1
        ;;
esac

echo "✅ Done!"
