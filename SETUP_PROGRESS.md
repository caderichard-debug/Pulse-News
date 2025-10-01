# Pulse News Aggregator - Setup Progress

## ✅ Completed

### 1. Project Architecture Finalized
- **Tech Stack**: FastAPI + SQLModel + PostgreSQL + Next.js
- **Cost-optimized** for <$100/month budget
- **Email-first** approach with web app as secondary
- **AI-powered** framework generation using Claude Haiku

### 2. Dependencies Updated
- Updated `requirements.txt` with all necessary packages
- Core: FastAPI, SQLModel, Alembic
- Scraping: feedparser, trafilatura, readability-lxml
- AI: Anthropic Claude API
- Email: Resend
- Scheduling: APScheduler

### 3. Database Models Created (`backend/app/models.py`)
Complete SQLModel schema with:
- **Source**: News outlets (AP, Reuters, NYT, etc.)
- **Topic**: Categories (Politics, Tech, Science, etc.)
- **Article**: Scraped articles with metadata
- **ArticleAnalysis**: AI summaries, sentiment, bias
- **Framework**: AI-generated ethical debates
- **User**: User accounts and preferences
- **Newsletter**: Email tracking

### 4. Database Configuration
- Created `backend/app/database.py` with SQLModel engine
- Created `backend/app/config.py` for centralized settings
- Environment-based configuration with `.env` support

### 5. Alembic Migrations Setup
- Initialized Alembic in `backend/alembic/`
- Configured `alembic/env.py` to work with SQLModel
- Ready for auto-generating migrations

### 6. FastAPI Application Updated
- Updated `backend/app/main.py` with:
  - Lifespan events for DB table creation
  - Proper app metadata
  - Router integration

### 7. Docker Configuration
- Updated `dockerfile` with:
  - Python 3.11 base image
  - System dependencies for lxml
  - Proper build steps
- Created `.env.example` template

## 🔄 Next Steps

### Immediate (Week 1):
1. **Start Docker** and build containers:
   ```bash
   docker-compose up --build
   ```

2. **Create initial Alembic migration**:
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "Initial schema"
   docker-compose exec backend alembic upgrade head
   ```

3. **Build RSS Scraper Service** (`backend/app/services/rss_scraper.py`):
   - Use feedparser to fetch RSS feeds
   - Store article metadata in database
   - Handle 8 initial news sources

4. **Build Article Extractor** (`backend/app/services/article_extractor.py`):
   - Primary: trafilatura
   - Fallback: readability-lxml
   - Store full article text

5. **Set up APScheduler** (`backend/app/jobs/scheduler.py`):
   - Scrape RSS every 3 hours
   - Process articles every 4 hours
   - Update frameworks daily at 2am
   - Send newsletters daily at 7am

### Week 2: AI Integration
6. **Claude API Integration** (`backend/app/utils/claude_client.py`):
   - Batch processing wrapper
   - Cost tracking
   - Error handling

7. **AI Analyzer Service** (`backend/app/services/ai_analyzer.py`):
   - Batch process 5 articles at a time
   - Generate summaries (100 words)
   - Sentiment & bias analysis
   - Extract statistics

8. **Framework Generator** (`backend/app/services/framework_generator.py`):
   - Seed 10 initial frameworks
   - Weekly AI-powered framework discovery
   - Map articles to frameworks

### Week 3: Email System
9. **Newsletter Builder** (`backend/app/services/newsletter_builder.py`):
   - Select top articles per user preferences
   - Generate "The Bigger Picture" section
   - Create HTML email from template

10. **Jinja2 Email Template** (`backend/app/templates/newsletter.html`):
    - Responsive HTML design
    - Article summaries with bias indicators
    - Framework connections

11. **Resend Integration** (`backend/app/services/email_sender.py`):
    - Send emails via Resend API
    - Track opens and clicks
    - Handle failures

### Week 4: User Interface
12. **Auth Routes** (`backend/app/routes/auth.py`):
    - Signup endpoint
    - Email verification
    - Login/JWT tokens

13. **Preferences API** (`backend/app/routes/preferences.py`):
    - Topic selection
    - Newsletter frequency
    - Update preferences

14. **Next.js Pages**:
    - Signup form
    - Topic selection UI
    - Newsletter preview
    - Preferences management

## 📁 Project Structure

```
Pulse/
├── backend/
│   ├── alembic/              ✅ Configured
│   │   ├── versions/
│   │   └── env.py           ✅ SQLModel integration
│   ├── app/
│   │   ├── main.py          ✅ Updated with lifespan
│   │   ├── config.py        ✅ Settings management
│   │   ├── database.py      ✅ SQLModel session
│   │   ├── models.py        ✅ All database models
│   │   ├── routes/
│   │   │   ├── articles.py  ⏳ TODO
│   │   │   ├── auth.py      ⏳ TODO
│   │   │   └── preferences.py ⏳ TODO
│   │   ├── services/
│   │   │   ├── rss_scraper.py ⏳ TODO
│   │   │   ├── article_extractor.py ⏳ TODO
│   │   │   ├── ai_analyzer.py ⏳ TODO
│   │   │   ├── framework_generator.py ⏳ TODO
│   │   │   ├── newsletter_builder.py ⏳ TODO
│   │   │   └── email_sender.py ⏳ TODO
│   │   ├── jobs/
│   │   │   ├── scheduler.py ⏳ TODO
│   │   │   └── tasks.py ⏳ TODO
│   │   ├── templates/
│   │   │   └── newsletter.html ⏳ TODO
│   │   └── utils/
│   │       └── claude_client.py ⏳ TODO
│   └── alembic.ini          ✅ Configured
├── frontend/                ✅ Next.js scaffolded
├── docker-compose.yml       ✅ Configured
├── dockerfile               ✅ Updated
├── requirements.txt         ✅ All dependencies
└── .env.example            ✅ Template created

## 🚀 How to Continue

### 1. Get API Keys
- **Anthropic Claude**: https://console.anthropic.com/
- **Resend Email**: https://resend.com/

### 2. Create `.env` file
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Development
```bash
# Start Docker services
docker-compose up --build

# In another terminal, run migrations
docker-compose exec backend alembic upgrade head

# Test the API
curl http://localhost:8000/health
```

### 4. Build Services in Order
Follow the implementation phases in the main plan:
1. RSS scraping
2. Article extraction
3. AI analysis
4. Framework generation
5. Email newsletter
6. User interface

## 📊 Estimated Timeline
- Week 1: Core pipeline (scraping + extraction)
- Week 2: AI integration (analysis + frameworks)
- Week 3: Email system (templates + sending)
- Week 4: User interface (signup + preferences)
- Week 5: Polish and beta launch

## 💰 Projected Costs
- **Month 1** (50 users): $5-15
  - Hosting: $0 (free tier)
  - AI: $2-5
  - Email: $0 (free tier)
- **Month 6** (500 users): $30-50
  - Hosting: $12-24
  - AI: $10-20
  - Email: $5-10

## 🔑 Key Design Decisions
1. **SQLModel over raw SQLAlchemy** - Better FastAPI integration
2. **Alembic from day 1** - Prevent schema drift
3. **trafilatura over newspaper3k** - Better maintained, higher success rate
4. **4 separate APScheduler jobs** - Better isolation and flexibility
5. **Claude Haiku** - Most cost-effective for our use case
6. **Email-first** - Focus on core value prop before complex UI
