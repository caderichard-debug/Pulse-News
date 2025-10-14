#!/bin/bash

# Pulse Local-Container Sync Script
# This script ensures the local filesystem matches the Docker container state
# for deployment-ready parity.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Container names
BACKEND_CONTAINER="news_backend"
FRONTEND_CONTAINER="news_frontend"

# Directories
BACKEND_MIGRATIONS_LOCAL="backend/alembic/versions"
BACKEND_MIGRATIONS_CONTAINER="/app/alembic/versions"
BACKEND_REQUIREMENTS_LOCAL="backend/requirements.txt"
BACKEND_REQUIREMENTS_CONTAINER="/app/requirements.txt"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Pulse Local-Container Sync Script                        ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}═══ $1 ═══${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if containers are running
check_containers() {
    print_header "Checking Container Status"

    if ! docker ps --format '{{.Names}}' | grep -q "^${BACKEND_CONTAINER}$"; then
        print_error "Backend container (${BACKEND_CONTAINER}) is not running"
        echo "Please start containers with: docker-compose up -d"
        exit 1
    fi
    print_success "Backend container is running"
}

# Sync alembic migrations
sync_migrations() {
    print_header "Syncing Alembic Migrations"

    # Create migrations directory if it doesn't exist locally
    mkdir -p "$BACKEND_MIGRATIONS_LOCAL"

    # Get list of migrations in container
    container_migrations=$(docker exec "$BACKEND_CONTAINER" sh -c "cd $BACKEND_MIGRATIONS_CONTAINER && ls -1 *.py 2>/dev/null || true" | grep -v __pycache__ || true)

    # Get list of migrations locally
    local_migrations=$(cd "$BACKEND_MIGRATIONS_LOCAL" && ls -1 *.py 2>/dev/null || true)

    # Count migrations
    container_count=$(echo "$container_migrations" | grep -c ".py" || echo "0")
    local_count=$(echo "$local_migrations" | grep -c ".py" || echo "0")

    echo "Container migrations: $container_count"
    echo "Local migrations: $local_count"

    if [ "$container_count" -eq 0 ] && [ "$local_count" -eq 0 ]; then
        print_warning "No migrations found in either location"
        return
    fi

    # Find migrations only in container
    if [ "$container_count" -gt "$local_count" ]; then
        print_warning "Found migrations in container not present locally"

        while IFS= read -r migration; do
            if [ -n "$migration" ] && [ "$migration" != "__pycache__" ]; then
                if [ ! -f "$BACKEND_MIGRATIONS_LOCAL/$migration" ]; then
                    echo "  Copying: $migration"
                    docker cp "$BACKEND_CONTAINER:$BACKEND_MIGRATIONS_CONTAINER/$migration" "$BACKEND_MIGRATIONS_LOCAL/"
                    print_success "Copied $migration from container"
                fi
            fi
        done <<< "$container_migrations"
    fi

    # Find migrations only locally
    if [ "$local_count" -gt "$container_count" ]; then
        print_warning "Found migrations locally not present in container"

        while IFS= read -r migration; do
            if [ -n "$migration" ] && [ "$migration" != "__pycache__" ]; then
                # Check if migration exists in container
                if ! docker exec "$BACKEND_CONTAINER" test -f "$BACKEND_MIGRATIONS_CONTAINER/$migration" 2>/dev/null; then
                    echo "  Copying: $migration"
                    docker cp "$BACKEND_MIGRATIONS_LOCAL/$migration" "$BACKEND_CONTAINER:$BACKEND_MIGRATIONS_CONTAINER/"
                    print_success "Copied $migration to container"
                fi
            fi
        done <<< "$local_migrations"
    fi

    # Final count
    final_container_count=$(docker exec "$BACKEND_CONTAINER" sh -c "cd $BACKEND_MIGRATIONS_CONTAINER && ls -1 *.py 2>/dev/null | grep -v __pycache__ | wc -l" | tr -d ' ')
    final_local_count=$(cd "$BACKEND_MIGRATIONS_LOCAL" && ls -1 *.py 2>/dev/null | wc -l)

    if [ "$final_container_count" -eq "$final_local_count" ]; then
        print_success "Migrations synced: $final_local_count files in both locations"
    else
        print_error "Migration count mismatch after sync: Container=$final_container_count, Local=$final_local_count"
    fi
}

# Check requirements.txt
check_requirements() {
    print_header "Checking Python Requirements"

    if [ ! -f "$BACKEND_REQUIREMENTS_LOCAL" ]; then
        print_warning "Local requirements.txt not found"
        return
    fi

    # Compare local and container requirements
    local_hash=$(md5sum "$BACKEND_REQUIREMENTS_LOCAL" | cut -d' ' -f1)
    container_hash=$(docker exec "$BACKEND_CONTAINER" md5sum "$BACKEND_REQUIREMENTS_CONTAINER" | cut -d' ' -f1)

    if [ "$local_hash" = "$container_hash" ]; then
        print_success "requirements.txt matches in both locations"
    else
        print_warning "requirements.txt differs between local and container"
        echo "  Consider regenerating: docker exec $BACKEND_CONTAINER pip freeze > $BACKEND_REQUIREMENTS_LOCAL"
    fi
}

# Check migration status in database
check_migration_status() {
    print_header "Checking Applied Migrations"

    current_migration=$(docker exec "$BACKEND_CONTAINER" alembic current 2>/dev/null | grep -v "INFO" | head -1 || echo "none")

    if [ "$current_migration" = "none" ]; then
        print_warning "No migrations applied to database"
    else
        print_success "Current database migration: $current_migration"
    fi

    # Check for pending migrations
    pending=$(docker exec "$BACKEND_CONTAINER" alembic heads 2>/dev/null | grep -v "INFO" | head -1 || echo "")

    if [ -n "$pending" ] && [ "$current_migration" != "$pending" ]; then
        print_warning "Pending migrations detected. Run: docker-compose exec backend alembic upgrade head"
    fi
}

# Generate summary report
generate_report() {
    print_header "Sync Summary"

    echo ""
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│ Component                │ Status                       │"
    echo "├─────────────────────────────────────────────────────────┤"

    # Migrations
    final_local_count=$(cd "$BACKEND_MIGRATIONS_LOCAL" && ls -1 *.py 2>/dev/null | wc -l)
    final_container_count=$(docker exec "$BACKEND_CONTAINER" sh -c "cd $BACKEND_MIGRATIONS_CONTAINER && ls -1 *.py 2>/dev/null | grep -v __pycache__ | wc -l" | tr -d ' ')

    if [ "$final_local_count" -eq "$final_container_count" ]; then
        echo -e "│ Migrations               │ ${GREEN}✓ Synced ($final_local_count files)${NC}         │"
    else
        echo -e "│ Migrations               │ ${RED}✗ Out of sync${NC}                │"
    fi

    # Requirements
    local_hash=$(md5sum "$BACKEND_REQUIREMENTS_LOCAL" 2>/dev/null | cut -d' ' -f1 || echo "missing")
    container_hash=$(docker exec "$BACKEND_CONTAINER" md5sum "$BACKEND_REQUIREMENTS_CONTAINER" 2>/dev/null | cut -d' ' -f1 || echo "missing")

    if [ "$local_hash" = "$container_hash" ]; then
        echo -e "│ Requirements.txt         │ ${GREEN}✓ Matched${NC}                    │"
    else
        echo -e "│ Requirements.txt         │ ${YELLOW}⚠ Differs${NC}                    │"
    fi

    echo "└─────────────────────────────────────────────────────────┘"
    echo ""
}

# Main execution
main() {
    check_containers
    sync_migrations
    check_requirements
    check_migration_status
    generate_report

    echo -e "\n${GREEN}Sync complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review any warnings above"
    echo "  2. Run tests: docker-compose exec backend pytest"
    echo "  3. Commit synced files: git add backend/alembic/versions/"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Sync local filesystem with Docker container state for deployment parity."
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --dry-run      Show what would be synced without making changes"
        echo ""
        echo "Examples:"
        echo "  $0              # Run full sync"
        echo "  $0 --dry-run    # Preview changes without syncing"
        exit 0
        ;;
    --dry-run)
        echo "DRY RUN MODE - No changes will be made"
        echo ""
        check_containers
        # Add dry-run logic here if needed
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
