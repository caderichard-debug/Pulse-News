#!/bin/bash
# Reset database to clean state

echo "🗄️  Resetting Database..."
echo ""
echo "⚠️  WARNING: This will delete all data!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Stopping containers..."
docker-compose down

echo "Removing database volume..."
docker volume rm pulse_postgres_data || true

echo "Starting containers..."
docker-compose up -d

echo "Waiting for database to be ready..."
sleep 5

echo "Running migrations..."
docker-compose exec -T backend alembic upgrade head

echo ""
echo "✅ Database reset complete!"
echo "Run './scripts/seed-db.sh' to add sample data"
