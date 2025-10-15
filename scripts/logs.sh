#!/bin/bash
# View logs from services

SERVICE=${1:-backend}

case $SERVICE in
    "backend"|"be")
        docker logs news_backend -f --tail=100
        ;;
    "db"|"database")
        docker logs news_db -f --tail=100
        ;;
    "all")
        docker-compose logs -f --tail=100
        ;;
    *)
        echo "Usage: $0 {backend|db|all}"
        echo ""
        echo "Examples:"
        echo "  $0 backend  # Follow backend logs"
        echo "  $0 db       # Follow database logs"
        echo "  $0 all      # Follow all logs"
        exit 1
        ;;
esac
