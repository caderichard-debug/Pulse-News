# Pulse Development Scripts

Quick reference for common development tasks.

## Testing

### Run All Tests
```bash
./scripts/test-all.sh
```
Runs frontend unit tests, frontend E2E tests, and backend tests. Shows summary of all results.

### Quick Test Summary
```bash
./scripts/test-quick.sh
```
Fast overview of test status without full output.

### Frontend Tests Only
```bash
./scripts/test-frontend.sh
```
Runs both unit and E2E tests for frontend.

### Backend Tests Only
```bash
./scripts/test-backend.sh
```
Runs all backend pytest tests.

### Individual Test Suites
```bash
# Frontend unit tests
cd frontend && npm test

# Frontend E2E tests
cd frontend && npx playwright test

# Backend tests
docker-compose exec backend pytest tests/
```

## Development Environment

### Start Everything
```bash
./scripts/dev-up.sh
```
Starts backend (PostgreSQL + FastAPI) and frontend dev server.

### Stop Everything
```bash
./scripts/dev-down.sh
```
Stops all services.

### View Logs
```bash
./scripts/logs.sh backend  # Backend logs
./scripts/logs.sh db       # Database logs
./scripts/logs.sh all      # All logs
```

## Database

### Reset Database
```bash
./scripts/db-reset.sh
```
⚠️ **WARNING:** Deletes all data and resets to clean state.

### Database Migrations
```bash
./scripts/db-migrate.sh create "description"  # Create new migration
./scripts/db-migrate.sh upgrade               # Apply migrations
./scripts/db-migrate.sh downgrade             # Rollback one migration
./scripts/db-migrate.sh history               # Show migration history
./scripts/db-migrate.sh current               # Show current version
```

## Build & Deploy

### Build Frontend
```bash
./scripts/build.sh
```
Creates production build in `frontend/.next`.

### Run Linters
```bash
./scripts/lint.sh
```
Runs ESLint on frontend code.

### Clean Artifacts
```bash
./scripts/clean.sh
```
Removes build artifacts, caches, and test outputs.

## Manual Commands

### Backend Shell
```bash
docker-compose exec backend bash
```

### Database Shell
```bash
docker-compose exec db psql -U postgres -d news_db
```

### Python Shell (with app context)
```bash
docker-compose exec backend python
```

### Run Specific Backend Test
```bash
docker-compose exec backend pytest tests/specific_test.py -v
```

### Run Specific E2E Test
```bash
cd frontend
npx playwright test e2e/specific-test.spec.ts
```

### Generate Playwright Report
```bash
cd frontend
npx playwright show-report
```

## Tips

1. **Make scripts executable:**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Run from project root:**
   All scripts should be run from `/Users/caderichard/Projects/Pulse/`

3. **Check services:**
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:3000

4. **Quick health check:**
   ```bash
   curl http://localhost:8000/docs  # Backend
   curl http://localhost:3000       # Frontend
   ```
