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
This directory contains utility scripts for maintaining and managing the Pulse project.

## 🔄 sync-local-container.sh

**Purpose**: Ensures local filesystem matches Docker container state for deployment-ready parity.

### What It Does

1. **Syncs Alembic Migrations**
   - Compares migration files between container and local filesystem
   - Copies any missing migrations in either direction
   - Verifies final counts match

2. **Checks Python Requirements**
   - Compares `requirements.txt` between container and local
   - Warns if they differ

3. **Checks Migration Status**
   - Shows current applied migration in database
   - Warns about pending migrations

4. **Generates Summary Report**
   - Visual status table showing sync state
   - Clear indicators for any issues

### Usage

```bash
# Run full sync
./scripts/sync-local-container.sh

# Show help
./scripts/sync-local-container.sh --help

# Preview changes without syncing (future feature)
./scripts/sync-local-container.sh --dry-run
```

### When to Use

- **After creating migrations in container**: Immediately sync to local
- **Before committing code**: Verify local matches container state
- **After pulling changes**: Ensure your container has latest migrations
- **Regular maintenance**: Run periodically to catch any drift

### Example Output

```
╔════════════════════════════════════════════════════════════╗
║  Pulse Local-Container Sync Script                        ║
╔════════════════════════════════════════════════════════════╗

═══ Checking Container Status ═══
✓ Backend container is running

═══ Syncing Alembic Migrations ═══
Container migrations: 7
Local migrations: 7
✓ Migrations synced: 7 files in both locations

═══ Checking Python Requirements ═══
✓ requirements.txt matches in both locations

═══ Checking Applied Migrations ═══
✓ Current database migration: e29da670f9de (head)

═══ Sync Summary ═══

┌─────────────────────────────────────────────────────────┐
│ Component                │ Status                       │
├─────────────────────────────────────────────────────────┤
│ Migrations               │ ✓ Synced (7 files)           │
│ Requirements.txt         │ ✓ Matched                    │
└─────────────────────────────────────────────────────────┘

Sync complete!

Next steps:
  1. Review any warnings above
  2. Run tests: docker-compose exec backend pytest
  3. Commit synced files: git add backend/alembic/versions/
```

### Troubleshooting

**Script exits with "Backend container is not running"**
- Start your containers: `docker-compose up -d`

**Migrations show as out of sync after running**
- Check for permission issues
- Manually verify: `docker exec news_backend ls /app/alembic/versions/`
- Compare with: `ls backend/alembic/versions/`

**Requirements.txt shows as different**
- Regenerate from container: `docker exec news_backend pip freeze > backend/requirements.txt`
- Or copy from container: `docker cp news_backend:/app/requirements.txt backend/`

## 📝 Adding New Scripts

When adding new utility scripts to this directory:

1. **Make them executable**: `chmod +x scripts/your-script.sh`
2. **Add help option**: Support `--help` flag
3. **Use colors for output**: Follow the pattern in `sync-local-container.sh`
4. **Document here**: Add a section to this README
5. **Reference in CLAUDE.md**: If AI assistants should use it, document in project context

## 🔗 Related Documentation

- [CLAUDE.md - Local-Container Parity](../CLAUDE.md#-local-container-parity-critical)
- [DEVELOPMENT_GUIDE.md](../docs/DEVELOPMENT_GUIDE.md)
- [HOW_TO_RUN_TESTS.md](../docs/HOW_TO_RUN_TESTS.md)
