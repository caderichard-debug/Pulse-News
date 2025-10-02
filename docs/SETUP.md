# Setup Guide

## Prerequisites

- **Docker & Docker Compose** - For containerized development
- **Python 3.11+** - For local backend development
- **Node.js 18+** - For frontend development
- **Anthropic API Key** - [Get one here](https://console.anthropic.com/)
- **Resend API Key** - [Get one here](https://resend.com/)

## Quick Start (Docker)

### 1. Clone and Configure

```bash
git clone <your-repo>
cd Pulse
cp .env.example .env
```

Edit `.env` with your API keys:
```env
# Required
ANTHROPIC_API_KEY=your_anthropic_key_here
RESEND_API_KEY=your_resend_key_here

# Optional - defaults work for development
DATABASE_URL=postgresql://pulseuser:pulsepass@db:5432/pulsedb
SECRET_KEY=your-secret-key-for-jwt
```

### 2. Start Services

```bash
docker-compose up --build
```

This starts:
- **Backend** (FastAPI) - http://localhost:8000
- **Database** (PostgreSQL) - localhost:5432
- **Frontend** (Next.js) - http://localhost:3000

### 3. Run Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Seed Initial Data

```bash
docker-compose exec backend python -m app.seed_data
```

This creates:
- 8 news sources (AP, Reuters, NPR, BBC, etc.)
- 5 topic categories
- 10 seed ethical frameworks

### 5. Verify Installation

```bash
# Test API
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# View API docs
open http://localhost:8000/docs

# View frontend
open http://localhost:3000
```

## Local Development (No Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL locally
createdb pulsedb

# Configure .env for local DB
DATABASE_URL=postgresql://localhost/pulsedb

# Run migrations
alembic upgrade head

# Seed data
python -m app.seed_data

# Start server
uvicorn app.main:app --reload
```

Backend available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start development server
npm run dev
```

Frontend available at http://localhost:3000

## Database Management

### Create New Migration

```bash
# Auto-generate from model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Or create empty migration
docker-compose exec backend alembic revision -m "description"
```

### Apply Migrations

```bash
# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Upgrade one version
docker-compose exec backend alembic upgrade +1

# Downgrade one version
docker-compose exec backend alembic downgrade -1

# Show current version
docker-compose exec backend alembic current

# Show migration history
docker-compose exec backend alembic history
```

### Reset Database

```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm pulse_postgres_data

# Restart and re-initialize
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.seed_data
```

## Testing

### Run Tests

```bash
# All tests
docker-compose exec backend python -m pytest tests/ -v

# Specific test file
docker-compose exec backend python -m pytest tests/test_api.py -v

# With coverage
docker-compose exec backend python -m pytest tests/ --cov=app --cov-report=html
```

See [TESTING.md](TESTING.md) for detailed testing guide.

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key for AI analysis | `sk-ant-...` |
| `RESEND_API_KEY` | Resend API key for email | `re_...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://pulseuser:pulsepass@db:5432/pulsedb` |
| `SECRET_KEY` | JWT signing secret | Random string |
| `ENVIRONMENT` | Environment name | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## Scheduled Jobs

Jobs run automatically via APScheduler:

| Job | Schedule | Description |
|-----|----------|-------------|
| Scrape RSS | Every 3 hours | Fetch new articles from sources |
| Extract Content | Every 4 hours | Extract full article text |
| Analyze Articles | Every 4 hours | AI analysis of articles |
| Generate Frameworks | Daily at 2 AM | Map articles to frameworks |
| Send Newsletters | Daily at 7 AM | Send personalized emails |

### Trigger Jobs Manually

```bash
# Via API (requires admin auth)
curl -X POST http://localhost:8000/admin/scrape
curl -X POST http://localhost:8000/admin/extract
curl -X POST http://localhost:8000/admin/analyze
curl -X POST http://localhost:8000/admin/frameworks

# Or via Python
docker-compose exec backend python -c "
from app.services.rss_scraper import scrape_all_active_sources
from app.database import get_session
with next(get_session()) as session:
    scrape_all_active_sources(session)
"
```

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Database Connection Failed

```bash
# Check database is running
docker-compose ps

# View database logs
docker-compose logs db

# Connect to database directly
docker-compose exec db psql -U pulseuser -d pulsedb
```

### Migration Conflicts

```bash
# If migrations are out of sync
docker-compose exec backend alembic heads  # Show current heads

# Merge heads if multiple exist
docker-compose exec backend alembic merge heads -m "merge migrations"
```

### API Key Not Working

```bash
# Verify environment variables are loaded
docker-compose exec backend python -c "
from app.config import settings
print(f'Anthropic key: {settings.anthropic_api_key[:10]}...')
print(f'Resend key: {settings.resend_api_key[:10]}...')
"

# Restart after .env changes
docker-compose restart backend
```

### Frontend Not Connecting to Backend

Check CORS configuration in `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
# Add tests
# Run tests
docker-compose exec backend python -m pytest tests/ -v

# Commit
git add .
git commit -m "feat: add my feature"
```

### 2. Database Schema Changes

```bash
# Modify models in app/models.py

# Generate migration
docker-compose exec backend alembic revision --autogenerate -m "add new field"

# Review generated migration in alembic/versions/

# Apply migration
docker-compose exec backend alembic upgrade head

# Test migration is reversible
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

### 3. Adding New Dependencies

```bash
# Backend
cd backend
pip install new-package
pip freeze > requirements.txt

# Rebuild container
docker-compose up --build backend

# Frontend
cd frontend
npm install new-package
# Restart dev server
```

## Next Steps

- Read [ARCHITECTURE.md](../ARCHITECTURE.md) for system design
- Read [TESTING.md](TESTING.md) for testing guidelines
- Read [API.md](API.md) for API documentation
- Check [../README.md](../README.md) for project overview
