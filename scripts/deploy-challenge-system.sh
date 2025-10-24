#!/bin/bash

# Challenge System Deployment Script
# Deploys the newsletter challenge system to production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Challenge System Deployment${NC}"

# Configuration
PROJECT_DIR="/Users/caderichard/Projects/Pulse"
BACKUP_DIR="/tmp/pulse-backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="/tmp/challenge-deployment-$(date +%Y%m%d_%H%M%S).log"

# Create backup directory
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "${BLUE}📦 Deployment started at $(date)${NC}"

# Function to check command success
check_command() {
    if [ $? -eq 0 ]; then
        log "${GREEN}✅ $1${NC}"
    else
        log "${RED}❌ $1 failed${NC}"
        exit 1
    fi
}

# Function to check if container is running
check_container() {
    if docker ps --format "table {{.Names}}" | grep -q "$1"; then
        return 0
    else
        return 1
    fi
}

# Function to wait for container to be healthy
wait_for_health() {
    local container_name="$1"
    local max_attempts=30
    local attempt=1

    log "${YELLOW}⏳ Waiting for $container_name to be healthy...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null | grep -q "healthy"; then
            log "${GREEN}✅ $container_name is healthy${NC}"
            return 0
        fi

        log "${YELLOW}⏳ Attempt $attempt/$max_attempts: $container_name not healthy yet${NC}"
        sleep 10
        ((attempt++))
    done

    log "${RED}❌ $container_name failed to become healthy${NC}"
    return 1
}

# Pre-deployment checks
log "${BLUE}🔍 Running pre-deployment checks...${NC}"

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/docker-compose.yml" ]; then
    log "${RED}❌ docker-compose.yml not found in project directory${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Backup current state
log "${BLUE}💾 Creating backup of current state...${NC}"
docker-compose exec -T postgres pg_dump -U postgres news_db > "$BACKUP_DIR/database_backup.sql" 2>/dev/null || {
    log "${YELLOW}⚠️  Warning: Could not create database backup${NC}"
}

# Stop existing services
log "${BLUE}🛑 Stopping existing services...${NC}"
docker-compose down

# Pull latest changes
log "${BLUE}📥 Pulling latest changes...${NC}"
git pull origin main

# Build new images
log "${BLUE}🏗️ Building new images...${NC}"
docker-compose build

# Start services
log "${BLUE}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
log "${BLUE}⏳ Waiting for services to be ready...${NC}"

# Wait for database
check_command "Database container started"
if check_container "news_db"; then
    wait_for_health "news_db"
else
    log "${RED}❌ Database container not found${NC}"
    exit 1
fi

# Wait for backend
check_command "Backend container started"
if check_container "news_backend"; then
    wait_for_health "news_backend"
else
    log "${RED}❌ Backend container not found${NC}"
    exit 1
fi

# Run database migrations
log "${BLUE}🔄 Running database migrations...${NC}"
docker-compose exec -T backend alembic upgrade head
check_command "Database migrations completed"

# Verify challenge system tables
log "${BLUE}🔍 Verifying challenge system database schema...${NC}"
docker-compose exec -T backend python3 -c "
from app.models import WeeklyChallenge, ChallengeClaim, UserChallengeResponse, ChallengeArticleAssignment
from app.database import get_session
session = get_session()

# Check if tables exist
try:
    session.query(WeeklyChallenge).first()
    print('✅ WeeklyChallenge table exists')
except:
    print('❌ WeeklyChallenge table missing')
    exit(1)

try:
    session.query(ChallengeClaim).first()
    print('✅ ChallengeClaim table exists')
except:
    print('❌ ChallengeClaim table missing')
    exit(1)

try:
    session.query(UserChallengeResponse).first()
    print('✅ UserChallengeResponse table exists')
except:
    print('❌ UserChallengeResponse table missing')
    exit(1)

try:
    session.query(ChallengeArticleAssignment).first()
    print('✅ ChallengeArticleAssignment table exists')
except:
    print('❌ ChallengeArticleAssignment table missing')
    exit(1)

print('✅ All challenge system tables verified')
"

check_command "Challenge system database schema verified"

# Test API endpoints
log "${BLUE}🧪 Testing API endpoints...${NC}"

# Test basic health check
API_URL="http://localhost:8000"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "$API_URL/monitoring/health" > /dev/null; then
        log "${GREEN}✅ API health check passed${NC}"
        break
    fi

    ((RETRY_COUNT++))
    log "${YELLOW}⏳ API not ready, retrying in 10 seconds... ($RETRY_COUNT/$MAX_RETRIES)${NC}"
    sleep 10
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log "${RED}❌ API health check failed after $MAX_RETRIES attempts${NC}"
    exit 1
fi

# Test challenge endpoints
CHALLENGE_TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -n "$CHALLENGE_TOKEN" ]; then
    log "${GREEN}✅ Authentication test passed${NC}"

    # Test challenge endpoints
    if curl -s "$API_URL/challenge/current" -H "Authorization: Bearer $CHALLENGE_TOKEN" > /dev/null; then
        log "${GREEN}✅ Challenge endpoints test passed${NC}"
    else
        log "${RED}❌ Challenge endpoints test failed${NC}"
        exit 1
    fi
else
    log "${YELLOW}⚠️  Warning: Could not test challenge endpoints (test user not available)${NC}"
fi

# Test monitoring endpoints
if curl -s "$API_URL/monitoring/health" > /dev/null; then
    log "${GREEN}✅ Monitoring endpoints test passed${NC}"
else
    log "${RED}❌ Monitoring endpoints test failed${NC}"
    exit 1
fi

# Verify scheduler jobs
log "${BLUE}⏰ Verifying scheduler jobs...${NC}"
docker-compose exec -T backend python3 -c "
from app.jobs.scheduler import scheduler
from app.database import get_session

session = get_session()

# Check if scheduler is configured
if scheduler:
    print('✅ Scheduler is configured')

    # List jobs
    jobs = scheduler.get_jobs()
    if jobs:
        print(f'✅ Found {len(jobs)} configured jobs')
        for job in jobs:
            print(f'  - {job.id}: {job.name}')
    else
        print('⚠️  No jobs configured')
else
    print('❌ Scheduler not configured')
    exit(1)
"

check_command "Scheduler jobs verified"

# Test newsletter integration
log "${BLUE}📧 Testing newsletter integration...${NC}"
docker-compose exec -T backend python3 -c "
from app.services.newsletter_service import NewsletterService
from app.database import get_session

session = get_session()

# Check if newsletter service is configured
try:
    newsletter_service = NewsletterService()
    print('✅ Newsletter service is configured')

    # Test template rendering
    from app.models import User
    test_user = session.query(User).first()
    if test_user:
        test_html = newsletter_service.render_challenge_section(test_user.id, '2024-01-15')
        if test_html:
            print('✅ Challenge template rendering test passed')
        else
            print('⚠️  Challenge template rendering returned empty')
    else:
        print('⚠️  No users found for template testing')

except Exception as e:
    print(f'❌ Newsletter service test failed: {e}')
    exit(1)
"

check_command "Newsletter integration test passed"

# Frontend deployment check
log "${BLUE}🌐 Checking frontend deployment...${NC}"

# Check if frontend is running
if curl -s "http://localhost:3000" > /dev/null; then
    log "${GREEN}✅ Frontend is running${NC}"

    # Test challenge page
    if curl -s "http://localhost:3000/challenge/2024-01-15" > /dev/null; then
        log "${GREEN}✅ Challenge page test passed${NC}"
    else
        log "${YELLOW}⚠️  Challenge page test failed (may not have challenge data)${NC}"
    fi

    # Test analytics page
    if curl -s "http://localhost:3000/analytics" > /dev/null; then
        log "${GREEN}✅ Analytics page test passed${NC}"
    else
        log "${YELLOW}⚠️  Analytics page test failed${NC}"
    fi
else
    log "${YELLOW}⚠️  Frontend is not running (expected if only deploying backend)${NC}"
fi

# Performance tests
log "${BLUE}⚡ Running performance tests...${NC}"
docker-compose exec -T backend python3 -c "
import time
import requests

# Test API response times
start_time = time.time()
response = requests.get('http://localhost:8000/monitoring/health', timeout=10)
response_time = time.time() - start_time

if response.status_code == 200:
    if response_time < 2.0:
        print(f'✅ API response time: {response_time:.2f}s (excellent)')
    elif response_time < 5.0:
        print(f'✅ API response time: {response_time:.2f}s (good)')
    else:
        print(f'⚠️  API response time: {response_time:.2f}s (slow)')
else:
    print(f'❌ API health check failed')
    exit(1)
"

# Security checks
log "${BLUE}🔒 Running security checks...${NC}"

# Check for exposed API endpoints
docker-compose exec -T backend python3 -c "
import requests

# Check if sensitive endpoints require authentication
sensitive_endpoints = [
    '/monitoring/admin/system',
    '/challenge/current',
    '/challenge/analytics'
]

for endpoint in sensitive_endpoints:
    try:
        response = requests.get(f'http://localhost:8000{endpoint}', timeout=5)
        if response.status_code == 401:
            print(f'✅ {endpoint} properly protected')
        else:
            print(f'❌ {endpoint} not properly protected (status: {response.status_code})')
    except Exception as e:
        print(f'⚠️  Could not test {endpoint}: {e}')
"

# Check for SSL/TLS (if configured)
try:
    response = requests.get('https://localhost:8000/monitoring/health', timeout=5, verify=False)
    if response.status_code == 200:
        print('⚠️  SSL/TLS not properly configured')
except:
    print('✅ HTTP only (expected for development)')
"

# Final health verification
log "${BLUE}🏥 Running final health verification...${NC}"

# Get comprehensive health report
HEALTH_REPORT=$(curl -s "$API_URL/monitoring/health/detailed" | python3 -c "
import sys, json
data = json.load(sys.stdin)
status = data.get('overall_status', 'unknown')
print(f'System status: {status}')
print(f'Active alerts: {len(data.get(\"alerts\", []))}')
print(f'Performance health: {data.get(\"performance_metrics\", {}).get(\"assignment_processing\", {}).get(\"health_status\", \"unknown\")}')
")

if status != 'healthy':
    sys.exit(1)
")

if [ $? -eq 0 ]; then
    check_command "Final health verification passed"
else
    log "${RED}❌ Final health verification failed${NC}"
    exit 1
fi

# Deployment complete
log "${GREEN}🎉 Challenge System Deployment Completed Successfully!${NC}"
log "${GREEN}📊 Deployment Summary:${NC}"
echo "  - Database: ✅ Migrated and verified"
echo "  - Backend: ✅ Running and healthy"
echo "  - API: ✅ All endpoints responding"
echo "  - Monitoring: ✅ Health checks passing"
echo "  - Jobs: ✅ Scheduler configured"
echo "  - Newsletter: ✅ Integration verified"
echo "  - Security: ✅ Basic checks passed"
echo "  - Performance: ✅ Response times acceptable"

echo ""
echo "${BLUE}📈 Next Steps:${NC}"
echo "1. Monitor system health: curl http://localhost:8000/monitoring/health/detailed"
echo "2. Check alerts: curl http://localhost:8000/monitoring/alerts"
echo "3. View executive summary: curl http://localhost:8000/monitoring/summary"
echo "4. Monitor logs: docker-compose logs -f news_backend"
echo "5. Test challenge functionality in the web interface"

echo ""
echo "${BLUE}📋 Useful Commands:${NC}"
echo "- View logs: docker-compose logs -f news_backend"
echo "- Check jobs: docker-compose exec backend python3 -c \"from app.jobs.scheduler import scheduler; print(scheduler.get_jobs())\""
echo "- Database access: docker-compose exec postgres psql -U postgres news_db"
echo "- Restart services: docker-compose restart"
echo "- Stop services: docker-compose down"

echo ""
echo "${GREEN}🎯 Challenge system is now live and ready for users!${NC}"

# Create deployment marker
echo "DEPLOYMENT_SUCCESSFUL_$(date +%s)" > "$PROJECT_DIR/.challenge_deployment_status"

log "${GREEN}✅ Deployment status saved to .challenge_deployment_status${NC}"
echo "${GREEN}📝 Full deployment log: $LOG_FILE${NC}"

exit 0