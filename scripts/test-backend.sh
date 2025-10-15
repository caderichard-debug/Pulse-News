#!/bin/bash
# Run backend tests

set -e

echo "========================================="
echo "Backend Tests"
echo "========================================="
echo ""

docker-compose exec -T backend pytest tests/ -v

echo ""
echo "✅ All backend tests passed!"
