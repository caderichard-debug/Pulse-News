# Claude Context - Pulse News Aggregator

> **AI-powered news aggregation with ethical framework mapping to help build context and connect headlines into coherent mental models.**

## 🎯 Project Overview

**Pulse** aggregates news from trusted sources and uses AI to:
- Summarize articles (100 words)
- Analyze sentiment and political bias
- Extract and verify key statistics with source tracing
- **Map articles to underlying ethical debates** (competitive edge)
- Generate daily newsletters that connect the dots

### Example Framework Mapping
```
Article: "Biden Cancels Student Loan Debt"
Framework: Individual Liberty vs. Collective Welfare
Position: +6 (leans toward collective welfare)
Explanation: Policy prioritizes community benefit over individual responsibility
```

## 🏗️ Tech Stack

### Backend (Python 3.11)
- **FastAPI** - REST API framework
- **SQLModel 0.0.16** - ORM with Pydantic validation
- **PostgreSQL** - Relational database
- **Alembic** - Database migrations
- **APScheduler** - Background job scheduling
- **OpenAI GPT-4o-mini** - AI analysis (cheapest GPT-4 model)

### Services
- **feedparser** - RSS feed parsing
- **trafilatura** - Article content extraction (primary)
- **readability-lxml** - Fallback extractor
- **Resend API** - Email delivery
- **Jinja2** - Email template rendering

### Frontend
- **Next.js 15.5.4** (React 19.1.0, TypeScript 5)
- **Tailwind CSS 4** with PostCSS
- **Turbopack** - Fast bundler (dev & build)

### Infrastructure
- **Docker & Docker Compose**
- **Railway/Render** (free tier MVP)

## 📊 Database Schema

```
sources → articles → article_analysis
   ↓                       ↓
topics              article_frameworks → frameworks
   ↓                                           ↑
user_topic_preferences              (AI-generated debates)
   ↓
users → newsletters

Enhancement Tables (V2):
- statistic_verifications (with V2 source tracing fields)
- source_credibility_ratings
- article_clusters & article_cluster_members
- article_context
```

### Key Models

**Article Pipeline:**
- `Article` - Scraped articles (content, metadata, processing status)
- `ArticleAnalysis` - AI analysis (summary, sentiment, political lean, key stats)
- `ArticleFramework` - Link between articles and ethical frameworks

**Statistics Verification V2:**
- `StatisticVerification` - Extracted stats with source tracing and fact-checking
  - V2 fields: `source_url`, `source_name`, `source_credibility_score`
  - Fact-check: `fact_check_status`, `fact_check_source`, `fact_check_url`
- `SourceCredibilityRating` - Cached credibility scores for domains

**User & Newsletters:**
- `User` - Authentication, preferences, subscription tier
- `Newsletter` - Generated emails with article/framework references

## 🔄 Data Flow

### 1. Article Ingestion Pipeline
```
RSS Feeds → Scraper (every 3h) → Articles (PENDING)
                ↓
        Extractor (every 4h) → Full content
                ↓
        AI Analyzer (OpenAI GPT-4o-mini) → Analysis
                ↓
        Framework Mapper → Article-Framework links
                ↓
        Stats Verifier V2 → Verified statistics
```

### 2. Statistics Verification V2 (Three-Stage Pipeline)
```
1. Source Tracing (AI-powered)
   - Extract source URLs/names from article content
   - Identify citations and references

2. Credibility Rating
   - Rate source credibility (0.0-1.0)
   - Cache ratings by domain
   - Heuristics: .gov (+0.3), .edu (+0.3), universities (+0.2)

3. Fact-Checking
   - Query external APIs (Google Fact Check, ClaimBuster)
   - Return verification status: verified, false, mixed, unverifiable
```

### 3. Newsletter Generation
```
User Preferences → Topic Filtering → Top 5 Articles
                ↓
        Related Frameworks
                ↓
        Template Rendering (Jinja2)
                ↓
        HTML Email → Resend API → User Inbox
```

## 📁 Project Structure

```
Pulse/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings (env vars)
│   │   ├── database.py      # DB session management
│   │   ├── models.py        # SQLModel schemas
│   │   ├── seed_data.py     # Initial data seeding
│   │   ├── routes/          # API endpoints
│   │   │   ├── admin.py     # Admin routes
│   │   │   ├── articles.py  # Article CRUD
│   │   │   ├── auth.py      # Authentication
│   │   │   ├── preferences.py
│   │   │   └── test_email.py
│   │   ├── services/        # Business logic
│   │   │   ├── ai_analyzer.py
│   │   │   ├── article_extractor.py
│   │   │   ├── rss_scraper.py
│   │   │   ├── framework_generator.py
│   │   │   ├── newsletter_service.py
│   │   │   ├── statistics_verifier.py  # V2 orchestrator
│   │   │   ├── source_tracer.py        # V2: Stage 1
│   │   │   ├── credibility_rater.py    # V2: Stage 2
│   │   │   ├── fact_check_integrator.py # V2: Stage 3
│   │   │   ├── article_clusterer.py
│   │   │   └── context_generator.py
│   │   ├── jobs/            # Scheduled tasks
│   │   │   ├── scheduler.py
│   │   │   └── tasks.py
│   │   ├── templates/       # Email templates (Jinja2)
│   │   │   └── newsletter.html  # Main newsletter template
│   │   └── utils/           # Helpers (auth, OpenAI client)
│   ├── tests/               # Test suite (127 tests, 100% passing)
│   └── trace_all_statistics.py  # Script to analyze all stats
├── frontend/                # Next.js app
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── STATISTICS_VERIFICATION_V2_PLAN.md
│   ├── HOW_TO_SEND_TEST_EMAIL.md
│   └── README.md
├── docker-compose.yml
├── dockerfile
└── requirements.txt
```

## 🔧 Common Development Commands

### Docker Operations
```bash
# Start all services
docker-compose up --build

# Restart backend only
docker-compose restart backend

# View logs
docker logs news_backend -f

# Stop all
docker-compose down
```

### Database Migrations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

### Running Tests
```bash
# All tests
docker-compose exec backend pytest

# Specific test file
docker-compose exec backend pytest tests/test_statistics_verifier.py

# With verbose output
docker-compose exec backend pytest -vv

# With coverage
docker-compose exec backend pytest --cov=app
```

### Manual Tasks
```bash
# Seed initial data
docker-compose exec backend python -m app.seed_data

# Run statistics tracing script
docker-compose exec backend python trace_all_statistics.py
```

## 🔐 Environment Variables

Required in `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@db:5432/news_db

# AI (OpenAI)
OPENAI_API_KEY=sk-proj-...
AI_MODEL=gpt-4o-mini

# Email
RESEND_API_KEY=re_...
FROM_EMAIL=onboarding@resend.dev  # Resend test domain (no verification needed)
FROM_NAME=Pulse News

# Auth
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Fact-checking (Optional)
GOOGLE_FACT_CHECK_API_KEY=...
CLAIMBUSTER_API_KEY=...
```

## 📝 API Endpoints

### Public Routes
- `GET /health` - Health check
- `POST /auth/register` - User registration
- `POST /auth/login` - Login (returns JWT)
- `GET /articles` - Browse articles

### Protected Routes (require JWT)
- `GET /auth/me` - Current user
- `PUT /preferences` - Update topic preferences
- `GET /preferences/newsletter-preview` - Preview newsletter
- `GET /newsletters/latest` - Latest newsletter

### Admin Routes
- `GET /admin/stats` - System statistics
- `GET /admin/scheduler/status` - Job scheduler status
- `POST /admin/jobs/scrape` - Manually trigger RSS scrape
- `POST /admin/jobs/extract` - Manually trigger article extraction
- `POST /admin/jobs/analyze` - Manually trigger AI analysis
- `POST /admin/jobs/frameworks` - Manually trigger framework updates
- `POST /admin/jobs/verify-statistics` - Manually trigger stats verification
- `POST /admin/jobs/cluster-articles` - Manually trigger article clustering
- `POST /admin/jobs/generate-context` - Manually trigger context generation
- `GET /admin/articles/recent` - Get recent articles
- `GET /admin/sources/status` - Get source statistics

### Testing Routes
- `GET /test/email-config` - Check email configuration
- `POST /test/send-email` - Send test email

**Interactive Docs:** http://localhost:8000/docs

## 🧪 Testing Strategy

### Current Test Coverage
- **127 tests, 100% passing**
- Unit tests for all services
- Integration tests for API routes
- Database relationship tests
- V2 statistics verification tests

### Key Test Files
- `test_statistics_verifier.py` - V2 verification pipeline
- `test_source_tracer.py` - Source extraction
- `test_credibility_rater.py` - Credibility scoring
- `test_fact_check_integrator.py` - Fact-check APIs
- `test_newsletter_service_simple.py` - Email generation

## 🎨 Frontend Structure

The frontend is built with Next.js 15 using the App Router pattern:

### Pages
- **`/` (Landing Page)** - Hero section, features, trusted sources, CTA
- **`/login`** - User login with JWT authentication
- **`/signup`** - New user registration
- **`/preferences`** - Topic preference management

### API Client (`src/lib/api.ts`)
- Centralized API communication
- JWT token management (localStorage)
- TypeScript interfaces for type safety
- Methods for auth, preferences, topics

### Tech Details
- **React 19.1.0** - Latest React with new features
- **Turbopack** - Next.js's fast bundler for dev and production
- **Tailwind CSS 4** - Utility-first CSS with PostCSS
- **TypeScript 5** - Full type safety

### Running Frontend
```bash
# Development mode
cd frontend && npm run dev

# Production build
npm run build && npm start
```

## 📧 Sending Test Newsletters

### Quick Test
```bash
# 1. Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

# 2. Send test email
curl -X POST http://localhost:8000/test/send-email \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_email":"your-email@example.com","subject":"Test","message":"Testing!"}'
```

### Using Admin UI
1. Navigate to http://localhost:8000/docs
2. Click "Authorize" → Enter: `Bearer YOUR_TOKEN`
3. Go to `/test/send-email` endpoint
4. Try it out

**Note:** Uses `onboarding@resend.dev` (Resend's test domain) - no verification needed!

## 🚀 Background Jobs (APScheduler)

Configured in `backend/app/jobs/scheduler.py`:

1. **RSS Scraping** - Every 3 hours
2. **Article Extraction** - Every 4 hours
3. **AI Analysis** - Every 6 hours
4. **Framework Mapping** - Daily at 2am (discovers new frameworks on Sundays)
5. **Newsletter Generation** - Daily at 10:20 AM PST
6. **Statistics Verification V2** - Every 6 hours
7. **Article Clustering** - Every 4 hours
8. **Context Generation** - Every 8 hours

## 📊 Statistics Verification V2

### Architecture
Three-stage pipeline for comprehensive verification:

1. **Source Tracing** (`source_tracer.py`)
   - AI extracts source URLs/names from article content
   - Stores: `source_url`, `source_name`, `source_excerpt`

2. **Credibility Rating** (`credibility_rater.py`)
   - Rates source credibility (0.0-1.0)
   - Heuristics: .gov +0.3, .edu +0.3, universities +0.2
   - Caches ratings in `source_credibility_ratings` table

3. **Fact-Checking** (`fact_check_integrator.py`)
   - Queries external APIs (Google Fact Check, ClaimBuster)
   - Returns: `fact_check_status`, `fact_check_source`, `fact_check_url`

### Final Status Determination
- `fact_check_status == "false"` → FALSE
- `fact_check_status == "verified" AND credibility >= 0.6` → VERIFIED
- `source_credibility >= 0.7 AND no contradiction` → VERIFIED
- `fact_check_status == "mixed"` → DISPUTED
- Otherwise → UNVERIFIED

### Newsletter Badge Display
- ✓ Verified (green)
- ⚠️ Disputed (orange)
- ❌ False (red)
- ⏳ Unverified (gray)
- ⭐⭐⭐⭐⭐ Credibility stars (1-5)
- Source link with name
- Confidence percentage

## 🔍 Common Tasks & Solutions

### Task: Analyze All Statistics in Database
```bash
# Run the tracing script
docker-compose exec backend python trace_all_statistics.py
```

### Task: Send Test Newsletter
```bash
# Preview newsletter (no send)
curl -X GET http://localhost:8000/preferences/newsletter-preview \
  -H "Authorization: Bearer $TOKEN"

# Send actual newsletter
curl -X POST http://localhost:8000/admin/send-newsletter \
  -H "Authorization: Bearer $TOKEN"
```

### Task: Manually Trigger Jobs
```bash
# Trigger RSS scrape
curl -X POST http://localhost:8000/admin/jobs/scrape

# Trigger article extraction
curl -X POST http://localhost:8000/admin/jobs/extract

# Trigger AI analysis
curl -X POST http://localhost:8000/admin/jobs/analyze

# Trigger statistics verification
curl -X POST http://localhost:8000/admin/jobs/verify-statistics

# Check scheduler status
curl -X GET http://localhost:8000/admin/scheduler/status
```

### Task: Debug Failed Tests
```bash
# Run with verbose output and stop at first failure
docker-compose exec backend pytest -vvv -x

# Run specific test
docker-compose exec backend pytest tests/test_file.py::TestClass::test_method -vv
```

### Task: Check Database State
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d news_db

# Useful queries
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM statistic_verifications;
SELECT * FROM statistic_verifications WHERE verification_status = 'verified';
```

## 💡 Key Design Decisions

1. **Batch AI Processing** - Process 5 articles per API call (60% cost savings)
2. **Dual Extraction Methods** - trafilatura (primary) + readability (fallback) = 95% success rate
3. **Framework Evolution** - Start with 10 seed frameworks, AI discovers new ones from clusters
4. **V2 Verification** - Source tracing + credibility rating + fact-checking (more robust than cross-reference)
5. **Email-Compatible Templates** - Inline styles, table layouts for maximum compatibility

## 📈 Current Status

### ✅ Completed
- Core pipeline (scraping → extraction → analysis → frameworks)
- V2 statistics verification with source tracing
- Newsletter generation & email delivery
- User authentication & preferences
- Comprehensive test suite (127 tests passing)
- Background job scheduling

### 🔄 In Progress
- **Frontend UI** (Next.js 15 with React 19)
  - ✅ Landing page with hero, features, and CTA
  - ✅ Login page (`/login`)
  - ✅ Signup page (`/signup`)
  - ✅ Preferences page (`/preferences`)
  - ✅ API client with authentication
- Email analytics & tracking

### 📅 Upcoming
- Framework discovery optimization
- Real-time updates
- Mobile app
- Premium features

## 📚 Key Documentation References

- **Full Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **V2 Verification Plan:** [docs/STATISTICS_VERIFICATION_V2_PLAN.md](docs/STATISTICS_VERIFICATION_V2_PLAN.md)
- **Email Testing:** [docs/HOW_TO_SEND_TEST_EMAIL.md](docs/HOW_TO_SEND_TEST_EMAIL.md)
- **API Reference:** http://localhost:8000/docs (when running)

## 🐛 Common Issues & Solutions

### Issue: Email not sending
**Solution:**
1. Check `RESEND_API_KEY` in `.env`
2. Use `onboarding@resend.dev` as `FROM_EMAIL`
3. Restart backend: `docker-compose restart backend`
4. Check logs: `docker logs news_backend`

### Issue: Tests failing
**Solution:**
1. Ensure test database is clean: `docker-compose exec backend pytest --create-db`
2. Check for stale migrations: `alembic upgrade head`
3. Review logs for specific errors

### Issue: Statistics not being verified
**Solution:**
1. Check if job is running: Look for "Statistics verification" in logs
2. Verify API keys are set (OPENAI_API_KEY for AI extraction)
3. Run manual trace: `docker-compose exec backend python trace_all_statistics.py`

### Issue: Docker build fails
**Solution:**
1. Clear cache: `docker-compose build --no-cache`
2. Remove volumes: `docker-compose down -v`
3. Rebuild: `docker-compose up --build`

## 💰 Cost Optimization

**AI Costs** (OpenAI GPT-4o-mini):
- $0.150 per 1M input tokens, $0.600 per 1M output tokens
- Batch processing (5 articles/call) = 60% savings
- Estimated: $2-5/month for 50 users

**Email Costs** (Resend):
- Free tier: 3,000 emails/month
- Paid tier: ~$5/month for 5,000 users

**Scaling Targets:**
- 50 users: $0-5/month
- 500 users: $30-50/month
- 5,000 users: $100-300/month

---

## 🎯 Quick Start Checklist

When starting a new session:
1. ✅ Check if Docker services are running: `docker ps`
2. ✅ Verify database is accessible: `docker-compose exec db psql -U postgres -d news_db`
3. ✅ Check API is responding: `curl http://localhost:8000/health`
4. ✅ Review recent logs: `docker logs news_backend --tail 50`
5. ✅ Run tests to ensure stability: `docker-compose exec backend pytest`

---

## 📋 Summary

**Pulse** is a fully-functional AI-powered news aggregator with:
- ✅ 8 automated background jobs for content pipeline
- ✅ OpenAI GPT-4o-mini integration for article analysis
- ✅ V2 statistics verification with 3-stage pipeline (source tracing, credibility rating, fact-checking)
- ✅ Framework mapping to connect articles to ethical debates
- ✅ Email newsletters via Resend API
- ✅ Next.js 15 frontend with authentication
- ✅ Comprehensive test suite (127 tests, 100% passing)

**Key Files to Know:**
- `backend/app/main.py` - FastAPI app entry point
- `backend/app/models.py` - Database schema (SQLModel)
- `backend/app/jobs/scheduler.py` - Background job configuration
- `backend/app/services/statistics_verifier.py` - V2 verification orchestrator
- `frontend/src/lib/api.ts` - API client for frontend

---

**Last Updated:** 2025-10-02
**Status:** 127/127 tests passing ✅
**AI Provider:** OpenAI GPT-4o-mini
**Frontend:** Next.js 15 (React 19, Turbopack, Tailwind 4)
