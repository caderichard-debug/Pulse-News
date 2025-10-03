# Development Guide - Pulse News Aggregator

> Quick reference for common development tasks, Docker management, testing, and troubleshooting.

**Last Updated:** 2025-10-02

---

## 🐳 Docker Container Management

### Starting Services

```bash
# Start all services (backend, frontend, database)
docker-compose up --build

# Start in detached mode (background)
docker-compose up -d

# Start specific service only
docker-compose up backend
docker-compose up frontend
docker-compose up db
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Viewing Logs

```bash
# View backend logs (live)
docker logs news_backend -f

# View frontend logs
docker logs news_frontend -f

# View database logs
docker logs news_db -f

# View last 50 lines
docker logs news_backend --tail 50
```

### Container Status

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Check container health
docker-compose ps
```

### Executing Commands in Containers

```bash
# General format
docker exec <container_name> <command>

# Example: Run Python script in backend
docker exec news_backend python -m app.seed_data

# Example: Access PostgreSQL
docker-compose exec db psql -U postgres -d news_db

# Example: Run backend tests
docker-compose exec backend pytest

# Example: Interactive shell in backend
docker exec -it news_backend bash
```

### Common Docker Issues

**Issue: Port already in use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Issue: Container won't start**
```bash
# Clear everything and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up --build
```

**Issue: Database connection errors**
```bash
# Check database is running
docker ps | grep postgres

# Restart database
docker-compose restart db

# Check database logs
docker logs news_db
```

---

## 🧪 Running Tests

### Test Suite Overview

- **Total Tests:** 127 tests
- **Status:** 100% passing ✅
- **Framework:** pytest
- **Location:** `/backend/tests/`

### Run All Tests

```bash
# Run complete test suite
docker-compose exec backend pytest

# With verbose output
docker-compose exec backend pytest -v

# With very verbose output (shows print statements)
docker-compose exec backend pytest -vv

# With coverage report
docker-compose exec backend pytest --cov=app
```

### Run Specific Tests

```bash
# Run specific test file
docker-compose exec backend pytest tests/test_statistics_verifier.py

# Run specific test class
docker-compose exec backend pytest tests/test_statistics_verifier.py::TestStatisticsVerifier

# Run specific test method
docker-compose exec backend pytest tests/test_statistics_verifier.py::TestStatisticsVerifier::test_verification_pipeline

# Run multiple specific files
docker-compose exec backend pytest backend/tests/test_statistics_verifier.py backend/tests/test_article_clusterer.py backend/tests/test_context_generator.py -v
```

### Test Options

```bash
# Stop at first failure
docker-compose exec backend pytest -x

# Show local variables on failure
docker-compose exec backend pytest -l

# Run last failed tests only
docker-compose exec backend pytest --lf

# Run tests in parallel (faster)
docker-compose exec backend pytest -n auto

# Show print statements
docker-compose exec backend pytest -s

# Short traceback format
docker-compose exec backend pytest --tb=short

# Very verbose with short traceback
docker-compose exec backend pytest -vvv --tb=short
```

### Key Test Files

| File | Purpose |
|------|---------|
| `test_statistics_verifier.py` | V2 verification pipeline tests |
| `test_source_tracer.py` | Source extraction and tracing |
| `test_credibility_rater.py` | Credibility scoring system |
| `test_fact_check_integrator.py` | Fact-checking API integration |
| `test_newsletter_service_simple.py` | Email generation and sending |
| `test_article_extractor.py` | Content extraction (trafilatura + readability) |
| `test_ai_analyzer.py` | OpenAI GPT-4o-mini analysis |
| `test_article_clusterer.py` | Article clustering logic |
| `test_context_generator.py` | Context generation |

### Test Database

Tests use a separate in-memory SQLite database by default. No cleanup required.

---

## 🗄️ Database Management

### Access PostgreSQL

```bash
# Connect to database
docker-compose exec db psql -U postgres -d news_db

# Useful SQL queries
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM statistic_verifications;
SELECT * FROM articles WHERE processing_status = 'completed' LIMIT 5;
SELECT * FROM statistic_verifications WHERE verification_status = 'verified';
```

### Database Migrations

```bash
# Create new migration (after model changes)
docker-compose exec backend alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Rollback last migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history

# View current migration version
docker-compose exec backend alembic current
```

### Seed Database

```bash
# Seed initial data (sources, topics, frameworks)
docker-compose exec backend python -m app.seed_data
```

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U postgres news_db > backup.sql

# Restore from backup
docker-compose exec -T db psql -U postgres news_db < backup.sql
```

---

## 📧 Sending Test Emails/Newsletters

### Two Types of Emails

1. **Simple Test Email** - Basic connectivity test
2. **Full Newsletter** - Production-quality newsletter with all enrichments

### Method 1: Send Test Newsletter (Recommended)

```bash
# Send full newsletter to any email
docker exec news_backend python -c "
from app.services.newsletter_service import send_test_newsletter
result = send_test_newsletter('your-email@example.com')
print(f'Newsletter sent: {result}')
"
```

### Method 2: Via API Endpoint

```bash
# 1. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"cade.richard@gmail.com","password":"your_password"}' \
  | jq -r '.access_token')

# 2. Send test newsletter
curl -X POST http://localhost:8000/test/send-newsletter \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_email":"your-email@example.com"}'

# 3. Or send simple test email
curl -X POST http://localhost:8000/test/send-email \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_email":"your-email@example.com","subject":"Test","message":"Testing"}'
```

### Newsletter Contains

- 5 curated articles with AI summaries
- Political lean indicators (left/center/right badges)
- Ethical framework mappings with position on axis
- V2 verified statistics with badges (✓/⚠️/❌/⏳)
- Source credibility ratings (1-5 stars)
- Background context (historical, key players, timeline)
- Cross-source clustering information

### Email Configuration

Required environment variables in `/backend/.env`:
```bash
RESEND_API_KEY=re_...
FROM_EMAIL=onboarding@resend.dev  # Resend's test domain (no verification needed)
FROM_NAME=Pulse News
```

---

## 🔧 Manual Job Triggers

### Available Admin Endpoints

```bash
# Trigger RSS scraping
curl -X POST http://localhost:8000/admin/jobs/scrape

# Trigger article extraction
curl -X POST http://localhost:8000/admin/jobs/extract

# Trigger AI analysis
curl -X POST http://localhost:8000/admin/jobs/analyze

# Trigger framework mapping
curl -X POST http://localhost:8000/admin/jobs/frameworks

# Trigger statistics verification
curl -X POST http://localhost:8000/admin/jobs/verify-statistics

# Trigger article clustering
curl -X POST http://localhost:8000/admin/jobs/cluster-articles

# Trigger context generation
curl -X POST http://localhost:8000/admin/jobs/generate-context

# Check scheduler status
curl -X GET http://localhost:8000/admin/scheduler/status

# Get system stats
curl -X GET http://localhost:8000/admin/stats

# Get recent articles
curl -X GET http://localhost:8000/admin/articles/recent

# Get source statistics
curl -X GET http://localhost:8000/admin/sources/status
```

### Background Job Schedule

| Job | Frequency | Time |
|-----|-----------|------|
| RSS Scraping | Every 3 hours | - |
| Article Extraction | Every 4 hours | - |
| AI Analysis | Every 6 hours | - |
| Framework Mapping | Daily | 2:00 AM |
| Newsletter Generation | Daily | 10:20 AM PST |
| Statistics Verification | Every 6 hours | - |
| Article Clustering | Every 4 hours | - |
| Context Generation | Every 8 hours | - |

---

## 🔍 Common Development Tasks

### Task: Check System Health

```bash
# 1. Check if services are running
docker ps

# 2. Verify API is responding
curl http://localhost:8000/health

# 3. Check database connection
docker-compose exec db psql -U postgres -d news_db -c "SELECT COUNT(*) FROM articles;"

# 4. Check recent logs
docker logs news_backend --tail 50

# 5. Run test suite
docker-compose exec backend pytest
```

### Task: Analyze All Statistics

```bash
# Run the statistics tracing script
docker-compose exec backend python trace_all_statistics.py
```

### Task: Create New User

```bash
# Via API
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","name":"User Name"}'
```

### Task: Update User Preferences

```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' \
  | jq -r '.access_token')

# Update preferences
curl -X PUT http://localhost:8000/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic_preferences":[{"topic_id":1,"include_in_newsletter":true,"priority_level":"high"}]}'
```

### Task: View API Documentation

Navigate to: http://localhost:8000/docs (when services are running)

### Task: Debug Failed Job

```bash
# 1. Check scheduler status
curl http://localhost:8000/admin/scheduler/status | jq .

# 2. Check logs for errors
docker logs news_backend --tail 100 | grep ERROR

# 3. Manually trigger the job
curl -X POST http://localhost:8000/admin/jobs/<job-name>

# 4. Watch logs in real-time
docker logs news_backend -f
```

---

## 🐛 Troubleshooting

### Email Not Sending

**Symptoms:** Newsletter/test email doesn't arrive

**Solutions:**
1. Check Resend API key is set in `.env`
2. Verify `FROM_EMAIL=onboarding@resend.dev` (Resend's test domain)
3. Check spam folder
4. View logs: `docker logs news_backend | grep -i "email\|resend"`
5. Test Resend connectivity:
   ```bash
   curl -X GET http://localhost:8000/test/email-config
   ```

### Tests Failing

**Symptoms:** pytest returns failures

**Solutions:**
1. Ensure Docker containers are running: `docker ps`
2. Check for stale migrations: `docker-compose exec backend alembic upgrade head`
3. Run tests with verbose output: `docker-compose exec backend pytest -vvv`
4. Check specific test file: `docker-compose exec backend pytest tests/test_file.py -vv`
5. Clear cache and rebuild:
   ```bash
   docker-compose down -v
   docker-compose up --build
   ```

### Database Connection Errors

**Symptoms:** `could not connect to server` or `connection refused`

**Solutions:**
1. Check database is running: `docker ps | grep postgres`
2. Restart database: `docker-compose restart db`
3. Check database logs: `docker logs news_db`
4. Verify `DATABASE_URL` in `.env`:
   ```bash
   DATABASE_URL=postgresql://postgres:password@db:5432/news_db
   ```
5. Rebuild database volume:
   ```bash
   docker-compose down -v
   docker-compose up db
   ```

### API Returns 500 Errors

**Symptoms:** HTTP 500 Internal Server Error

**Solutions:**
1. Check backend logs: `docker logs news_backend --tail 50`
2. Verify environment variables are set: `docker exec news_backend env | grep API_KEY`
3. Restart backend: `docker-compose restart backend`
4. Check database migrations: `docker-compose exec backend alembic current`
5. Test with simple endpoint: `curl http://localhost:8000/health`

### Statistics Not Being Verified

**Symptoms:** `stats_verified = false` in article_analysis

**Solutions:**
1. Check if verification job is running:
   ```bash
   curl http://localhost:8000/admin/scheduler/status | jq '.jobs[] | select(.name | contains("verif"))'
   ```
2. Manually trigger verification:
   ```bash
   curl -X POST http://localhost:8000/admin/jobs/verify-statistics
   ```
3. Check OpenAI API key is set (required for AI source extraction)
4. Run trace script: `docker-compose exec backend python trace_all_statistics.py`
5. View verification logs: `docker logs news_backend | grep -i "statistic\|verif"`

### Port Already in Use

**Symptoms:** `Error starting userland proxy: bind: address already in use`

**Solutions:**
1. Find process using the port:
   ```bash
   # For port 8000 (backend)
   lsof -i :8000

   # For port 3000 (frontend)
   lsof -i :3000

   # For port 5432 (database)
   lsof -i :5432
   ```
2. Kill the process: `kill -9 <PID>`
3. Or change port in `docker-compose.yml`

---

## 📊 Key Files Reference

| File | Purpose | Path |
|------|---------|------|
| **Backend** |
| Main FastAPI App | Application entry point | `/backend/app/main.py` |
| Database Models | SQLModel schemas | `/backend/app/models.py` |
| Configuration | Environment variables | `/backend/app/config.py` |
| Job Scheduler | Background task config | `/backend/app/jobs/scheduler.py` |
| Newsletter Service | Email generation logic | `/backend/app/services/newsletter_service.py` |
| Statistics Verifier | V2 verification pipeline | `/backend/app/services/statistics_verifier.py` |
| Source Tracer | Stage 1: Source extraction | `/backend/app/services/source_tracer.py` |
| Credibility Rater | Stage 2: Credibility scoring | `/backend/app/services/credibility_rater.py` |
| Fact Check Integrator | Stage 3: Fact-checking | `/backend/app/services/fact_check_integrator.py` |
| Newsletter Template | HTML email template | `/backend/app/templates/newsletter.html` |
| **Frontend** |
| API Client | Backend communication | `/frontend/src/lib/api.ts` |
| Landing Page | Home page | `/frontend/src/app/page.tsx` |
| Login Page | Authentication | `/frontend/src/app/login/page.tsx` |
| Preferences Page | Topic management | `/frontend/src/app/preferences/page.tsx` |
| **Infrastructure** |
| Docker Compose | Service orchestration | `/docker-compose.yml` |
| Dockerfile | Backend container config | `/dockerfile` |
| Requirements | Python dependencies | `/requirements.txt` |
| **Database** |
| Migrations | Alembic migration files | `/backend/alembic/versions/` |
| Alembic Config | Migration configuration | `/backend/alembic.ini` |

---

## 🎯 Quick Start Checklist

When starting a new development session:

1. ✅ **Start Docker services:**
   ```bash
   docker-compose up -d
   ```

2. ✅ **Verify all containers are running:**
   ```bash
   docker ps
   ```

3. ✅ **Check API health:**
   ```bash
   curl http://localhost:8000/health
   ```

4. ✅ **Run tests to ensure stability:**
   ```bash
   docker-compose exec backend pytest
   ```

5. ✅ **Check recent logs for errors:**
   ```bash
   docker logs news_backend --tail 50
   ```

6. ✅ **Verify database is accessible:**
   ```bash
   docker-compose exec db psql -U postgres -d news_db -c "SELECT COUNT(*) FROM articles;"
   ```

---

## 📈 System Status Check

```bash
# One-command health check
echo "=== Docker Containers ===" && \
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" && \
echo -e "\n=== API Health ===" && \
curl -s http://localhost:8000/health | jq . && \
echo -e "\n=== Database Stats ===" && \
docker-compose exec -T db psql -U postgres -d news_db -c "SELECT 'Articles: ' || COUNT(*) FROM articles; SELECT 'Users: ' || COUNT(*) FROM users; SELECT 'Verified Stats: ' || COUNT(*) FROM statistic_verifications WHERE verification_status = 'verified';" && \
echo -e "\n=== Scheduler Status ===" && \
curl -s http://localhost:8000/admin/scheduler/status | jq '.scheduler_running'
```

---

## 💡 Pro Tips

1. **Use `docker-compose exec` for one-off commands** - Faster than `docker exec` for already-running services
2. **Always check logs first** - Most issues are apparent in `docker logs news_backend`
3. **Test in isolation** - Run specific test files when debugging
4. **Use `-f` flag for live logs** - `docker logs news_backend -f` streams in real-time
5. **Keep containers running** - Use `docker-compose up -d` instead of stopping/starting repeatedly
6. **Interactive API docs** - Use http://localhost:8000/docs to test endpoints visually
7. **Database queries** - Use `psql` for quick data inspection instead of writing scripts
8. **Background jobs** - Check `/admin/scheduler/status` before manually triggering jobs

---

**Last Updated:** 2025-10-02
**Maintained By:** Pulse Development Team
**Related Docs:** [ARCHITECTURE.md](ARCHITECTURE.md), [STATISTICS_VERIFICATION_V2_PLAN.md](STATISTICS_VERIFICATION_V2_PLAN.md)
